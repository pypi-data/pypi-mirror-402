import asyncio
import logging
from typing import TYPE_CHECKING, Protocol

import httpx

if TYPE_CHECKING:
    from playwright.async_api import Page

    from .types import Action

logger = logging.getLogger(__name__)


class CaptchaSolver(Protocol):
    async def solve(self, page: "Page", action: "Action") -> str | None:
        """
        Solve a CAPTCHA on the page.

        Args:
            page: Playwright page instance
            action: Action configuration containing API key etc.

        Returns:
            Solution token if successful, None otherwise
        """
        ...

    async def detect(self, page: "Page") -> str | None:
        """
        Detect presence of a CAPTCHA.

        Returns:
            Type of CAPTCHA detected (e.g. "recaptcha", "hcaptcha") or None
        """
        ...


class TwoCaptchaSolver:
    """
    Solver using 2Captcha API.
    """

    API_URL = "http://2captcha.com/in.php"
    RES_URL = "http://2captcha.com/res.php"

    async def solve(self, page: "Page", action: "Action") -> str | None:
        if not action.api_key:
            logger.error("[captcha] No API key provided for 2Captcha")
            return None

        captcha_type = await self.detect(page)
        if not captcha_type:
            logger.info("[captcha] No supported CAPTCHA detected")
            return None

        sitekey = await self._get_sitekey(page, captcha_type)
        if not sitekey:
            logger.error(f"[captcha] Could not find sitekey for {captcha_type}")
            return None

        logger.info(
            f"[captcha] Solving {captcha_type} with 2Captcha (key={sitekey[:5]}...)"
        )

        try:
            async with httpx.AsyncClient() as client:
                # 1. Submit request
                params = {
                    "key": action.api_key,
                    "method": "userrecaptcha",  # Default to reCaptcha fallback
                    "googlekey": sitekey,
                    "pageurl": page.url,
                    "json": 1,
                }

                if captcha_type == "hcaptcha":
                    params["method"] = "hcaptcha"
                elif captcha_type == "turnstile":
                    params["method"] = "turnstile"

                resp = await client.post(self.API_URL, params=params)
                data = resp.json()

                if data.get("status") != 1:
                    logger.error(f"[captcha] Submission failed: {data}")
                    return None

                request_id = data["request"]

                # 2. Poll for result
                for _ in range(30):  # Wait up to 150s
                    await asyncio.sleep(5)
                    resp = await client.get(
                        self.RES_URL,
                        params={
                            "key": action.api_key,
                            "action": "get",
                            "id": request_id,
                            "json": 1,
                        },
                    )
                    data = resp.json()

                    if data.get("status") == 1:
                        token = data["request"]
                        logger.info("[captcha] Solved successfully")
                        await self._inject_token(page, token, captcha_type)

                        # Optional: wait for navigation/reload if the captcha solution triggers it
                        # The action.options might not exist, so handle it safely
                        wait_navigation = (
                            action.options.get("waitForNavigation", True)
                            if action.options
                            else True
                        )
                        if wait_navigation and token:
                            try:
                                # Wait for load event or network idle
                                # Default to 'load' as it's safest for redirects
                                await page.wait_for_load_state(
                                    "load", timeout=action.timeout or 30000
                                )
                                logger.info(
                                    "[captcha] Waited for navigation after solve."
                                )
                            except Exception as nav_err:
                                logger.warning(
                                    f"[captcha] Wait for navigation failed: {nav_err}"
                                )
                        return token

                    if data.get("request") != "CAPCHA_NOT_READY":
                        logger.error(f"[captcha] Error polling: {data}")
                        return None

                logger.error("[captcha] Timed out waiting for solution")
                return None
        except Exception as e:
            logger.error(f"[captcha] Error: {e}")
            return None

    async def detect(self, page: "Page") -> str | None:
        if await page.locator(".g-recaptcha").count() > 0:
            return "recaptcha"
        if await page.locator("[data-sitekey]").count() > 0:
            # Could be hcaptcha or recaptcha
            if await page.locator('iframe[src*="hcaptcha"]').count() > 0:
                return "hcaptcha"
            return "recaptcha"
        if await page.locator(".cf-turnstile").count() > 0:
            return "turnstile"
        return None

    async def _get_sitekey(self, page: "Page", captcha_type: str) -> str | None:
        try:
            if captcha_type == "recaptcha":
                el = page.locator(".g-recaptcha").first
                return await el.get_attribute("data-sitekey")
            elif captcha_type == "hcaptcha":
                # hCaptcha often puts sitekey on a div with class h-captcha or data-sitekey
                el = page.locator("[data-sitekey]").first
                return await el.get_attribute("data-sitekey")
            elif captcha_type == "turnstile":
                el = page.locator(".cf-turnstile").first
                return await el.get_attribute("data-sitekey")
        except Exception:
            pass
        return None

    async def _inject_token(self, page: "Page", token: str, captcha_type: str) -> None:
        """Inject token into the form."""
        if captcha_type == "recaptcha":
            await page.evaluate(
                f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
            )
            # Try to find callback
            # This is tricky without knowing specific page implementation
        elif captcha_type == "hcaptcha":
            await page.evaluate(
                f'document.querySelector("[name=h-captcha-response]").innerHTML="{token}";'
            )
            await page.evaluate(
                f'document.querySelector("[name=g-recaptcha-response]").innerHTML="{token}";'
            )
        elif captcha_type == "turnstile":
            await page.evaluate(
                f'document.querySelector("[name=cf-turnstile-response]").value="{token}";'
            )


