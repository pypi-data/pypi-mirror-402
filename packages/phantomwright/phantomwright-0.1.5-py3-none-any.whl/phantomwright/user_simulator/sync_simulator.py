"""Synchronous user behavior simulation module.

This module provides high-level APIs to simulate realistic human-like
interactions with web pages using Playwright's sync API.
"""

import random
import time
import string
from .script import _VISUAL_CURSOR_JS
from .sync_basic import (
    wait_human,
    move_to_target,
    move_to_box,
    scroll_human,
    bring_into_view,
    idle_human,
)

class SyncUserSimulator:
    """
    High-level synchronous user behavior simulation.

    This class provides methods to simulate realistic human-like interactions
    with web pages, including mouse movements, typing, scrolling, and browsing.

    Attributes:
        page: Playwright Page object.
        mouse: Playwright Mouse object for mouse operations.
        keyboard: Playwright Keyboard object for keyboard operations.
        mouse_x (float): Current mouse X coordinate.
        mouse_y (float): Current mouse Y coordinate.

    Example:
        >>> from playwright.sync_api import sync_playwright
        >>> from phantomwright.user_simulator import SyncUserSimulator
        >>>
        >>> with sync_playwright() as p:
        ...     browser = p.chromium.launch(headless=False)
        ...     page = browser.new_page(viewport={"width": 1280, "height": 900})
        ...     page.goto("https://example.com")
        ...     sim = SyncUserSimulator(page)
        ...     sim.simulate_browsing(duration_ms=2000)
        ...     browser.close()
    """

    def __init__(self, page, *, visualize_mouse: bool = False):
        """
        Initialize the SyncUserSimulator.

        Creates a new simulator instance and positions the mouse near the
        center of the viewport with a small random offset to simulate
        natural cursor placement.

        Args:
            page: Playwright Page object. Must have a viewport set.

        Raises:
            TypeError: If page.viewport_size is None (viewport not set).

        Example:
            >>> page = browser.new_page(viewport={"width": 1280, "height": 900})
            >>> page.goto("https://example.com")
            >>> sim = SyncUserSimulator(page)
        """
        self.page = page
        self.mouse = page.mouse
        self.keyboard = page.keyboard
        self.visualize_mouse = visualize_mouse

        if self.visualize_mouse:
            self.page.add_init_script(_VISUAL_CURSOR_JS)

        vp = self.page.viewport_size
        cx, cy = vp["width"] / 2, vp["height"] / 2
        self.mouse_x = cx + random.uniform(-40, 40)
        self.mouse_y = cy + random.uniform(-20, 20)

        self.mouse.move(self.mouse_x, self.mouse_y)
        self._visual_update(self.mouse_x, self.mouse_y)

    def _visual_update(self, x, y):
        if not self.visualize_mouse:
            return
        self.page.evaluate(
            "([x, y]) => window.__pw_move_cursor && window.__pw_move_cursor(x, y)",
            [x, y]
        )

    def on_page_ready(self):
        """Update visual cursor after navigation or when the page is ready."""
        if self.visualize_mouse:
            self._visual_update(self.mouse_x, self.mouse_y)

    # ------------------------------------------------
    # High Level Actions
    # ------------------------------------------------

    def prepare_for_interaction(self, locator):
        """
        Prepare for interaction by scrolling element into view and moving cursor to it.

        This method simulates the natural behavior of a user before clicking
        on an element: first ensuring the element is visible, then moving
        the mouse towards it with a human-like curved trajectory.

        Args:
            locator: Playwright Locator object pointing to the element.
                The first matching element will be used.

        Returns:
            The resolved locator (first element) for subsequent operations.

        Example:
            >>> button = page.locator("button#submit")
            >>> resolved = sim.prepare_for_interaction(button)
            >>> resolved.click()  # Now click the button

        Note:
            Call this method before performing click operations to simulate
            realistic user behavior. The method updates internal mouse_x and
            mouse_y state.
        """
        loc = locator.first
        viewport = self.page.viewport_size

        # Get initial bounding box
        box = loc.bounding_box()
        if not box:
            raise ValueError("Element has no bounding box (may not be visible)")

        # Check if scrolling is needed
        top_visible = box["y"] >= 0
        bottom_visible = box["y"] + box["height"] <= viewport["height"]
        needs_scroll = not (top_visible and bottom_visible)

        if needs_scroll:
            bring_into_view(self.page, box, viewport)
            wait_human(80, 240)
            # Re-fetch bounding box after scroll since coordinates changed
            box = loc.bounding_box()
            if not box:
                raise ValueError("Element has no bounding box after scrolling")
        else:
            wait_human(80, 240)

        self.mouse_x, self.mouse_y = move_to_box(
            self.mouse,
            box,
            current_x=self.mouse_x,
            current_y=self.mouse_y,
            on_move=self._visual_update if self.visualize_mouse else None
        )

        if random.random() < 0.5:
            wait_human(40, 160)

        return loc

    def click(self, locator):
        """
        Click an element with human-like behavior.

        This method encapsulates the complete click workflow:
        1. Scrolls the element into view if needed
        2. Moves the mouse to the element with natural motion
        3. Clicks the element

        Args:
            locator: Playwright Locator object pointing to the element.
                The first matching element will be used.

        Example:
            >>> button = page.locator("button#submit")
            >>> sim.click(button)

        Note:
            This is a convenience method that combines prepare_for_interaction()
            and click(). Use prepare_for_interaction() directly if you need
            more control over the click behavior.
        """
        loc = self.prepare_for_interaction(locator)
        loc.click()

    def navigate_to_url(self, url: str, *, cool_down=True):
        """
        Navigate to a URL with human-like behavior.

        Simulates a user navigating to a new page by:
        1. Adding a natural pre-navigation delay
        2. Moving the mouse toward the address bar area
        3. Navigating to the URL
        4. Optionally simulating post-navigation browsing behavior

        Args:
            url (str): The URL to navigate to.
            cool_down (bool, optional): Whether to simulate browsing behavior
                after navigation completes. This includes random scrolling
                and idle movements. Defaults to True.

        Example:
            >>> sim.navigate_to_url("https://example.com")
            >>> # With immediate interaction (no cool down)
            >>> sim.navigate_to_url("https://example.com", cool_down=False)

        Note:
            When cool_down=True, the method will take 1.5-3 seconds longer
            to simulate natural page scanning behavior.
        """
        wait_human(200, 900)

        vp = self.page.viewport_size
        tx = random.uniform(vp["width"] * 0.3, vp["width"] * 0.7)
        ty = random.uniform(20, 60)

        # Move mouse before navigating
        self.mouse_x, self.mouse_y = move_to_target(
            self.mouse,
            tx,
            ty,
            current_x=self.mouse_x,
            current_y=self.mouse_y,
            on_move=self._visual_update if self.visualize_mouse else None
        )

        self.page.goto(url)

        if cool_down:
            wait_human(300, 900)
            self.simulate_browsing(duration_ms=random.randint(1500, 3000))

    def type(self, locator, text: str, typos: bool = False):
        """
        Click the element and type text with human-like timing.

        Simulates realistic typing behavior by:
        1. Moving mouse to the element
        2. Clicking to focus the element
        3. Typing each character with random delays (20-80ms between keystrokes)
        4. Optionally simulating typos and corrections

        Args:
            locator: Playwright Locator object pointing to the input element.
                The first matching element will be used.
            text (str): The text to type into the element.
            typos (bool, optional): Whether to simulate typing mistakes.
                When True, occasionally types wrong characters and corrects
                them with backspace. Defaults to False.

        Example:
            >>> search_input = page.locator("input#search")
            >>> sim.type(search_input, "hello world")
            >>>
            >>> # Type with simulated typos
            >>> sim.type(search_input, "hello world", typos=True)

        Note:
            This method automatically clicks the element before typing,
            so you don't need to call click() separately.
        """
        # Resolve to a single element
        loc = locator.first

        # Move mouse to element for realism
        box = loc.bounding_box()
        if box:
            x = box["x"] + box["width"] * 0.5
            y = box["y"] + box["height"] * 0.5
            # Update mouse state
            self.mouse_x, self.mouse_y = x, y
            self.mouse.move(x, y)
            self._visual_update(x, y)
            wait_human(80, 140)

        loc.click()  # IMPORTANT: click the resolved locator, not the raw Locator object

        # Now type
        for ch in text:
            # Simulate typo with ~5% probability
            if typos and random.random() < 0.05 and ch.isalpha():
                # Type a wrong character
                wrong_char = random.choice(string.ascii_lowercase)
                self.page.keyboard.type(wrong_char)
                wait_human(30, 100)
                # Pause as if noticing the mistake
                wait_human(100, 300)
                # Backspace to correct
                self.page.keyboard.press("Backspace")
                wait_human(30, 80)

            self.page.keyboard.type(ch)
            wait_human(20, 80)

    def scroll_and_read(self, duration_ms=2000):
        """
        Simulate reading behavior with scrolling and idle movements.

        Models natural user behavior when reading a webpage by randomly:
        - Scrolling up or down (50% chance per iteration)
        - Performing small idle mouse movements
        - Pausing between actions (300-1200ms)

        Args:
            duration_ms (int, optional): Total duration of the simulation
                in milliseconds. Defaults to 2000 (2 seconds).

        Example:
            >>> # Simulate reading for 3 seconds
            >>> sim.scroll_and_read(duration_ms=3000)
            >>>
            >>> # Quick scan of the page
            >>> sim.scroll_and_read(duration_ms=1000)

        Note:
            The actual duration may slightly exceed the specified time
            due to the nature of the simulation loop.
        """
        end = time.time() + duration_ms / 1000
        while time.time() < end:
            if random.random() < 0.5:
                scroll_human(self.page, random.randint(-200, 240))

            self.mouse_x, self.mouse_y = idle_human(
                self.mouse,
                self.page,
                current_x=self.mouse_x,
                current_y=self.mouse_y
            )
            self._visual_update(self.mouse_x, self.mouse_y)

            wait_human(300, 1200)

    def simulate_browsing(self, duration_ms=2000):
        """
        Simulate general browsing behavior on a webpage.

        Models natural user browsing patterns by randomly choosing between:
        - Scrolling (50% probability): Scrolls -180 to +220 pixels
        - Idle movements (50% probability): Small mouse micro-movements

        Each action is followed by a pause of 300-1100ms.

        Args:
            duration_ms (int, optional): Total duration of the simulation
                in milliseconds. Defaults to 2000 (2 seconds).

        Example:
            >>> # Simulate casual browsing for 5 seconds
            >>> sim.simulate_browsing(duration_ms=5000)
            >>>
            >>> # Brief browsing after page load
            >>> sim.simulate_browsing(duration_ms=1500)

        Note:
            This method is automatically called by navigate_to_url()
            when cool_down=True.
        """
        end = time.time() + duration_ms / 1000
        while time.time() < end:
            action = random.choices(
                ["scroll", "idle"],
                weights=[0.5, 0.5],
                k=1
            )[0]

            if action == "scroll":
                scroll_human(self.page, random.randint(-180, 220))

            else:
                self.mouse_x, self.mouse_y = idle_human(
                    self.mouse,
                    self.page,
                    current_x=self.mouse_x,
                    current_y=self.mouse_y
                )

            wait_human(300, 1100)
