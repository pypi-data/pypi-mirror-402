"""Main HumanCursor class for Playwright integration."""

import asyncio
import random
import socket
import json
from typing import Any

from playwright.sync_api import Locator as SyncLocator
from playwright.async_api import Locator as AsyncLocator

from .models import (
    Vector,
    BoundingBox,
    CurveOptions,
    ClickOptions,
    ScrollOptions,
    MoveOptions,
)
from .curve_generator import HumanizeMouseTrajectory
from .randomizer import generate_random_curve_parameters, get_random_box_point
from .easing import ease_out_quint


# Default options for human-like behavior
DEFAULT_OPTIONS = {
    "move_speed": 1.75,
    "move_delay": 50,
    "hesitate": 50,
    "wait_for_click": 30,
    "scroll_speed": 250,
    "scroll_delay": 200,
}


class OverlayClient:
    """Client to send cursor positions to the visual overlay."""

    def __init__(self, port: int = 7845):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = ("127.0.0.1", port)
        self.offset_x = 0
        self.offset_y = 0

    def set_offset(self, x: float, y: float):
        """Set screen offset for viewport coordinates."""
        self.offset_x = x
        self.offset_y = y

    def send(self, x: float, y: float):
        """Send cursor position to overlay (with offset applied)."""
        screen_x = x + self.offset_x
        screen_y = y + self.offset_y
        msg = json.dumps({"x": screen_x, "y": screen_y}).encode()
        try:
            self.sock.sendto(msg, self.addr)
        except OSError:
            pass  # Overlay not running

    def close(self):
        self.sock.close()


