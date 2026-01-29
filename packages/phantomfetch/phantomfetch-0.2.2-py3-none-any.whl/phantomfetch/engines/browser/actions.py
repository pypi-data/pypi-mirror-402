import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from ...types import ActionResult

from ...telemetry import get_tracer
from ...types import Action

logger = logging.getLogger(__name__)
tracer = get_tracer()


async def _human_type(page: "Page", text: str):
    """Type text with human-like delays."""
    for char in text:
        await page.keyboard.type(char)
        # Random delay: Gaussian distribution
        # Mean 100ms, sigma 50ms, min 20ms, max 300ms
        delay = max(0.02, min(0.3, random.gauss(0.1, 0.05)))
        await asyncio.sleep(delay)


async def _human_mouse_move(page: "Page", element_handle: Any):
    """
    Move the mouse to the center of the element using a cubic Bezier curve
    to simulate human movement.
    """
    box = await element_handle.bounding_box()
    if not box:
        return

    # Target: random point within the element
    target_x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
    target_y = box["y"] + box["height"] * random.uniform(0.2, 0.8)

    # Start: current mouse position (default 0,0 if not tracked?)
    # Playwright keeps track of mouse position.
    # We can just use page.mouse.move with steps? No, native move is linear.
    # We need to manually calculate steps.

    # start_pos = {"x": 0, "y": 0}
    # Ideally should get current mouse pos but playwright doesn't expose it easily.
    # We'll just assume start from random edge or 0,0?
    # Simple approach: Move in steps

    await page.mouse.move(target_x, target_y, steps=random.randint(5, 25))

    # Real "human" logic (Bezier) is complex to implement fully without
    # external libraries like numpy/scipy or complex math.
    # For now, Playwright's `steps` parameter adds intermediate events which is "smoother"
    # than instant teleport.
    # We can add a slight overshoot/correction if we want to be fancy, but `steps` is 1st iterated humanization.


