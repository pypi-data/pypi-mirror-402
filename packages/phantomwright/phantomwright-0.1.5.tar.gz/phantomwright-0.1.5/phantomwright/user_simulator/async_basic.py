# async_basic.py

import random
import math
import asyncio


async def wait_human(min_ms: int, max_ms: int = None):
    """Human-like pause with natural variance (async)."""
    if max_ms is None:
        max_ms = min_ms * 1.3
    duration = random.triangular(min_ms, max_ms, (min_ms + max_ms) / 2)
    await asyncio.sleep(duration / 1000)


def _bezier_curve(p0, p1, p2, t):
    """Quadratic Bezier interpolation (same as sync)."""
    return (
        (1 - t) ** 2 * p0
        + 2 * (1 - t) * t * p1
        + t ** 2 * p2
    )


async def move_to_target(mouse, target_x, target_y, *, current_x, current_y, on_move=None):
    """
    Move mouse smoothly to a coordinate using a curved Bezier path (async).
    Supports an optional async `on_move(x, y)` callback for side-effects
    such as updating a visual cursor in the page.

    Returns (new_x, new_y).
    """

    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.hypot(dx, dy)

    # 1. Step count (performance tuning)
    # For natural mouse motion: long distances should use fewer sample points
    if distance > 800:
        steps = int(distance / 45)
    elif distance > 400:
        steps = int(distance / 32)
    elif distance > 150:
        steps = int(distance / 22)
    else:
        steps = int(distance / 14)

    # Hard cap to bound step count
    steps = max(6, min(steps, 24))

    # 2. Curve (reduce curvature complexity)
    curve_strength = distance * random.uniform(0.08, 0.16)
    ctrl_x = current_x + dx * 0.5 + random.uniform(-curve_strength, curve_strength)
    ctrl_y = current_y + dy * 0.5 + random.uniform(-curve_strength, curve_strength)

    # 3. Movement (accelerate then decelerate)
    for i in range(1, steps + 1):
        t = i / steps

        # Accelerate early, decelerate later (non-linear)
        if t < 0.7:
            tt = t * 1.25
        else:
            tt = 0.875 + (t - 0.7) * 0.42

        nx = _bezier_curve(current_x, ctrl_x, target_x, tt)
        ny = _bezier_curve(current_y, ctrl_y, target_y, tt)

        # Add small jitter only in the final phase (anti-bot measure)
        if t > 0.75:
            nx += random.uniform(-0.25, 0.25)
            ny += random.uniform(-0.25, 0.25)

        await mouse.move(nx, ny)

        # call optional on_move (support both coroutine and sync callbacks)
        if on_move is not None:
            try:
                # prefer awaiting if coroutine
                if asyncio.iscoroutinefunction(on_move):
                    await on_move(nx, ny)
                else:
                    on_move(nx, ny)
            except Exception:
                # swallow errors from visual callbacks - non-critical
                pass

    return target_x, target_y


async def move_to_box(mouse, box, *, current_x, current_y, on_move=None):
    """Move to center of bounding box with small random offset."""
    cx = box["x"] + box["width"] * 0.5 + random.uniform(-4, 4)
    cy = box["y"] + box["height"] * 0.5 + random.uniform(-4, 4)
    return await move_to_target(mouse, cx, cy, current_x=current_x, current_y=current_y, on_move=on_move)


async def scroll_human(page, delta_y):
    """Human-like scrolling in multiple small wheel steps."""
    step_count = random.randint(5, 12)
    per_step = delta_y / step_count

    for _ in range(step_count):
        await page.mouse.wheel(0, per_step + random.uniform(-4, 4))
        await wait_human(40, 110)


async def bring_into_view(page, box, viewport):
    """Scroll element into view with realistic timing."""
    top_visible = box["y"] >= 0
    bottom_visible = box["y"] + box["height"] <= viewport["height"]

    if not (top_visible and bottom_visible):
        target_scroll = box["y"] - viewport["height"] * 0.35
        await page.evaluate(f"window.scrollTo(0, {int(target_scroll)})")
        await wait_human(260, 650)


async def idle_human(mouse, page, *, current_x, current_y):
    """Small idle micro-movements & small scrolls."""
    if random.random() < 0.45:
        nx = current_x + random.uniform(-6, 6)
        ny = current_y + random.uniform(-4, 4)
        await mouse.move(nx, ny)
        await wait_human(40, 90)
        return nx, ny

    if random.random() < 0.15:
        await page.mouse.wheel(0, random.uniform(-25, 25))
        await wait_human(150, 350)

    return current_x, current_y
