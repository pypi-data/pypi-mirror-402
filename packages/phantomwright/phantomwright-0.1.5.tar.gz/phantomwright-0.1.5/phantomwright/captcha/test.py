import asyncio
import logging

from phantomwright.async_api import async_playwright
from phantomwright.captcha import CloudflareSolverAsync

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        solver = CloudflareSolverAsync(
            context,
            max_attempts=3,
            attempt_delay=5,
            log_callback=logging.getLogger("CloudflareSolver").info,
        )

        solver.start()
        urls = [
            "https://2captcha.com/demo/cloudflare-turnstile-challenge",
            "https://2captcha.com/demo/cloudflare-turnstile",
            # "https://www.pexels.com",
        ]
        for url in urls:
            page = await context.new_page()
            await page.goto(url)

        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
