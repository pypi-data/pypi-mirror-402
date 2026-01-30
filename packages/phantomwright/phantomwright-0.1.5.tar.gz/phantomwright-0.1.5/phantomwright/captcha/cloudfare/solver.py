import asyncio
import json
import time
from typing import Callable, Optional

from phantomwright.async_api import Page, BrowserContext

from .utils.consts import ChallengeType
from .utils.detection import (
    detect_cf_challenge_type,
    detect_cloudflare_challenge,
)
from .utils.dom_helpers import get_ready_checkbox
from .utils.shadow_root import (
    search_shadow_root_elements,
    search_shadow_root_iframes,
)
from .utils.build_js import observer_js, shadow_root_js


class CloudflareSolverAsync:
    """
    Automatic Cloudflare challenge solver for Playwright async API.

    This class automatically detects and solves Cloudflare Turnstile and Interstitial
    challenges by monitoring page loads and clicking the verification checkbox.

    Attributes:
        context: Playwright BrowserContext to monitor for Cloudflare challenges.
        max_attempts: Maximum number of solve attempts per challenge (default: 3).
        attempt_delay: Delay in seconds between retry attempts (default: 5).
        log: Optional callback function for logging solve events.

    Example:
        >>> from phantomwright.async_api import async_playwright
        >>> from .solver import CloudflareSolverAsync
        >>>
        >>> async with async_playwright() as p:
        ...     browser = await p.chromium.launch(headless=False)
        ...     context = await browser.new_context()
        ...     solver = CloudflareSolverAsync(context, log_callback=print)
        ...     solver.solve()  # Start monitoring for Cloudflare challenges
        ...     page = await context.new_page()
        ...     await page.goto("https://example.com")  # Challenges will be auto-solved
    """

    def __init__(
        self,
        context: BrowserContext,
        *,
        max_attempts: int = 3,
        attempt_delay: int = 5,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the Cloudflare solver.

        Args:
            context: Playwright BrowserContext to monitor for challenges.
            max_attempts: Maximum number of solve attempts per challenge.
            attempt_delay: Delay in seconds between retry attempts.
            log_callback: Optional callback function that receives a JSON string
                containing solve event details. The JSON includes:
                - event: "cloudflare_captcha_solve"
                - url: The page URL where the challenge was detected
                - challenge_type: "TURNSTILE" or "INTERSTITIAL"
                - success: Whether the solve was successful
                - attempts: Number of attempts made
                - duration_sec: Time taken to solve
                - error: Error message if failed, None otherwise
                - timestamp: Unix timestamp of the event
        """
        self.context = context
        self.max_attempts = max_attempts
        self.attempt_delay = attempt_delay
        self.log = log_callback

        self.solve_click_delay = 6
        self.wait_checkbox_attempts = 3
        self.wait_checkbox_delay = 6
        self.checkbox_click_attempts = 3

        self.page_solve_state = {}

    # ---------------- state ----------------
    def _get_page_state(self, page: Page):
        return self.page_solve_state.setdefault(
            page,
            {
                "status": "idle",  # idle | solving
                "last_url": None,
            },
        )

    # ---------------- js rebind ----------------
    async def _rebind(self, page: Page):
        try:
            await page.evaluate("""
                window.onCloudflareDetected = function(sel, url) {
                    window.__cf_callback(sel, url);
                };
            """)
            await asyncio.sleep(1)
            await page.evaluate("""
                if (typeof window.__triggerCfRescan === 'function') {
                    window.__triggerCfRescan();
                }
            """)
        except Exception:
            pass

    # ---------------- report helper ----------------
    def _log_final_report(self, report: dict):
        data = {
            "event": "cloudflare_captcha_solve",
            "url": report.get("url"),
            "challenge_type": report.get("challenge_type"),
            "success": report.get("success"),
            "attempts": report.get("attempts"),
            "duration_sec": round(report.get("duration", 0), 3),
            "error": report.get("error"),
            "timestamp": time.time(),
        }

        if self.log:
            log_str = json.dumps(data, ensure_ascii=False)
            self.log(log_str)

    # ---------------- core solve ----------------
    async def _auto_solve_cf(self, page: Page):
        state = self._get_page_state(page)

        report = {
            "url": page.url,
            "challenge_type": None,
            "success": False,
            "attempts": 0,
            "error": None,
            "start_time": time.time(),
            "duration": 0,
        }

        try:
            for attempt in range(1, self.max_attempts + 1):
                report["attempts"] = attempt
                try:
                    challenge_type = await detect_cf_challenge_type(page)
                    if challenge_type is None:
                        raise Exception("Unknown challenge type")

                    report["challenge_type"] = challenge_type.name

                    if challenge_type is ChallengeType.TURNSTILE:
                        await page.locator("#cf-turnstile").wait_for(timeout=10000)

                    cf_iframes = await search_shadow_root_iframes(
                        captcha_container=page,
                        src_filter="https://challenges.cloudflare.com/cdn-cgi/challenge-platform/",
                    )
                    if not cf_iframes:
                        raise Exception("Cloudflare iframe not found")

                    checkbox_data = await get_ready_checkbox(
                        iframes=cf_iframes,
                        delay=self.wait_checkbox_delay,
                        attempts=self.wait_checkbox_attempts,
                    )
                    if not checkbox_data:
                        raise Exception("Checkbox not ready")

                    iframe, checkbox = checkbox_data

                    click_errors = []
                    for i in range(self.checkbox_click_attempts):
                        try:
                            await checkbox.click()
                            break
                        except Exception as e:
                            click_errors.append(e)
                    else:
                        raise Exception(f"Failed to click checkbox. Errors: {click_errors}")

                    await asyncio.sleep(self.solve_click_delay)
                    if challenge_type is ChallengeType.TURNSTILE:
                        success_elements = await search_shadow_root_elements(
                            iframe, 'div[id="success"]'
                        )
                        
                        # Check if success element is actually visible
                        solved = False
                        for el in success_elements:
                            try:
                                is_visible = await el.is_visible()
                                if is_visible:
                                    solved = True
                                    break
                            except:
                                pass
                    else:
                        solved = not await detect_cloudflare_challenge(page)

                    if solved:
                        state["status"] = "idle"

                        report["success"] = True
                        return
                    else:
                        raise Exception("Solve attempt did not pass verification")

                except Exception as e:
                    report["error"] = str(e)
                    await asyncio.sleep(self.attempt_delay)

            state["status"] = "idle"
            raise Exception(f"Failed after {self.max_attempts} attempts")

        except Exception as final_error:
            report["error"] = str(final_error)
            raise

        finally:
            report["duration"] = time.time() - report["start_time"]
            if report["success"]:
                report["url"] = None  # Clear URL on success for privacy
            self._log_final_report(report)

    # ---------------- callback ----------------
    def _make_on_cf_detected(self, page: Page):
        async def on_cf_detected(selector, url):
            if not selector:
                return

            state = self._get_page_state(page)
            current_url = page.url
            
            # Skip if this URL was already attempted
            if state["last_url"] == current_url:
                return

            if state["status"] == "solving":
                return

            state["status"] = "solving"
            state["last_url"] = current_url

            asyncio.create_task(self._auto_solve_cf(page))

        return on_cf_detected

    # ---------------- page setup ----------------
    async def _setup_page(self, page: Page):
        await page.add_init_script("""
            window.onCloudflareDetected = function(sel, url) {};
        """)
        await page.add_init_script(observer_js)
        await page.add_init_script(shadow_root_js)

        await page.expose_function("__cf_callback", self._make_on_cf_detected(page))
        
        # Listen to multiple events for more reliable detection
        page.on("load", lambda: asyncio.create_task(self._rebind(page)))
        page.on("domcontentloaded", lambda: asyncio.create_task(self._rebind(page)))
        page.on("framenavigated", lambda frame: asyncio.create_task(self._rebind(page)) if frame == page.main_frame else None)
        
        # Immediately rebind in case page is already loaded
        asyncio.create_task(self._rebind(page))

    # ---------------- public api ----------------
    def start(self) -> None:
        """
        Start monitoring the browser context for Cloudflare challenges.

        This method registers event listeners on the context to automatically
        detect and solve Cloudflare challenges on any new page. Call this once
        after creating the solver instance.

        Note:
            This method is synchronous but sets up async handlers internally.
            Challenges will be solved automatically in the background.
        """
        self.context.on(
            "page",
            lambda p: asyncio.create_task(self._setup_page(p)),
        )