class CDPSolver:
    """
    Solver using Browser CDP events (e.g. for Scraping Browser).
    """

    async def solve(self, page: "Page", action: "Action") -> str | None:
        try:
            # 1. Start CDP session
            # Note: page.context.new_cdp_session(page) creates a session for the target page
            client = await page.context.new_cdp_session(page)

            # 2. Setup state
            loop = asyncio.get_running_loop()
            finished_future = loop.create_future()
            detected_event = asyncio.Event()

            def on_detected(e):
                logger.info(f"[captcha-cdp] Captcha detected: {e}")
                detected_event.set()

            def on_solved(e):
                logger.info("[captcha-cdp] Captcha solved!")
                if not finished_future.done():
                    # Token might be in 'token' field if provided by event
                    # The user example schema says: type, success, message, token?
                    # But event handlers receive the event dict/payload.
                    # We assume 'e' is the dict.
                    token = e.get("token")
                    finished_future.set_result(token or "SOLVED_NO_TOKEN")

            def on_failed(e):
                logger.error(f"[captcha-cdp] Captcha failed: {e}")
                if not finished_future.done():
                    finished_future.set_result(None)  # Treat as failure

            client.on("Captcha.detected", on_detected)
            client.on("Captcha.solveFinished", on_solved)
            client.on("Captcha.solveFailed", on_failed)

            # 3. Configure
            if action.options:
                import json

                # Check for config to send
                # The user example uses 'Captcha.setConfig' with a 'config' dict/json string
                # We expect action.options to contain the config fields directly or wrapped?
                # Let's assume action.options IS the config dict.
                # format: client.send('Captcha.setConfig', {'config': json.dumps(options)})

                # Extract specific config keys if mixed with other options?
                # For now, pass all options as config

                # Filter options?
                config_payload = action.options.copy()
                # Remove non-captcha options if any (like 'detectTimeout' which we use locally)
                detect_timeout = config_payload.pop("detectTimeout", 5000)

                # Only set config if there are keys left
                passed_config = {
                    k: v
                    for k, v in config_payload.items()
                    if k
                    not in [
                        "autoSolve",
                        "enabledForRecaptcha",
                        "enabledForRecaptchaV3",
                        "enabledForTurnstile",
                        "apiKey",
                    ]
                    or True  # actually user might pass anything
                }

                # Actually, strictly following user example:
                # { "apiKey": ..., "autoSolve": ... }
                # We'll valid keys or just pass everything.

                if passed_config:
                    await client.send(
                        "Captcha.setConfig", {"config": json.dumps(passed_config)}
                    )

            # Detect phase
            # If "if detected wait for finished" is the logic:
            # We wait for 'detectTimeout' (default e.g. 5s).
            # If detected -> wait for 'timeout' (action.timeout) for resolution.
            # If not detected -> return None (assume clear)

            detect_timeout = (
                action.options.get("detectTimeout", 3000) if action.options else 3000
            )

            try:
                # We also check if we should trigger solve manually?
                # User said: "most of the time... automatically"
                # So we just wait.

                logger.debug(
                    f"[captcha-cdp] Monitoring for CAPTCHA (timeout={detect_timeout}ms)"
                )

                # Wait for detected event OR finished event (if we missed detected)
                # We can race (sleep(detect), finished_future)
                # But we also want to know if 'detected' happened to extend timeout.

                # Wait for detected or finished
                done, _ = await asyncio.wait(
                    [asyncio.create_task(detected_event.wait()), finished_future],
                    timeout=detect_timeout / 1000,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if finished_future in done:
                    # Solved!
                    token = finished_future.result()

                    # Optional: wait for navigation/reload if the captcha solution triggers it
                    wait_navigation = (
                        action.options.get("waitForNavigation", True)
                        if action.options
                        else True
                    )
                    if wait_navigation and token:
                        try:
                            # Give the page a moment to react to the token injection
                            # This prevents wait_for_load_state from returning immediately if the navigation hasn't started yet
                            # Increasing to 3.0s as 0.5s was insufficient for some redirects
                            await asyncio.sleep(3.0)

                            # Wait for load event or network idle
                            # Default to 'load' as it's safest for redirects
                            await page.wait_for_load_state(
                                "load", timeout=action.timeout or 30000
                            )
                            logger.info(
                                "[captcha-cdp] Waited for navigation after solve."
                            )
                        except Exception as nav_err:
                            logger.warning(
                                f"[captcha-cdp] Wait for navigation failed: {nav_err}"
                            )

                    return token

                if detected_event.is_set():
                    # Detected! Now wait for full timeout
                    logger.info("[captcha-cdp] Detected! Waiting for solution...")
                    remaining_timeout = max(0, action.timeout - detect_timeout) / 1000
                    return await asyncio.wait_for(
                        finished_future, timeout=remaining_timeout
                    )

                # If we got here, we timed out on detection
                logger.debug("[captcha-cdp] No CAPTCHA detected within timeout.")
                return None

            except TimeoutError:
                if detected_event.is_set():
                    logger.error("[captcha-cdp] Timed out waiting for solution.")
                return None

        except Exception as e:
            logger.error(f"[captcha-cdp] Error: {e}")
            return None
