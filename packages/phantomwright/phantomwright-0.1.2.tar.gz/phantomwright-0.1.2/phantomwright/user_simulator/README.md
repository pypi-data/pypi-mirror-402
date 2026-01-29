# User Simulator

Human-like interaction simulation for Playwright automation. This module provides high-level APIs to simulate realistic user behavior, including mouse movements, typing, scrolling, and browsing patterns.

## Features

- **Bezier curve mouse movements**: Smooth, curved trajectories that mimic real human mouse motion
- **Natural timing**: Random delays with triangular distribution for human-like pauses
- **Micro-movements**: Small idle movements during pauses to simulate natural behavior
- **Human-like scrolling**: Multi-step scrolling with variable speed
- **Typing simulation**: Character-by-character typing with realistic delays
- **Both sync and async support**: Works with both Playwright sync and async APIs

## Installation

The user simulator is part of the `phantomwright` package:

```python
from phantomwright.user_simulator import SyncUserSimulator, AsyncUserSimulator
```

## Quick Start

### Sync API

```python
from playwright.sync_api import sync_playwright
from phantomwright.user_simulator import SyncUserSimulator

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("https://www.bing.com")

    # Create simulator
    sim = SyncUserSimulator(page)

    # Find search box
    search_box = page.locator("#sb_form_q")
    search_box.first.wait_for(timeout=5000)

    # Click with human-like behavior (scrolls into view + moves mouse + clicks)
    sim.click(search_box)

    # Or prepare for interaction without clicking
    # sim.prepare_for_interaction(search_box)

    # Type with human-like delays
    sim.type(search_box, "hello world")

    # Type with simulated typos
    # sim.type(search_box, "hello world", typos=True)

    # Simulate browsing behavior
    sim.simulate_browsing(duration_ms=2000)

    browser.close()
```

### Async API

```python
import asyncio
from playwright.async_api import async_playwright
from phantomwright.user_simulator import AsyncUserSimulator

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("https://www.bing.com")

        # Create simulator using factory method (recommended)
        sim = await AsyncUserSimulator.create(page)

        # Find search box
        search_box = page.locator("#sb_form_q")
        await search_box.first.wait_for(timeout=5000)

        # Click with human-like behavior
        await sim.click(search_box)

        # Type with human-like delays
        await sim.type(search_box, "hello world")

        # Simulate browsing behavior
        await sim.simulate_browsing(duration_ms=2000)

        await browser.close()

asyncio.run(main())
```

## API Reference

### SyncUserSimulator / AsyncUserSimulator

#### Constructor

```python
SyncUserSimulator(page)
AsyncUserSimulator(page)
# Or use the factory method for async (recommended):
await AsyncUserSimulator.create(page)
```

Creates a new user simulator instance.

- `page`: Playwright Page object

The simulator initializes with the mouse position near the center of the viewport (with small random offset).

> **Note**: For `AsyncUserSimulator`, use the `create()` factory method which automatically initializes the mouse position. If you use the constructor directly, you must call `await sim.init_mouse_position()` after construction.

#### Methods

##### `click(locator)`

Click an element with human-like behavior. This is a convenience method that combines `prepare_for_interaction()` and `click()`.

**Parameters:**
- `locator`: Playwright Locator object

**Behavior:**
1. Scrolls the element into view if needed
2. Moves mouse to the element using curved Bezier path
3. Clicks the element

```python
# Sync
sim.click(page.locator("button#submit"))

# Async
await sim.click(page.locator("button#submit"))
```

##### `prepare_for_interaction(locator)`

Scroll element into view and move cursor to it with human-like behavior. Returns the resolved locator for further operations.

**Parameters:**
- `locator`: Playwright Locator object

**Returns:**
- The resolved locator (first matching element)

**Behavior:**
1. Scrolls the element into view if not already visible
2. Re-fetches bounding box after scrolling (ensures accurate coordinates)
3. Waits with human-like timing (80-240ms)
4. Moves mouse to the element using curved Bezier path
5. Optionally adds a small hover hesitation

