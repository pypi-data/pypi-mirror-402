"""
Window and display management system.
"""
from typing import Optional, Callable, Tuple
from .events import EventDispatcher, EventType, get_event_dispatcher


class Window:
    """Window manager for display and context management."""
    
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "Core",
        fullscreen: bool = False,
        vsync: bool = True,
        resizable: bool = True
    ):
        """
        Initialize window.
        
        Args:
            width: Window width
            height: Window height
            title: Window title
            fullscreen: Start in fullscreen mode
            vsync: Enable vertical sync
            resizable: Allow window resizing
        """
        self.width = width
        self.height = height
        self.title = title
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.resizable = resizable
        
        self._native_window = None  # Will be set by graphics backend
        self._should_close = False
        self._focused = True
        
        self.event_dispatcher = get_event_dispatcher()
    
    def create(self) -> bool:
        """
        Create the window.
        Returns True if successful.
        Note: Actual implementation depends on graphics backend (OpenGL, Vulkan, etc.)
        """
        # Placeholder - actual implementation would create native window
        # This is a stub that can be extended with actual windowing library
        return True
    
    def destroy(self):
        """Destroy the window."""
        self._should_close = True
    
    def should_close(self) -> bool:
        """Check if window should close."""
        return self._should_close
    
    def swap_buffers(self):
        """Swap front and back buffers."""
        # Placeholder - actual implementation depends on graphics backend
        pass
    
    def poll_events(self):
        """Poll window events."""
        # Placeholder - would poll native window events
        # and dispatch them through event system
        pass
    
    def set_title(self, title: str):
        """Set window title."""
        self.title = title
        # Update native window title
    
    def set_size(self, width: int, height: int):
        """Set window size."""
        if self.width != width or self.height != height:
            self.width = width
            self.height = height
            self.event_dispatcher.dispatch_immediate(
                EventType.WINDOW_RESIZE,
                {"width": width, "height": height}
            )
    
    def get_size(self) -> Tuple[int, int]:
        """Get window size."""
        return (self.width, self.height)
    
    def get_aspect_ratio(self) -> float:
        """Get window aspect ratio."""
        return self.width / self.height if self.height > 0 else 1.0
    
    def set_fullscreen(self, fullscreen: bool):
        """Set fullscreen mode."""
        if self.fullscreen != fullscreen:
            self.fullscreen = fullscreen
            # Update native window
    
    def set_vsync(self, vsync: bool):
        """Set VSync mode."""
        self.vsync = vsync
        # Update graphics context
    
    def set_focused(self, focused: bool):
        """Set window focus state (internal use)."""
        if self._focused != focused:
            self._focused = focused
            event_type = EventType.WINDOW_FOCUS if focused else EventType.WINDOW_LOST_FOCUS
            self.event_dispatcher.dispatch_immediate(event_type)
    
    def is_focused(self) -> bool:
        """Check if window is focused."""
        return self._focused
    
    def center(self):
        """Center window on screen."""
        # Placeholder - would center native window
        pass
    
    def __repr__(self):
        return f"Window({self.width}x{self.height}, title='{self.title}', fullscreen={self.fullscreen})"

