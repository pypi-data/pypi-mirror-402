# smooth-cursor-playwright

Human-like cursor movements for Playwright automation using Bezier curves with randomized control points and easing functions.

## Features

- **Bezier curve trajectories** - Natural mouse movement paths with randomized control points
- **Momentum scrolling** - Smooth scroll animations with easing
- **Sync and Async API** - Works with both `playwright.sync_api` and `playwright.async_api`
- **Visual debugging overlay** - Optional cursor visualization for development
- **Configurable parameters** - Fine-tune speed, hesitation, and movement characteristics

## Installation

```bash
pip install smooth-cursor-playwright
```

## Quick Start

### Synchronous API

```python
from playwright.sync_api import sync_playwright
from human_cursor import SyncHumanCursor, Vector

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")

    cursor = SyncHumanCursor(page)

    # Click using Locator (recommended)
    submit_btn = page.locator("button#submit")
    cursor.click(submit_btn)

    # Or use CSS selector string
    cursor.click("input#search")

    # Scroll down
    cursor.scroll(Vector(0, 500))

    browser.close()
```

### Asynchronous API

```python
import asyncio
from playwright.async_api import async_playwright
from human_cursor import HumanCursor, Vector

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com")

        cursor = HumanCursor(page)

        # Click using Locator (recommended)
        submit_btn = page.locator("button#submit")
        await cursor.click(submit_btn)

        # Or use CSS selector string
        await cursor.click("input#search")

        # Scroll down
        await cursor.scroll(Vector(0, 500))

        await browser.close()

asyncio.run(main())
```

## Default Values

The library uses these defaults for human-like behavior:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `move_speed` | 1.75 | Cursor movement speed multiplier |
| `move_delay` | 50 ms | Delay before starting movement |
| `hesitate` | 50 ms | Pause before clicking |
| `wait_for_click` | 30 ms | Small delay before click action |
| `scroll_speed` | 250 ms | Scroll animation duration |
| `scroll_delay` | 200 ms | Delay before scrolling starts |

Access defaults programmatically:

```python
from human_cursor import DEFAULT_OPTIONS
print(DEFAULT_OPTIONS)
# {'move_speed': 1.75, 'move_delay': 50, 'hesitate': 50, 'wait_for_click': 30, 'scroll_speed': 250, 'scroll_delay': 200}
```

## API Reference

### HumanCursor / SyncHumanCursor

#### Constructor

```python
cursor = HumanCursor(
    page,                    # Playwright Page object
    start=Vector(0, 0),      # Initial cursor position
    default_options={},      # Override default options
    show_overlay=False,      # Enable visual overlay
    overlay_port=7845,       # UDP port for overlay
    overlay_offset=None      # Manual offset for overlay (Vector)
)
```

#### Methods

##### `click(selector, **options)`

Click on an element or current position. Accepts **Locator** or CSS selector string.

```python
# Using Locator (recommended)
button = page.locator("button#submit")
await cursor.click(button)

# Using CSS selector
await cursor.click("button#submit")

# Click at current position
await cursor.click()

# Full options
await cursor.click(
    page.locator("button"),  # Locator, CSS selector, or None
    timeout=30000,           # Wait timeout (ms)
    move_speed=1.75,         # Speed multiplier (default: 1.75)
    move_delay=50,           # Delay before moving (ms, default: 50)
    scroll_speed=250,        # Scroll animation duration (ms, default: 250)
    hesitate=50,             # Pause before clicking (ms, default: 50)
    wait_for_click=30,       # Delay before click (ms, default: 30)
    button="left",           # Mouse button: "left", "right", "middle"
    click_count=1,           # Number of clicks (2 = double-click)
    modifiers=None           # Key modifiers: ["Control"], ["Shift"], ["Alt"]
)
```

##### `move(selector, **options)`

Move cursor to an element (random point inside it). Accepts **Locator** or CSS selector string.

```python
# Using Locator (recommended)
search_input = page.locator("input#search")
await cursor.move(search_input)

# Using CSS selector
await cursor.move("input#search")

# Full options
await cursor.move(
    page.locator("input"),   # Locator or CSS selector
    timeout=30000,           # Wait timeout (ms)
    move_speed=1.75,         # Speed multiplier (default: 1.75)
    move_delay=50,           # Delay before moving (ms, default: 50)
    scroll_speed=250         # Scroll animation duration (ms, default: 250)
)
```