```python
# Sync
resolved = sim.prepare_for_interaction(search_box)
resolved.click()  # Manual click if needed

# Async
resolved = await sim.prepare_for_interaction(search_box)
await resolved.click()
```

##### `navigate_to_url(url, *, cool_down=True)`

Navigate to a URL with human-like behavior.

**Parameters:**
- `url`: Target URL string
- `cool_down`: Whether to simulate browsing after navigation (default: `True`)

**Behavior:**
1. Adds pre-navigation delay (200-900ms)
2. Moves mouse toward browser's address bar area
3. Navigates to the URL
4. If `cool_down=True`, simulates browsing behavior (scrolling, idle movements)

```python
# Sync
sim.navigate_to_url("https://example.com", cool_down=True)

# Async
await sim.navigate_to_url("https://example.com", cool_down=True)
```

##### `type(locator, text, typos=False)`

Click the element and type text with human-like delays.

**Parameters:**
- `locator`: Playwright Locator object
- `text`: Text string to type
- `typos`: Whether to simulate typing mistakes (default: `False`)

**Behavior:**
1. Moves mouse to the element and updates internal mouse state
2. Clicks to focus
3. Types each character with random delay (20-80ms between keystrokes)
4. If `typos=True`, occasionally (~5% chance per letter) types a wrong character, pauses, then corrects with backspace

```python
# Sync
sim.type(search_input, "hello world")
sim.type(search_input, "hello world", typos=True)  # With simulated typos

# Async
await sim.type(search_input, "hello world")
await sim.type(search_input, "hello world", typos=True)
```

##### `scroll_and_read(duration_ms=2000)`

Simulate reading behavior with scrolling and idle movements.

**Parameters:**
- `duration_ms`: Duration of the behavior simulation in milliseconds (default: 2000)

**Behavior:**
- Random scrolls up/down
- Idle micro-movements
- Pauses between actions (300-1200ms)

```python
# Sync
sim.scroll_and_read(duration_ms=3000)

# Async
await sim.scroll_and_read(duration_ms=3000)
```

##### `simulate_browsing(duration_ms=2000)`

Simulate general browsing behavior.

**Parameters:**
- `duration_ms`: Duration of the simulation in milliseconds (default: 2000)

**Behavior:**
- 50% chance of scrolling
- 50% chance of idle movements
- Pauses between actions (300-1100ms)

```python
# Sync
sim.simulate_browsing(duration_ms=2000)

# Async
await sim.simulate_browsing(duration_ms=2000)
```

## Low-Level Functions

The simulator is built on top of low-level functions available in `sync_basic.py` and `async_basic.py`:

| Function | Description |
|----------|-------------|
| `wait_human(min_ms, max_ms)` | Human-like pause with triangular distribution |
| `move_to_target(mouse, x, y, current_x, current_y)` | Move mouse along Bezier curve |
| `move_to_box(mouse, box, current_x, current_y)` | Move mouse to element center |
| `scroll_human(page, delta_y)` | Multi-step human-like scrolling |
| `bring_into_view(page, box, viewport)` | Scroll element into viewport |
| `idle_human(mouse, page, current_x, current_y)` | Small idle micro-movements |

## Mouse Movement Algorithm

The mouse movement uses quadratic Bezier curves for natural trajectories:

1. **Path calculation**: 
   - Number of steps based on distance: `max(35, distance / 8)`
   - Control point offset: `distance * random(0.15, 0.28)`

2. **Movement execution**:
   - Interpolates along the Bezier curve
   - Adds micro-jitter: `random(-0.3, 0.3)` pixels
   - Human reaction time between moves: 18-45ms

3. **Targeting**:
   - Element center with random offset: `±4` pixels

## Testing

Run the simulator tests:

```bash
pytest tests/simulator_tests/ -v
```

Visual tests with mouse tracking are available (requires headed browser):

```bash
pytest tests/simulator_tests/test_sync_simulator.py::TestMouseTrackingVisualization -v
pytest tests/simulator_tests/test_async_simulator.py::TestAsyncMouseTrackingVisualization -v
```

Screenshots are saved to `visual_out/simulator_tests/`.

## License

See the project LICENSE file.
