"""Asynchronous user behavior simulation module.

This module provides high-level APIs to simulate realistic human-like
interactions with web pages using Playwright's async API.
"""

import random
import time
import asyncio
import string

from .script import _VISUAL_CURSOR_JS
from .async_basic import (
    wait_human,
    move_to_target,
    move_to_box,
    scroll_human,
    bring_into_view,
    idle_human,
)


class AsyncUserSimulator:
    """
    High-level asynchronous user behavior simulation.

    This class provides async methods to simulate realistic human-like
    interactions with web pages, including mouse movements, typing,
    scrolling, and browsing.

    Attributes:
        page: Playwright async Page object.
        mouse: Playwright async Mouse object for mouse operations.
        keyboard: Playwright async Keyboard object for keyboard operations.
        mouse_x (float): Current mouse X coordinate.
        mouse_y (float): Current mouse Y coordinate.

    Example:
        >>> import asyncio
        >>> from playwright.async_api import async_playwright
        >>> from phantomwright.user_simulator import AsyncUserSimulator
        >>>
        >>> async def main():
        ...     async with async_playwright() as p:
        ...         browser = await p.chromium.launch(headless=False)
        ...         page = await browser.new_page(viewport={"width": 1280, "height": 900})
        ...         await page.goto("https://example.com")
        ...         sim = await AsyncUserSimulator.create(page, visualize_mouse=True)
        ...         await sim.simulate_browsing(duration_ms=2000)
        ...         await browser.close()
        >>>
        >>> asyncio.run(main())

    Note:
        Use the `await AsyncUserSimulator.create(page)` factory method to create
        an instance. This automatically initializes the mouse position.
    """

    def __init__(self, page, *, visualize_mouse: bool = False):
        """
        Initialize the AsyncUserSimulator.

        Creates a new simulator instance and calculates the initial mouse
        position near the center of the viewport. Note that the mouse is
        NOT moved during __init__ - use the `create()` factory method instead.

        Args:
            page: Playwright async Page object. Must have a viewport set.
            visualize_mouse: If True, inject the visual cursor script on page init.

        Raises:
            TypeError: If page.viewport_size is None (viewport not set).

        Example:
            >>> page = await browser.new_page(viewport={"width": 1280, "height": 900})
            >>> await page.goto("https://example.com")
            >>> sim = await AsyncUserSimulator.create(page, visualize_mouse=True)
        """
        self.page = page
        self.mouse = page.mouse
        self.keyboard = page.keyboard
        self.visualize_mouse = visualize_mouse

        vp = self.page.viewport_size
        cx, cy = vp["width"] / 2, vp["height"] / 2

        self.mouse_x = cx + random.uniform(-40, 40)
        self.mouse_y = cy + random.uniform(-20, 20)
        self._initialized = False

    @classmethod
    async def create(cls, page, *, visualize_mouse: bool = False):
        """
        Create and initialize an AsyncUserSimulator instance.

        This is the recommended way to create an AsyncUserSimulator.
        It automatically initializes the mouse position and optionally
        injects the visual cursor script when `visualize_mouse=True`.

        Args:
            page: Playwright async Page object. Must have a viewport set.
            visualize_mouse: If True, enable in-page visual cursor.

        Returns:
            AsyncUserSimulator: A fully initialized simulator instance.

        Example:
            >>> sim = await AsyncUserSimulator.create(page, visualize_mouse=True)
            >>> # Ready to use immediately!
        """
        instance = cls(page, visualize_mouse=visualize_mouse)
        if visualize_mouse:
            await instance._init_visual_cursor()
        await instance.init_mouse_position()
        return instance

    async def init_mouse_position(self):
        """
        Initialize the mouse position asynchronously.

        This method is called automatically when using the `create()` factory.
        You only need to call it manually if you used the constructor directly.

        Example:
            >>> sim = AsyncUserSimulator(page)
            >>> await sim.init_mouse_position()  # Required if not using create()
        """
        await self.mouse.move(self.mouse_x, self.mouse_y)
        self._initialized = True
        if self.visualize_mouse:
            await self._visual_update(self.mouse_x, self.mouse_y)

    async def _init_visual_cursor(self):
        """Inject the visual cursor initialization script into the page."""
        await self.page.add_init_script(_VISUAL_CURSOR_JS)

    async def _visual_update(self, x, y):
        """Update the in-page visual cursor (async)."""
        if not self.visualize_mouse:
            return
        await self.page.evaluate(
            "([x, y]) => window.__pw_move_cursor && window.__pw_move_cursor(x, y)",
            [x, y]
        )

    async def on_page_ready(self):
        if self.visualize_mouse:
            await self._visual_update(self.mouse_x, self.mouse_y)

    # --------------------------------------------------------
    # High Level Actions
    # --------------------------------------------------------

    async def prepare_for_interaction(self, locator):
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
            >>> resolved = await sim.prepare_for_interaction(button)
            >>> await resolved.click()  # Now click the button

        Note:
            Call this method before performing click operations to simulate
            realistic user behavior. The method updates internal mouse_x and
            mouse_y state.
        """
        loc = locator.first
        viewport = self.page.viewport_size

        # Get initial bounding box
        box = await loc.bounding_box()
        if not box:
            raise ValueError("Element has no bounding box (may not be visible)")

        # Check if scrolling is needed
        top_visible = box["y"] >= 0
        bottom_visible = box["y"] + box["height"] <= viewport["height"]
        needs_scroll = not (top_visible and bottom_visible)

        if needs_scroll:
            await bring_into_view(self.page, box, viewport)
            await wait_human(80, 240)
            # Re-fetch bounding box after scroll since coordinates changed
            box = await loc.bounding_box()
            if not box:
                raise ValueError("Element has no bounding box after scrolling")
        else:
            await wait_human(80, 240)

        self.mouse_x, self.mouse_y = await move_to_box(
            self.mouse,
            box,
            current_x=self.mouse_x,
            current_y=self.mouse_y,
            on_move=self._visual_update if self.visualize_mouse else None
        )

        if random.random() < 0.5:
            await wait_human(40, 160)

        return loc

    async def click(self, locator):
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
            >>> await sim.click(button)

        Note:
            This is a convenience method that combines prepare_for_interaction()
            and click(). Use prepare_for_interaction() directly if you need
            more control over the click behavior.
        """
        loc = await self.prepare_for_interaction(locator)
        await loc.click()

    async def navigate_to_url(self, url: str, *, cool_down=True):
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
            >>> await sim.navigate_to_url("https://example.com")
            >>> # With immediate interaction (no cool down)
            >>> await sim.navigate_to_url("https://example.com", cool_down=False)

        Note:
            When cool_down=True, the method will take 1.5-3 seconds longer
            to simulate natural page scanning behavior.
        """
        await wait_human(200, 900)

        vp = self.page.viewport_size
        tx = random.uniform(vp["width"] * 0.3, vp["width"] * 0.7)
        ty = random.uniform(20, 60)

        self.mouse_x, self.mouse_y = await move_to_target(
            self.mouse,
            tx,
            ty,
            current_x=self.mouse_x,
            current_y=self.mouse_y,
            on_move=self._visual_update if self.visualize_mouse else None
        )

        await self.page.goto(url)

        if cool_down:
            await wait_human(300, 900)
            await self.simulate_browsing(duration_ms=random.randint(1500, 3000))

    async def type(self, locator, text: str, typos: bool = False):
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
            >>> await sim.type(search_input, "hello world")
            >>>
            >>> # Type with simulated typos
            >>> await sim.type(search_input, "hello world", typos=True)

        Note:
            This method automatically clicks the element before typing,
            so you don't need to call click() separately.
        """
        loc = locator.first

        box = await loc.bounding_box()
        if box:
            x = box["x"] + box["width"] * 0.5
            y = box["y"] + box["height"] * 0.5
            # Update mouse state
            self.mouse_x, self.mouse_y = x, y
            await self.mouse.move(x, y)
            if self.visualize_mouse:
                await self._visual_update(x, y)
            await wait_human(80, 140)

        await loc.click()

        for ch in text:
            # Simulate typo with ~5% probability
            if typos and random.random() < 0.05 and ch.isalpha():
                # Type a wrong character
                wrong_char = random.choice(string.ascii_lowercase)
                await self.keyboard.type(wrong_char)
                await wait_human(30, 100)
                # Pause as if noticing the mistake
                await wait_human(100, 300)
                # Backspace to correct
                await self.keyboard.press("Backspace")
                await wait_human(30, 80)

            await self.keyboard.type(ch)
            await wait_human(20, 80)

    async def scroll_and_read(self, duration_ms=2000):
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
            >>> await sim.scroll_and_read(duration_ms=3000)
            >>>
            >>> # Quick scan of the page
            >>> await sim.scroll_and_read(duration_ms=1000)

        Note:
            The actual duration may slightly exceed the specified time
            due to the nature of the simulation loop.
        """
        end = time.time() + duration_ms / 1000
        while time.time() < end:
            if random.random() < 0.5:
                await scroll_human(self.page, random.randint(-200, 240))

            self.mouse_x, self.mouse_y = await idle_human(
                self.mouse,
                self.page,
                current_x=self.mouse_x,
                current_y=self.mouse_y
            )

            if self.visualize_mouse:
                await self._visual_update(self.mouse_x, self.mouse_y)

            await wait_human(300, 1200)

    async def simulate_browsing(self, duration_ms=2000):
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
            >>> await sim.simulate_browsing(duration_ms=5000)
            >>>
            >>> # Brief browsing after page load
            >>> await sim.simulate_browsing(duration_ms=1500)

        Note:
            This method is automatically called by navigate_to_url()
            when cool_down=True.
        """
        end = time.time() + duration_ms / 1000
        while time.time() < end:
            action = random.choices(["scroll", "idle"], weights=[0.5, 0.5])[0]

            if action == "scroll":
                await scroll_human(self.page, random.randint(-180, 220))

            else:
                self.mouse_x, self.mouse_y = await idle_human(
                    self.mouse,
                    self.page,
                    current_x=self.mouse_x,
                    current_y=self.mouse_y
                )

                if self.visualize_mouse:
                    await self._visual_update(self.mouse_x, self.mouse_y)

            await wait_human(300, 1100)
