"""
Core engine class - main entry point and game loop.
"""
from typing import Optional, Callable
from .time import Time, get_time
from .input import Input, get_input
from .window import Window
from .events import EventDispatcher, EventType, get_event_dispatcher
from .resources import ResourceManager, get_resource_manager
from .components import EntityManager, get_entity_manager
from .config import Config, get_config
from .logger import Logger, get_logger, LogLevel


class Engine:
    """Main engine class."""
    
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "Core",
        fullscreen: bool = False
    ):
        """
        Initialize engine.
        
        Args:
            width: Window width
            height: Window height
            title: Window title
            fullscreen: Start in fullscreen
        """
        self.logger = get_logger()
        self.config = get_config()
        self.time = get_time()
        self.input = get_input()
        self.event_dispatcher = get_event_dispatcher()
        self.resource_manager = get_resource_manager()
        self.entity_manager = get_entity_manager()
        
        # Window
        self.window = Window(
            width=width,
            height=height,
            title=title,
            fullscreen=fullscreen,
            vsync=self.config.get("window.vsync", True),
            resizable=self.config.get("window.resizable", True)
        )
        
        # State
        self._running = False
        self._initialized = False
        self._update_callback: Optional[Callable[[float], None]] = None
        self._render_callback: Optional[Callable[[], None]] = None
        
        # Setup event handlers
        self._setup_events()
    
    def _setup_events(self):
        """Setup default event handlers."""
        self.event_dispatcher.subscribe(EventType.WINDOW_CLOSE, self._on_window_close)
        self.event_dispatcher.subscribe(EventType.WINDOW_RESIZE, self._on_window_resize)
    
    def _on_window_close(self, event):
        """Handle window close event."""
        self._running = False
    
    def _on_window_resize(self, event):
        """Handle window resize event."""
        data = event.data
        if data:
            self.logger.info(f"Window resized to {data.get('width')}x{data.get('height')}")
    
    def initialize(self) -> bool:
        """
        Initialize engine.
        Returns True if successful.
        """
        if self._initialized:
            self.logger.warning("Engine already initialized")
            return True
        
        self.logger.info("Initializing Core...")
        
        # Create window
        if not self.window.create():
            self.logger.error("Failed to create window")
            return False
        
        # Initialize systems
        self.time.reset()
        self.resource_manager.set_base_path("assets")
        
        self._initialized = True
        self.logger.info("Engine initialized successfully")
        return True
    
    def set_update_callback(self, callback: Callable[[float], None]):
        """Set update callback (called each frame)."""
        self._update_callback = callback
    
    def set_render_callback(self, callback: Callable[[], None]):
        """Set render callback (called each frame)."""
        self._render_callback = callback
    
    def run(self):
        """Run the main game loop."""
        if not self._initialized:
            if not self.initialize():
                self.logger.error("Failed to initialize engine")
                return
        
        self._running = True
        self.logger.info("Starting engine main loop...")
        
        while self._running:
            # Poll events
            self.window.poll_events()
            self.event_dispatcher.process_queue()
            
            # Update time
            self.time.update()
            
            # Update input
            self.input.update()
            
            # Update entities
            self.entity_manager.update(self.time.get_delta_time())
            
            # User update
            if self._update_callback:
                self._update_callback(self.time.get_delta_time())
            
            # User render
            if self._render_callback:
                self._render_callback()
            
            # Swap buffers
            self.window.swap_buffers()
            
            # Check if window should close
            if self.window.should_close():
                self._running = False
        
        self.shutdown()
    
    def shutdown(self):
        """Shutdown engine."""
        if not self._initialized:
            return
        
        self.logger.info("Shutting down engine...")
        
        # Cleanup
        self.entity_manager.clear()
        self.resource_manager.clear()
        self.window.destroy()
        
        self._initialized = False
        self.logger.info("Engine shut down")
    
    def stop(self):
        """Stop the engine (exit main loop)."""
        self._running = False
    
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.time.get_fps()
    
    def get_delta_time(self) -> float:
        """Get delta time."""
        return self.time.get_delta_time()
    
    def __repr__(self):
        return f"Engine(running={self._running}, fps={self.get_fps():.1f})"