##### `move_to(destination, **options)`

Move cursor to exact coordinates.

```python
await cursor.move_to(
    Vector(100, 200),        # Target coordinates
    move_speed=1.75,         # Speed multiplier (default: 1.75)
    move_delay=50            # Delay before moving (ms, default: 50)
)
```

##### `scroll(delta, **options)`

Scroll by a delta amount with momentum effect.

```python
await cursor.scroll(
    Vector(0, 500),          # Scroll amount (positive y = down)
    scroll_speed=250,        # Animation duration (ms, default: 250)
    scroll_delay=200         # Delay before scrolling (ms, default: 200)
)
```

##### `scroll_to(selector, **options)`

Scroll an element into view. Accepts **Locator** or CSS selector string.

```python
# Using Locator
footer = page.locator("div#footer")
await cursor.scroll_to(footer)

# Using CSS selector
await cursor.scroll_to("div#footer", timeout=30000)
```

## Configuration Options

### Override Default Options

Pass custom defaults to the constructor:

```python
cursor = SyncHumanCursor(
    page,
    default_options={
        "move_speed": 2.0,       # Faster movements
        "hesitate": 100,         # Longer hesitation
        "wait_for_click": 50,    # Longer delay before click
        "scroll_speed": 300,     # Slower scroll animations
    }
)
```

### Speed Control

The `move_speed` parameter controls cursor velocity:
- `< 1.0` - Slower than default
- `1.0` - Normal speed
- `1.75` - Default (slightly fast, natural feel)
- `> 2.0` - Fast movements

### Modifiers for Click

Use keyboard modifiers with clicks:

```python
link = page.locator("a.external-link")

# Ctrl+Click to open link in new tab
await cursor.click(link, modifiers=["Control"])

# Shift+Click for range selection
await cursor.click(link, modifiers=["Shift"])

# Multiple modifiers
await cursor.click(link, modifiers=["Control", "Shift"])
```

## Visual Debugging Overlay

Enable the cursor overlay to visualize movements during development:

```python
cursor = SyncHumanCursor(
    page,
    show_overlay=True,
    overlay_offset=Vector(100, 150)  # Browser window position offset
)
```

Run the overlay server (requires separate script with tkinter):

```python
# cursor_overlay.py
import tkinter as tk
import socket
import json

root = tk.Tk()
root.attributes('-topmost', True)
root.attributes('-transparentcolor', 'white')
root.overrideredirect(True)
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

canvas = tk.Canvas(root, bg='white', highlightthickness=0)
canvas.pack(fill='both', expand=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 7845))
sock.setblocking(False)

cursor_dot = canvas.create_oval(0, 0, 10, 10, fill='red', outline='darkred')

def update():
    try:
        data, _ = sock.recvfrom(1024)
        pos = json.loads(data)
        canvas.coords(cursor_dot, pos['x']-5, pos['y']-5, pos['x']+5, pos['y']+5)
    except BlockingIOError:
        pass
    root.after(10, update)

update()
root.mainloop()
```

## Types

The package exports these types for type hints:

```python
from human_cursor import (
    Vector,              # Point with x, y coordinates
    BoundingBox,         # Element bounding box
    CurveOptions,        # Bezier curve parameters
    ClickOptions,        # Click operation options
    ScrollOptions,       # Scroll operation options
    MoveOptions,         # Move operation options
    DEFAULT_OPTIONS,     # Default configuration values
)
```

## How It Works

1. **Path Generation** - Calculates a Bezier curve between start and end points with randomized control points
2. **Trajectory Humanization** - Applies random distortions to simulate natural hand movement
3. **Easing Functions** - Uses easing (ease-out-quint) for acceleration/deceleration
4. **Micro-delays** - Adds small random delays between movement steps

## License

MIT License - see [LICENSE](LICENSE) for details.

## Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
cd human_cursor
python -m build

# Check the package
twine check dist/*

# Upload to TestPyPI (optional)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```