async def execute_actions(
    page: "Page | Locator", actions: list[Action]
) -> list["ActionResult"]:
    """
    Execute a list of actions on a Playwright page or locator.

    Args:
        page: Playwright page or locator instance
        actions: List of Action objects

    Returns:
        List of ActionResult objects
    """
    from playwright.async_api import Page

    from ...types import ActionResult

    results = []

    for action in actions:
        with tracer.start_as_current_span(
            f"phantomfetch.action.{action.action}"
        ) as span:
            span.set_attribute("phantomfetch.action.type", action.action)
            if action.selector:
                span.set_attribute("phantomfetch.action.selector", action.selector)

            logger.debug(
                f"[browser] Executing: {action.action} {action.selector or ''}"
            )

            # Handle conditional action logic
            if action.if_selector:
                condition_met = False

                # Resolve context for if_selector checks
                # If page is Locator, we check inside it?
                # Playwright Locator doesn't have wait_for_selector directly with same API sometimes?
                # Actually locator.locator(selector).count() works.

                # If timeout is specified, wait for selector
                if action.if_selector_timeout > 0:
                    try:
                        logger.debug(
                            f"[browser] Waiting up to {action.if_selector_timeout}ms for condition: {action.if_selector}"
                        )
                        # wait_for_selector is available on Page, frame, and ElementHandle.
                        # Locator has specific methods.
                        # We can use page.locator(selector).wait_for(...)
                        # But wait_for_selector is convenient.
                        # If page is Locator, creating a sub-locator:
                        target = page.locator(action.if_selector)
                        await target.wait_for(
                            timeout=action.if_selector_timeout,
                            state="attached",
                        )
                        condition_met = True
                    except Exception:
                        condition_met = False
                else:
                    # Immediate check
                    condition_count = await page.locator(action.if_selector).count()
                    condition_met = condition_count > 0

                if not condition_met:
                    logger.debug(
                        f"[browser] Skipping action {action.action} because if_selector '{action.if_selector}' not found"
                    )
                    # Create a skipped result
                    result = ActionResult(
                        action=action,
                        success=True,
                        data="Skipped (condition not met)",
                    )
                    span.set_attribute("phantomfetch.action.skipped", True)
                    results.append(result)
                    continue

            # Resolve execution context
            # Default to current page/locator context
            ctx = page

            # If scope is explicitly 'page', force usage of root page
            if action.scope == "page":
                ctx = page if isinstance(page, Page) else page.page

            start_time = time.perf_counter()
            result = ActionResult(action=action, success=True)

            try:
                match action.action:
                    case "wait":
                        if action.selector:
                            state = action.state or "visible"
                            if isinstance(ctx, Page):
                                await ctx.wait_for_selector(
                                    action.selector,
                                    timeout=action.timeout,
                                    state=state,
                                )
                            else:
                                # Start from locator context
                                await ctx.locator(action.selector).first.wait_for(
                                    timeout=action.timeout, state=state
                                )
                        elif action.timeout:
                            target_page = ctx if isinstance(ctx, Page) else ctx.page
                            await target_page.wait_for_timeout(action.timeout)

                    case "loop":
                        if not action.selector or not action.actions:
                            result.success = False
                            result.error = "Loop requires selector and child actions"
                        else:
                            # 1. Find all elements on the resolved context
                            elements = await ctx.locator(action.selector).all()
                            loop_results = []

                            limit = action.max_iterations or 100
                            logger.debug(
                                f"[browser] Looping over {len(elements)} elements (limit={limit})"
                            )

                            for i, el in enumerate(elements):
                                if i >= limit:
                                    break
                                # 2. Execute child actions on EACH element locator
                                sub_res = await execute_actions(el, action.actions)
                                loop_results.append({"index": i, "results": sub_res})

                            result.data = loop_results

                    case "click":
                        if action.selector:
                            if action.human_like:
                                # Human-like click
                                # Resolve handle first
                                if isinstance(ctx, Page):
                                    handle = await ctx.wait_for_selector(
                                        action.selector,
                                        timeout=action.timeout,
                                        state="visible",
                                    )
                                else:
                                    # Locator context
                                    target = ctx.locator(action.selector).first
                                    await target.wait_for(
                                        timeout=action.timeout, state="visible"
                                    )
                                    handle = await target.element_handle()

                                if handle:
                                    # Need page for mouse move
                                    target_page = (
                                        ctx if isinstance(ctx, Page) else ctx.page
                                    )
                                    await _human_mouse_move(target_page, handle)
                                    await handle.click(delay=random.randint(50, 150))
                            else:
                                await ctx.click(
                                    action.selector,
                                    timeout=action.timeout,
                                )
                        # Context click (no selector)
                        elif isinstance(ctx, Page):
                            result.success = False
                            result.error = "Click action on Page requires a selector"
                        elif action.human_like:
                            # Human-like click on self (ctx is locator)
                            handle = await ctx.element_handle()
                            if handle:
                                target_page = ctx.page
                                await _human_mouse_move(target_page, handle)
                                await handle.click(delay=random.randint(50, 150))
                        else:
                            await ctx.click(timeout=action.timeout)

                    case "input":
                        if action.selector:
                            # Input into descendant
                            val_str = str(action.value)
                            if action.human_like:
                                await ctx.click(action.selector, timeout=action.timeout)
                                target_page = ctx if isinstance(ctx, Page) else ctx.page
                                await _human_type(target_page, val_str)
                            else:
                                await ctx.fill(
                                    action.selector,
                                    val_str,
                                    timeout=action.timeout,
                                )
                        # Input into self (ctx is locator)
                        elif isinstance(ctx, Page):
                            result.success = False
                            result.error = "Input action on Page requires a selector"
                        else:
                            val_str = str(action.value)
                            if action.human_like:
                                await ctx.click(timeout=action.timeout)
                                target_page = ctx.page
                                await _human_type(target_page, val_str)
                            else:
                                await ctx.fill(val_str, timeout=action.timeout)

                    case "scroll":
                        # Scroll usually implies page-level or element-level scroll
                        # For now, keep page level logic mostly
                        target_page = ctx if isinstance(ctx, Page) else ctx.page

                        if action.selector == "top":
                            await target_page.evaluate("window.scrollTo(0, 0)")
                        elif action.x is not None or action.y is not None:
                            x = action.x or 0
                            y = action.y or 0
                            await target_page.evaluate(f"window.scrollTo({x}, {y})")
                        elif action.selector:
                            # Scroll specific element into view
                            await ctx.locator(
                                action.selector
                            ).scroll_into_view_if_needed(timeout=action.timeout)
                        else:
                            await target_page.evaluate(
                                "window.scrollTo(0, document.body.scrollHeight)"
                            )

                    case "extract":
                        # Validate schema
                        if not action.schema:
                            result.error = "Extraction requires a schema"
                            result.success = False
                        else:
                            # Compatibility JS for Locator execution
                            # RE-WRITING JS FOR LOCATOR COMPATIBILITY

                            js_extract_compat = """
                            (nodeOrArgs, argsIfNode) => {
                                // Logic to detect if called on element or page
                                let ctx = document;
                                let args = nodeOrArgs;

                                if (nodeOrArgs instanceof Node) {
                                    ctx = nodeOrArgs;
                                    args = argsIfNode;
                                }

                                const { rootSelector, schema } = args;

                                const getEl = (c, s) => s ? c.querySelector(s) : c;

                                const isVisible = (el) => {
                                    if (!el) return false;
                                    return el.offsetParent !== null && window.getComputedStyle(el).display !== 'none' && window.getComputedStyle(el).visibility !== 'hidden';
                                };

                                const extractSingle = (c, spec) => {
                                    let selector = spec;
                                    let op = "text";
                                    let param = null;
                                    let visibleOnly = false;

                                    if (typeof spec === "object" && spec !== null && spec._selector) {
                                        selector = spec._selector;
                                        visibleOnly = !!spec._visible_only;
                                    } else if (typeof spec === "string") {
                                        if (spec.includes(" :: ")) {
                                            const parts = spec.split(" :: ");
                                            selector = parts[0];
                                            const opPart = parts[1];
                                            if (opPart.startsWith("attr(")) {
                                                op = "attr";
                                                param = opPart.slice(5, -1);
                                            } else if (opPart === "text") {
                                                op = "text";
                                            } else if (opPart === "html") {
                                                op = "html";
                                            }
                                        } else if (spec.trim().startsWith("::")) {
                                            // Handle case where selector is implicit (self) e.g. ":: text"
                                            selector = null;
                                            const opPart = spec.trim().substring(2).trim();
                                            if (opPart.startsWith("attr(")) {
                                                op = "attr";
                                                param = opPart.slice(5, -1);
                                            } else if (opPart === "text" || opPart === "text") {
                                                op = "text";
                                            } else if (opPart === "html") {
                                                op = "html";
                                            }
                                        }
                                    }

                                    let el = null;
                                    // Treat empty string as "self"
                                    if (!selector || selector.trim() === "") selector = null;

                                    if (visibleOnly) {
                                        // Find first visible match
                                        const candidates = selector ? c.querySelectorAll(selector) : [c];
                                        el = Array.from(candidates).find(x => isVisible(x));
                                    } else {
                                        el = selector ? c.querySelector(selector) : c;
                                    }

                                    if (!el) return null;
                                    if (op === "text") return el.innerText.trim();
                                    if (op === "html") return el.outerHTML;
                                    if (op === "attr" && param) return el.getAttribute(param);
                                    return null;
                                };

                                const processSchema = (c, s) => {
                                    const out = {};
                                    for (const [key, val] of Object.entries(s)) {
                                        if (typeof val === "string") {
                                            out[key] = extractSingle(c, val);
                                        } else if (typeof val === "object" && val !== null) {
                                            // Check if it's a leaf definition object (starts with _)
                                            if (val._selector) {
                                                out[key] = extractSingle(c, val);
                                            } else {
                                                // Nested schema
                                                // If it has _root, scope ctx? Not processing lists here yet.
                                                // Assuming recursive dict structure
                                                out[key] = processSchema(c, val);
                                            }
                                        }
                                    }
                                    return out;
                                };

                                // If rootSelector is set, refine context
                                let root = ctx;
                                if (rootSelector) {
                                    if (rootSelector === "body" || rootSelector === "document") {
                                        root = document.body;
                                    } else {
                                        // If ctx is an element, this searches descendants
                                        root = ctx.querySelector(rootSelector);
                                    }
                                }
                                if (!root) return null;

                                return processSchema(root, schema);
                            }
                            """

                            extracted_data = await ctx.evaluate(
                                js_extract_compat,
                                {
                                    "rootSelector": action.selector,
                                    "schema": action.schema,
                                },
                            )
                            result.data = extracted_data

                    case "select":
                        # Locator also has select_option
                        await ctx.select_option(
                            selector=action.selector,  # For locator, if selector provided, it finds sub-element?
                            # Locator.select_option(value, ...) -> calls on self?
                            # Page.select_option(selector, value)
                            # If page is Locator, and selector is provided, do we perform relative select?
                            # locator.locator(selector).select_option(...) logic
                            value=str(action.value),
                            timeout=action.timeout,
                        ) if isinstance(ctx, Page) else await ctx.locator(
                            action.selector
                        ).select_option(str(action.value), timeout=action.timeout)

                    case "hover":
                        if action.selector:
                            if isinstance(ctx, Page):
                                await ctx.hover(action.selector, timeout=action.timeout)
                            else:
                                await ctx.locator(action.selector).hover(
                                    timeout=action.timeout
                                )

                    case "screenshot":
                        path = str(action.value) if action.value else None

                        # Handle full_page on Locator (not supported, must use Page)
                        screenshot_ctx = ctx
                        kwargs = {}
                        if action.full_page:
                            kwargs["full_page"] = True
                            if not isinstance(ctx, Page):
                                # If we are in a Locator (e.g. inside loop loop), but want full page,
                                # we must switch to the page context.
                                screenshot_ctx = ctx.page

                        if action.options:
                            # Map allowed options to playwright screenshot kwargs
                            allowed = [
                                "type",
                                "quality",
                                "omit_background",
                                "clip",
                                "mask",
                                "animations",
                                "caret",
                                "scale",
                            ]
                            for k, v in action.options.items():
                                if k in allowed:
                                    kwargs[k] = v

                        img_bytes = await screenshot_ctx.screenshot(path=path, **kwargs)
                        if not path:
                            result.data = img_bytes

                    case "wait_for_load":
                        target_page = ctx if isinstance(ctx, Page) else ctx.page
                        await target_page.wait_for_load_state(
                            "networkidle", timeout=action.timeout
                        )

                    case "evaluate":
                        if action.value:
                            eval_result = await ctx.evaluate(str(action.value))
                            result.data = eval_result

                    case "validate":
                        try:
                            state = action.state or "attached"
                            if isinstance(ctx, Page):
                                await ctx.wait_for_selector(
                                    action.selector,
                                    timeout=action.timeout or 5000,
                                    state=state,
                                )
                            else:
                                await ctx.locator(action.selector).first.wait_for(
                                    timeout=action.timeout or 5000, state=state
                                )
                            result.success = True
                        except Exception:
                            result.success = False
                            result.error = (
                                f"Validation failed: {action.selector} not {state}"
                            )

                    case "solve_captcha":
                        # Requires Page context for solver
                        target_page = ctx if isinstance(ctx, Page) else ctx.page

                        if action.provider in ("cdp", "scraping_browser"):
                            from ...captcha import CDPSolver

                            solver = CDPSolver()
                        else:
                            from ...captcha import TwoCaptchaSolver

                            solver = TwoCaptchaSolver()

                        token = await solver.solve(target_page, action)
                        # Token might be None if no captcha detected or failed
                        if token:
                            result.data = token
                        elif action.fail_on_error:
                            # If we strictly required a solution
                            result.success = False
                            result.error = "Failed to solve CAPTCHA or none detected"
                        else:
                            # Treated as success/skipped if no captcha found and not strict
                            result.data = "No CAPTCHA resolved"

                    case "if":
                        # Check condition (selector presence)
                        condition_met = False
                        if action.selector:
                            # Check visibility/existence
                            try:
                                if isinstance(ctx, Page):
                                    # Use strict=False, state=visible/attached?
                                    # Just check count > 0 or wait with short timeout?
                                    # Let's use is_visible or check count to avoid waiting if timeout=0
                                    if action.timeout > 0:
                                        try:
                                            await ctx.wait_for_selector(
                                                action.selector,
                                                timeout=action.timeout,
                                                state=action.state or "visible",
                                            )
                                            condition_met = True
                                        except Exception:
                                            condition_met = False
                                    else:
                                        # Instant check
                                        condition_met = await ctx.locator(
                                            action.selector
                                        ).first.is_visible()
                                # Locator context
                                elif action.timeout > 0:
                                    try:
                                        await ctx.locator(
                                            action.selector
                                        ).first.wait_for(
                                            timeout=action.timeout,
                                            state=action.state or "visible",
                                        )
                                        condition_met = True
                                    except Exception:
                                        condition_met = False
                                else:
                                    condition_met = await ctx.locator(
                                        action.selector
                                    ).first.is_visible()
                            except Exception as e:
                                logger.debug(f"IF condition check failed: {e}")
                                condition_met = False

                        if condition_met:
                            if action.then_actions:
                                result.data = await execute_actions(
                                    ctx, action.then_actions
                                )
                        elif action.else_actions:
                            result.data = await execute_actions(
                                ctx, action.else_actions
                            )

                    case "try":
                        # Try/Catch block
                        # The 'try' block is 'action.actions'
                        # The 'catch' block is 'action.else_actions'
                        if not action.actions:
                            result.success = False
                            result.error = "TRY requires actions list"
                        else:
                            try:
                                # We need to ensure fail_on_error behaves locally?
                                # If sub-actions fail, do we catch it?
                                # Yes, execute_actions catches internal errors but returns error results.
                                # But if they raise Exceptions (due to fail_on_error=True in child), we catch that.

                                # We should probably NOT force fail_on_error=True for children unless specified?
                                # But if children have it set, they raise.

                                sub_results = await execute_actions(ctx, action.actions)

                                # Check if any failed in strict mode logic?
                                # If execute_actions returns, it means no undetected exception raised.
                                # But did they succeed?
                                any_failed = any(not r.success for r in sub_results)
                                if any_failed:
                                    # Treat as failure?
                                    # 'try' usually catches Exceptions.
                                    # If we want to catch Logic Failures, we should check results.
                                    # Let's assume 'try' is for Exceptions/Handling quirks.
                                    # If execute_actions returned, technically the flow worked.
                                    result.data = sub_results

                            except Exception as e:
                                logger.warning(
                                    f"[browser] TRY block failed, executing CATCH: {e}"
                                )
                                if action.else_actions:
                                    result.data = await execute_actions(
                                        ctx, action.else_actions
                                    )
                                else:
                                    # Swallowed exception if no catch block
                                    pass

                    case _:
                        logger.warning(f"[browser] Unknown action: {action.action}")
                        result.success = False
                        result.error = f"Unknown action: {action.action}"
                        span.set_attribute("error", True)

            except Exception as e:
                # ... existing error handling ...
                result.success = False
                result.error = str(e)
                logger.error(f"[browser] Action failed: {action.action} - {e}")
                span.record_exception(e)

                if action.fail_on_error:
                    results.append(result)
                    raise RuntimeError(
                        f"Critical Action Failed ({action.action}): {e}"
                    ) from e

            finally:
                result.duration = time.perf_counter() - start_time
                # ... existing trace updates ...
                results.append(result)

    return results


def actions_to_payload(actions: list[Action]) -> list[dict]:
    """
    Convert Action objects to JSON-serializable dicts for BaaS API.

    Args:
        actions: List of Action objects

    Returns:
        List of action dicts
    """
    import msgspec

    return [msgspec.to_builtins(a) for a in actions]