class HumanCursor:
    """
    Human-like cursor movement for Playwright.

    Simulates natural mouse movements using Bezier curves with
    random distortions and easing functions.
    """

    def __init__(
        self,
        page: Any,
        start: Vector | None = None,
        default_options: dict | None = None,
        show_overlay: bool = False,
        overlay_port: int = 7845,
        overlay_offset: Vector | None = None
    ):
        """
        Initialize HumanCursor.

        Args:
            page: Playwright Page object
            start: Initial cursor position (defaults to 0, 0)
            default_options: Default options for all operations
            show_overlay: Enable visual overlay for debugging
            overlay_port: UDP port for overlay communication
            overlay_offset: Manual offset (x, y) for overlay position. If None, auto-detect.
        """
        self.page = page
        self.previous = start or Vector(0, 0)
        self.default_options = default_options or {}
        self.overlay = OverlayClient(overlay_port) if show_overlay else None
        self._overlay_offset_set = False
        self._manual_offset = overlay_offset

    async def _update_overlay_offset(self) -> None:
        """Update overlay offset based on browser window position."""
        if not self.overlay or self._overlay_offset_set:
            return

        if self._manual_offset:
            self.overlay.set_offset(self._manual_offset.x, self._manual_offset.y)
        # No auto-detect - user must provide overlay_offset
        self._overlay_offset_set = True

    async def move(
        self,
        selector: str | AsyncLocator,
        *,
        timeout: int = 30000,
        move_speed: float | None = None,
        move_delay: int | None = None,
        scroll_speed: int | None = None
    ) -> None:
        """
        Move cursor to an element (random point inside it).

        Args:
            selector: CSS selector string or Playwright Locator
            timeout: Maximum wait time for element (ms), 0 = no wait
            move_speed: Speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50
            scroll_speed: Duration of scroll animation (ms), default 250
        """
        box = await self._get_element_box(selector, timeout, scroll_speed)
        destination = get_random_box_point(box)

        await self.move_to(destination, move_speed=move_speed, move_delay=move_delay)

    async def move_to(
        self,
        destination: Vector,
        *,
        move_speed: float | None = None,
        move_delay: int | None = None
    ) -> None:
        """
        Move cursor to exact coordinates.

        Args:
            destination: Target position - Vector(x, y)
            move_speed: Speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50

        Example:
            await cursor.move_to(Vector(100, 200))
        """
        if move_speed is None:
            move_speed = self.default_options.get("move_speed", DEFAULT_OPTIONS["move_speed"])
        if move_delay is None:
            move_delay = self.default_options.get("move_delay", DEFAULT_OPTIONS["move_delay"])

        # Generate human-like path
        path = self._path_with_human_curve(
            self.previous,
            destination,
            move_speed
        )

        # Optional delay before moving
        if move_delay > 0:
            await asyncio.sleep(move_delay / 1000)

        # Execute the movement
        await self._trace_path(path)

        # Update current position
        self.previous = destination

    async def click(
        self,
        selector: str | AsyncLocator | None = None,
        *,
        timeout: int = 30000,
        move_speed: float | None = None,
        move_delay: int | None = None,
        scroll_speed: int | None = None,
        hesitate: int | None = None,
        wait_for_click: int | None = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: list[str] | None = None
    ) -> None:
        """
        Click on an element or at the current position.

        Args:
            selector: CSS selector string, Playwright Locator, or None for current position
            timeout: Maximum wait time for element (ms), 0 = no wait
            move_speed: Cursor speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50
            scroll_speed: Duration of scroll animation (ms), default 250
            hesitate: Pause before clicking (ms), default 50
            wait_for_click: Small delay before click (ms), default 30
            button: Mouse button ("left", "right", "middle")
            click_count: Number of clicks (1 = single, 2 = double)
            modifiers: Key modifiers ["Control"], ["Shift"], ["Alt"], ["Control", "Shift"]
                       Use ["Control"] + left click to open link in background tab
        """
        if hesitate is None:
            hesitate = self.default_options.get("hesitate", DEFAULT_OPTIONS["hesitate"])
        if wait_for_click is None:
            wait_for_click = self.default_options.get("wait_for_click", DEFAULT_OPTIONS["wait_for_click"])
        button = button or self.default_options.get("button", "left")
        click_count = click_count or self.default_options.get("click_count", 1)
        modifiers = modifiers or self.default_options.get("modifiers")

        destination = None

        if selector is not None:
            box = await self._get_element_box(selector, timeout, scroll_speed)
            destination = get_random_box_point(box)

        if destination:
            # Move to destination
            await self.move_to(
                destination,
                move_speed=move_speed,
                move_delay=move_delay
            )

        # Hesitate before clicking (human-like pause)
        if hesitate > 0:
            await asyncio.sleep(hesitate / 1000)

        # Small delay before click
        if wait_for_click > 0:
            await asyncio.sleep(wait_for_click / 1000)

        # Perform the click
        if modifiers:
            for mod in modifiers:
                await self.page.keyboard.down(mod)
            for _ in range(click_count):
                await self.page.mouse.down(button=button)
                await self.page.mouse.up(button=button)
            for mod in modifiers:
                await self.page.keyboard.up(mod)
        else:
            await self.page.mouse.click(
                self.previous.x,
                self.previous.y,
                button=button,
                click_count=click_count
            )

    async def scroll(
        self,
        delta: Vector,
        *,
        scroll_speed: int | None = None,
        scroll_delay: int | None = None
    ) -> None:
        """
        Scroll by a delta amount with momentum effect.

        Args:
            delta: Scroll amount - Vector(x, y) where positive y = scroll down
            scroll_speed: Duration of scroll animation (ms), default 250
            scroll_delay: Delay before scrolling starts (ms), default 200

        Example:
            await cursor.scroll(Vector(0, 500))   # scroll down 500px
            await cursor.scroll(Vector(0, -300))  # scroll up 300px
        """
        if scroll_speed is None:
            scroll_speed = self.default_options.get("scroll_speed", DEFAULT_OPTIONS["scroll_speed"])
        if scroll_delay is None:
            scroll_delay = self.default_options.get("scroll_delay", DEFAULT_OPTIONS["scroll_delay"])

        if scroll_delay > 0:
            await asyncio.sleep(scroll_delay / 1000)

        await self._momentum_wheel_scroll(
            delta.x,
            delta.y,
            scroll_speed
        )

    async def scroll_to(
        self,
        selector: str | AsyncLocator,
        *,
        timeout: int = 30000
    ) -> None:
        """
        Scroll an element into view.

        Args:
            selector: CSS selector string or Playwright Locator
            timeout: Maximum wait time for element (ms), 0 = no wait
        """
        # _get_element_box handles waiting and scrolling into view
        await self._get_element_box(selector, timeout)

    async def _smooth_scroll_to_element(self, locator: AsyncLocator, scroll_speed: int | None = None) -> None:
        """Smoothly scroll element into view with human-like momentum."""
        # Get viewport size
        viewport = self.page.viewport_size
        if not viewport:
            viewport = {"width": 1920, "height": 1080}

        viewport_height = viewport["height"]

        # Get element position
        box = await locator.bounding_box()
        if not box:
            # Element not rendered, fallback to instant scroll
            await locator.scroll_into_view_if_needed()
            return

        element_center_y = box["y"] + box["height"] / 2

        # Check if element is within viewport
        if 0 < element_center_y < viewport_height:
            return  # Already visible

        # Calculate scroll amount to center element
        scroll_amount = element_center_y - viewport_height / 2

        # Use momentum scroll
        if scroll_speed is None:
            scroll_speed = self.default_options.get("scroll_speed", DEFAULT_OPTIONS["scroll_speed"])
        await self.scroll(Vector(0, scroll_amount), scroll_speed=scroll_speed, scroll_delay=0)

    async def _get_element_box(self, selector: str | AsyncLocator, timeout: int, scroll_speed: int | None = None) -> BoundingBox:
        """
        Get element bounding box with automatic waiting.

        Args:
            selector: CSS selector string or Playwright Locator
            timeout: Maximum wait time in milliseconds (0 = no wait)
            scroll_speed: Duration of scroll animation (ms), None = use default

        Returns:
            BoundingBox of the element

        Raises:
            TimeoutError: If element not found within timeout
            ValueError: If element has no bounding box
        """
        # Convert string to Locator
        if isinstance(selector, str):
            locator = self.page.locator(selector)
        else:
            locator = selector

        # Wait for element to be visible
        if timeout > 0:
            await locator.wait_for(state="visible", timeout=timeout)

        # Scroll into view if needed (with smooth momentum)
        await self._smooth_scroll_to_element(locator, scroll_speed)

        # Get bounding box
        box = await locator.bounding_box()
        if not box:
            raise ValueError("Element has no bounding box")

        return BoundingBox(x=box["x"], y=box["y"], width=box["width"], height=box["height"])

    def _path_with_human_curve(
        self,
        start: Vector,
        end: Vector,
        speed: float | None = None
    ) -> list[Vector]:
        """
        Generate a human-like path between two points.

        Args:
            start: Starting position
            end: Ending position
            speed: Optional speed multiplier

        Returns:
            List of points along the path
        """
        # Generate random curve parameters based on distance
        curve_options = generate_random_curve_parameters(start, end, speed)

        # Generate the trajectory
        generator = HumanizeMouseTrajectory(start, end, curve_options)
        return generator.generate_curve()

    async def _trace_path(self, vectors: list[Vector]) -> None:
        """
        Execute mouse movement along a path.

        Args:
            vectors: List of points to move through
        """
        # Update overlay offset on first movement
        if self.overlay and not self._overlay_offset_set:
            await self._update_overlay_offset()

        for vector in vectors:
            await self.page.mouse.move(vector.x, vector.y)
            # Send position to overlay if enabled
            if self.overlay:
                self.overlay.send(vector.x, vector.y)
            # Small random delay between movements for realism
            delay = random.uniform(1, 5) / 1000  # 1-5ms
            await asyncio.sleep(delay)

    async def _momentum_wheel_scroll(
        self,
        delta_x: float,
        delta_y: float,
        duration_ms: int
    ) -> None:
        """
        Perform smooth momentum-based wheel scrolling.

        Uses easing to simulate natural scroll behavior where
        scrolling starts fast and slows down.

        Args:
            delta_x: Total horizontal scroll amount
            delta_y: Total vertical scroll amount
            duration_ms: Duration of scroll animation
        """
        if delta_x == 0 and delta_y == 0:
            return

        # Number of scroll steps
        steps = max(10, duration_ms // 10)
        step_duration = duration_ms / steps / 1000  # Convert to seconds

        # Track cumulative scroll
        scrolled_x = 0.0
        scrolled_y = 0.0

        for i in range(steps):
            # Calculate progress with easing
            t = (i + 1) / steps
            eased_t = ease_out_quint(t)

            # Calculate target scroll at this point
            target_x = delta_x * eased_t
            target_y = delta_y * eased_t

            # Calculate step delta
            step_x = target_x - scrolled_x
            step_y = target_y - scrolled_y

            # Perform scroll step
            if step_x != 0 or step_y != 0:
                await self.page.mouse.wheel(step_x, step_y)

            scrolled_x = target_x
            scrolled_y = target_y

            # Wait between steps
            await asyncio.sleep(step_duration)


class SyncHumanCursor:
    """
    Synchronous wrapper for HumanCursor.

    Use this with Playwright's sync_api.
    """

    def __init__(
        self,
        page: Any,
        start: Vector | None = None,
        default_options: dict | None = None,
        show_overlay: bool = False,
        overlay_port: int = 7845,
        overlay_offset: Vector | None = None
    ):
        """
        Initialize SyncHumanCursor.

        Args:
            page: Playwright sync Page object
            start: Initial cursor position
            default_options: Default options for all operations
            show_overlay: Enable visual overlay for debugging
            overlay_port: UDP port for overlay communication
            overlay_offset: Manual offset (x, y) for overlay position
        """
        self.page = page
        self.previous = start or Vector(0, 0)
        self.default_options = default_options or {}
        self.overlay = OverlayClient(overlay_port) if show_overlay else None
        self._overlay_offset_set = False
        self._manual_offset = overlay_offset

    def _update_overlay_offset(self) -> None:
        """Update overlay offset based on browser window position."""
        if not self.overlay or self._overlay_offset_set:
            return

        if self._manual_offset:
            self.overlay.set_offset(self._manual_offset.x, self._manual_offset.y)
        self._overlay_offset_set = True

    def move(
        self,
        selector: str | SyncLocator,
        *,
        timeout: int = 30000,
        move_speed: float | None = None,
        move_delay: int | None = None,
        scroll_speed: int | None = None
    ) -> None:
        """
        Move cursor to an element (random point inside it).

        Args:
            selector: CSS selector string or Playwright Locator
            timeout: Maximum wait time for element (ms), 0 = no wait
            move_speed: Speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50
            scroll_speed: Duration of scroll animation (ms), default 250
        """
        box = self._get_element_box(selector, timeout, scroll_speed)
        destination = get_random_box_point(box)
        self.move_to(destination, move_speed=move_speed, move_delay=move_delay)

    def move_to(
        self,
        destination: Vector,
        *,
        move_speed: float | None = None,
        move_delay: int | None = None
    ) -> None:
        """
        Move cursor to exact coordinates.

        Args:
            destination: Target position - Vector(x, y)
            move_speed: Speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50

        Example:
            cursor.move_to(Vector(100, 200))
        """
        import time

        if move_speed is None:
            move_speed = self.default_options.get("move_speed", DEFAULT_OPTIONS["move_speed"])
        if move_delay is None:
            move_delay = self.default_options.get("move_delay", DEFAULT_OPTIONS["move_delay"])

        path = self._path_with_human_curve(
            self.previous,
            destination,
            move_speed
        )

        if move_delay > 0:
            time.sleep(move_delay / 1000)

        self._trace_path(path)
        self.previous = destination

    def click(
        self,
        selector: str | SyncLocator | None = None,
        *,
        timeout: int = 30000,
        move_speed: float | None = None,
        move_delay: int | None = None,
        scroll_speed: int | None = None,
        hesitate: int | None = None,
        wait_for_click: int | None = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: list[str] | None = None
    ) -> None:
        """
        Click on an element or at the current position.

        Args:
            selector: CSS selector string, Playwright Locator, or None for current position
            timeout: Maximum wait time for element (ms), 0 = no wait
            move_speed: Cursor speed multiplier (higher = faster), default 1.75
            move_delay: Delay before moving (ms), default 50
            scroll_speed: Duration of scroll animation (ms), default 250
            hesitate: Pause before clicking (ms), default 50
            wait_for_click: Small delay before click (ms), default 30
            button: Mouse button ("left", "right", "middle")
            click_count: Number of clicks (1 = single, 2 = double)
            modifiers: Key modifiers ["Control"], ["Shift"], ["Alt"], ["Control", "Shift"]
                       Use ["Control"] + left click to open link in background tab
        """
        import time

        if hesitate is None:
            hesitate = self.default_options.get("hesitate", DEFAULT_OPTIONS["hesitate"])
        if wait_for_click is None:
            wait_for_click = self.default_options.get("wait_for_click", DEFAULT_OPTIONS["wait_for_click"])
        button = button or self.default_options.get("button", "left")
        click_count = click_count or self.default_options.get("click_count", 1)
        modifiers = modifiers or self.default_options.get("modifiers")

        destination = None

        if selector is not None:
            box = self._get_element_box(selector, timeout, scroll_speed)
            destination = get_random_box_point(box)

        if destination:
            self.move_to(
                destination,
                move_speed=move_speed,
                move_delay=move_delay
            )

        if hesitate > 0:
            time.sleep(hesitate / 1000)

        if wait_for_click > 0:
            time.sleep(wait_for_click / 1000)

        # Perform the click
        if modifiers:
            for mod in modifiers:
                self.page.keyboard.down(mod)
            for _ in range(click_count):
                self.page.mouse.down(button=button)
                self.page.mouse.up(button=button)
            for mod in modifiers:
                self.page.keyboard.up(mod)
        else:
            self.page.mouse.click(
                self.previous.x,
                self.previous.y,
                button=button,
                click_count=click_count
            )

    def scroll(
        self,
        delta: Vector,
        *,
        scroll_speed: int | None = None,
        scroll_delay: int | None = None
    ) -> None:
        """
        Scroll by a delta amount with momentum effect.

        Args:
            delta: Scroll amount - Vector(x, y) where positive y = scroll down
            scroll_speed: Duration of scroll animation (ms), default 250
            scroll_delay: Delay before scrolling starts (ms), default 200

        Example:
            cursor.scroll(Vector(0, 500))   # scroll down 500px
            cursor.scroll(Vector(0, -300))  # scroll up 300px
        """
        import time

        if scroll_speed is None:
            scroll_speed = self.default_options.get("scroll_speed", DEFAULT_OPTIONS["scroll_speed"])
        if scroll_delay is None:
            scroll_delay = self.default_options.get("scroll_delay", DEFAULT_OPTIONS["scroll_delay"])

        if scroll_delay > 0:
            time.sleep(scroll_delay / 1000)

        self._momentum_wheel_scroll(delta.x, delta.y, scroll_speed)

    def _smooth_scroll_to_element(self, locator: SyncLocator, scroll_speed: int | None = None) -> None:
        """Smoothly scroll element into view with human-like momentum."""
        viewport = self.page.viewport_size
        if not viewport:
            viewport = {"width": 1920, "height": 1080}

        viewport_height = viewport["height"]

        box = locator.bounding_box()
        if not box:
            locator.scroll_into_view_if_needed()
            return

        element_center_y = box["y"] + box["height"] / 2

        if 0 < element_center_y < viewport_height:
            return

        scroll_amount = element_center_y - viewport_height / 2
        if scroll_speed is None:
            scroll_speed = self.default_options.get("scroll_speed", DEFAULT_OPTIONS["scroll_speed"])
        self.scroll(Vector(0, scroll_amount), scroll_speed=scroll_speed, scroll_delay=0)

    def _get_element_box(self, selector: str | SyncLocator, timeout: int, scroll_speed: int | None = None) -> BoundingBox:
        """
        Get element bounding box with automatic waiting.

        Args:
            selector: CSS selector string or Playwright Locator
            timeout: Maximum wait time in milliseconds (0 = no wait)
            scroll_speed: Duration of scroll animation (ms), None = use default

        Returns:
            BoundingBox of the element

        Raises:
            TimeoutError: If element not found within timeout
            ValueError: If element has no bounding box
        """
        # Convert string to Locator
        if isinstance(selector, str):
            locator = self.page.locator(selector)
        else:
            locator = selector

        # Wait for element to be visible
        if timeout > 0:
            locator.wait_for(state="visible", timeout=timeout)

        # Scroll into view if needed (with smooth momentum)
        self._smooth_scroll_to_element(locator, scroll_speed)

        # Get bounding box
        box = locator.bounding_box()
        if not box:
            raise ValueError("Element has no bounding box")

        return BoundingBox(x=box["x"], y=box["y"], width=box["width"], height=box["height"])

    def _path_with_human_curve(
        self,
        start: Vector,
        end: Vector,
        speed: float | None = None
    ) -> list[Vector]:
        """Generate a human-like path between two points."""
        curve_options = generate_random_curve_parameters(start, end, speed)
        generator = HumanizeMouseTrajectory(start, end, curve_options)
        return generator.generate_curve()

    def _trace_path(self, vectors: list[Vector]) -> None:
        """Execute mouse movement along a path."""
        import time

        # Update overlay offset on first movement
        if self.overlay and not self._overlay_offset_set:
            self._update_overlay_offset()

        for vector in vectors:
            self.page.mouse.move(vector.x, vector.y)
            # Send position to overlay if enabled
            if self.overlay:
                self.overlay.send(vector.x, vector.y)
            delay = random.uniform(1, 5) / 1000
            time.sleep(delay)

    def _momentum_wheel_scroll(
        self,
        delta_x: float,
        delta_y: float,
        duration_ms: int
    ) -> None:
        """Perform smooth momentum-based wheel scrolling."""
        import time

        if delta_x == 0 and delta_y == 0:
            return

        steps = max(10, duration_ms // 10)
        step_duration = duration_ms / steps / 1000

        scrolled_x = 0.0
        scrolled_y = 0.0

        for i in range(steps):
            t = (i + 1) / steps
            eased_t = ease_out_quint(t)

            target_x = delta_x * eased_t
            target_y = delta_y * eased_t

            step_x = target_x - scrolled_x
            step_y = target_y - scrolled_y

            if step_x != 0 or step_y != 0:
                self.page.mouse.wheel(step_x, step_y)

            scrolled_x = target_x
            scrolled_y = target_y

            time.sleep(step_duration)
