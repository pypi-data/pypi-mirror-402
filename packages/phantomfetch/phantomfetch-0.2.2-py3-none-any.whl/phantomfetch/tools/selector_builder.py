import argparse
import asyncio

from playwright.async_api import async_playwright


async def generate_selectors(page, target_text):
    print(f"Searching for text: '{target_text}'...")

    # Matches returned from evaluate are just JS handles if we returned nodes?
    # No, evaluate returns Serializable. Nodes are not serializable.
    # We need to return their paths or attributes, OR generate selectors IN JS.

    # Let's do generation in JS for better DOM access

    selectors = await page.evaluate(
        """(text) => {
        function getPathTo(element) {
            if (element.id !== '') return '#' + element.id;  // High confidence ID

            if (element === document.body) return element.tagName;

            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element)
                    return getPathTo(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }

        function getRobustSelector(el) {
            const strategies = [];

            // 1. ID
            if (el.id) strategies.push('#' + el.id);

            // 2. Specialized Attributes (often used for testing/scraping)
            const testAttrs = ['data-test', 'data-testid', 'data-qa', 'itemprop'];
            for (const attr of testAttrs) {
                if (el.hasAttribute(attr)) {
                    strategies.push(`[${attr}="${el.getAttribute(attr)}"]`);
                }
            }

            // 3. Classes (filtered)
            if (el.className && typeof el.className === 'string') {
                const validClasses = el.className.split(' ')
                    .filter(c => c.trim().length > 0)
                    .filter(c => !c.match(/active|hover|focus|selected/)); // Filter state classes

                if (validClasses.length > 0) {
                    // Try single classes
                    // strategies.push('.' + validClasses[0]);
                    // Try combined? Maybe too specific.
                    strategies.push('.' + validClasses.join('.'));
                }
            }

            // 4. Text Content (Playwright specific)
            const text = el.innerText.trim();
            if (text.length > 0 && text.length < 50) {
                strategies.push(`text="${text}"`);
            }

            // 5. Tag + Hierarchy (last resort)
            // strategies.push(getPathTo(el));

            return strategies;
        }

        const matches = [];
        const iter = document.createNodeIterator(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = iter.nextNode()) {
             if (node.textContent.toLowerCase().includes(text.toLowerCase().trim())) {
                let el = node.parentElement;

                // Visibility check (essential!)
                if (el.offsetParent === null) continue;

                // Collect info
                matches.push({
                    tag: el.tagName.toLowerCase(),
                    text: el.innerText.substring(0, 50),
                    selectors: getRobustSelector(el),
                    html: el.outerHTML.substring(0, 100)
                });
            }
        }
        return matches;
    }""",
        target_text,
    )

    return selectors


async def interactive_builder(url, target_text):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True
        )  # Use headless for speed, or false for debug?
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Loading {url}...")
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_load_state(
                "networkidle", timeout=30000
            )  # Wait for dynamic content
        except Exception as e:
            print(f"Error loading page: {e}")

        matches = await generate_selectors(page, target_text)

        print(f"Found {len(matches)} visible elements containing '{target_text}':")
        for i, m in enumerate(matches):
            print(f"\n--- Match {i + 1} <{m['tag']}> ---")
            print(f"Preview: {m['text']}...")
            print("Suggested Selectors:")
            for s in m["selectors"]:
                # Validate uniqueness
                count = await page.locator(s).count()
                status = "UNIQUE" if count == 1 else f"Matches {count}"
                print(f"  [{status}] {s}")

        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhantomFetch Selector Builder")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("text", help="Text to search for")
    args = parser.parse_args()

    asyncio.run(interactive_builder(args.url, args.text))
