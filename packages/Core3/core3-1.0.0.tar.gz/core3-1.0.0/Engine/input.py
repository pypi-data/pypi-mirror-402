"""
Input system for keyboard and mouse input.
"""
from typing import Dict, Set, Callable, Optional
from enum import Enum


class Key(Enum):
    """Keyboard key codes."""
    # Letters
    A = 'a'
    B = 'b'
    C = 'c'
    D = 'd'
    E = 'e'
    F = 'f'
    G = 'g'
    H = 'h'
    I = 'i'
    J = 'j'
    K = 'k'
    L = 'l'
    M = 'm'
    N = 'n'
    O = 'o'
    P = 'p'
    Q = 'q'
    R = 'r'
    S = 's'
    T = 't'
    U = 'u'
    V = 'v'
    W = 'w'
    X = 'x'
    Y = 'y'
    Z = 'z'
    
    # Numbers
    KEY_0 = '0'
    KEY_1 = '1'
    KEY_2 = '2'
    KEY_3 = '3'
    KEY_4 = '4'
    KEY_5 = '5'
    KEY_6 = '6'
    KEY_7 = '7'
    KEY_8 = '8'
    KEY_9 = '9'
    
    # Special keys
    SPACE = 'space'
    ENTER = 'enter'
    ESCAPE = 'escape'
    TAB = 'tab'
    BACKSPACE = 'backspace'
    DELETE = 'delete'
    SHIFT = 'shift'
    CTRL = 'ctrl'
    ALT = 'alt'
    SUPER = 'super'  # Windows/Command key
    
    # Arrow keys
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    
    # Function keys
    F1 = 'f1'
    F2 = 'f2'
    F3 = 'f3'
    F4 = 'f4'
    F5 = 'f5'
    F6 = 'f6'
    F7 = 'f7'
    F8 = 'f8'
    F9 = 'f9'
    F10 = 'f10'
    F11 = 'f11'
    F12 = 'f12'


class MouseButton(Enum):
    """Mouse button codes."""
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2
    BUTTON_4 = 3
    BUTTON_5 = 4


class Input:
    """Input manager for keyboard and mouse."""
    
    def __init__(self):
        """Initialize input manager."""
        self._keys_pressed: Set[Key] = set()
        self._keys_down: Set[Key] = set()
        self._keys_up: Set[Key] = set()
        
        self._mouse_buttons_pressed: Set[MouseButton] = set()
        self._mouse_buttons_down: Set[MouseButton] = set()
        self._mouse_buttons_up: Set[MouseButton] = set()
        
        self._mouse_position = (0.0, 0.0)
        self._mouse_delta = (0.0, 0.0)
        self._mouse_scroll = (0.0, 0.0)
        
        self._key_callbacks: Dict[Key, list] = {}
        self._mouse_callbacks: Dict[MouseButton, list] = {}
    
    def update(self):
        """Update input state (call at end of frame)."""
        self._keys_down.clear()
        self._keys_up.clear()
        self._mouse_buttons_down.clear()
        self._mouse_buttons_up.clear()
        self._mouse_delta = (0.0, 0.0)
        self._mouse_scroll = (0.0, 0.0)
    
    # Keyboard
    def is_key_pressed(self, key: Key) -> bool:
        """Check if key is currently pressed."""
        return key in self._keys_pressed
    
    def is_key_down(self, key: Key) -> bool:
        """Check if key was pressed this frame."""
        return key in self._keys_down
    
    def is_key_up(self, key: Key) -> bool:
        """Check if key was released this frame."""
        return key in self._keys_up
    
    def set_key_pressed(self, key: Key, pressed: bool):
        """Set key pressed state (internal use)."""
        if pressed:
            if key not in self._keys_pressed:
                self._keys_down.add(key)
            self._keys_pressed.add(key)
        else:
            if key in self._keys_pressed:
                self._keys_up.add(key)
            self._keys_pressed.discard(key)
    
    def on_key_press(self, key: Key, callback: Callable):
        """Register callback for key press."""
        if key not in self._key_callbacks:
            self._key_callbacks[key] = []
        self._key_callbacks[key].append(callback)
    
    def trigger_key_callbacks(self, key: Key):
        """Trigger callbacks for key (internal use)."""
        if key in self._key_callbacks:
            for callback in self._key_callbacks[key]:
                callback()
    
    # Mouse
    def is_mouse_button_pressed(self, button: MouseButton) -> bool:
        """Check if mouse button is currently pressed."""
        return button in self._mouse_buttons_pressed
    
    def is_mouse_button_down(self, button: MouseButton) -> bool:
        """Check if mouse button was pressed this frame."""
        return button in self._mouse_buttons_down
    
    def is_mouse_button_up(self, button: MouseButton) -> bool:
        """Check if mouse button was released this frame."""
        return button in self._mouse_buttons_up
    
    def set_mouse_button_pressed(self, button: MouseButton, pressed: bool):
        """Set mouse button pressed state (internal use)."""
        if pressed:
            if button not in self._mouse_buttons_pressed:
                self._mouse_buttons_down.add(button)
            self._mouse_buttons_pressed.add(button)
        else:
            if button in self._mouse_buttons_pressed:
                self._mouse_buttons_up.add(button)
            self._mouse_buttons_pressed.discard(button)
    
    def get_mouse_position(self) -> tuple:
        """Get mouse position (x, y)."""
        return self._mouse_position
    
    def set_mouse_position(self, x: float, y: float):
        """Set mouse position (internal use)."""
        old_pos = self._mouse_position
        self._mouse_position = (x, y)
        self._mouse_delta = (x - old_pos[0], y - old_pos[1])
    
    def get_mouse_delta(self) -> tuple:
        """Get mouse movement delta (dx, dy)."""
        return self._mouse_delta
    
    def get_mouse_scroll(self) -> tuple:
        """Get mouse scroll delta (x, y)."""
        return self._mouse_scroll
    
    def set_mouse_scroll(self, x: float, y: float):
        """Set mouse scroll (internal use)."""
        self._mouse_scroll = (x, y)
    
    def on_mouse_press(self, button: MouseButton, callback: Callable):
        """Register callback for mouse button press."""
        if button not in self._mouse_callbacks:
            self._mouse_callbacks[button] = []
        self._mouse_callbacks[button].append(callback)
    
    def trigger_mouse_callbacks(self, button: MouseButton):
        """Trigger callbacks for mouse button (internal use)."""
        if button in self._mouse_callbacks:
            for callback in self._mouse_callbacks[button]:
                callback()
    
    # Utility
    def get_any_key_pressed(self) -> Optional[Key]:
        """Get any currently pressed key (or None)."""
        return next(iter(self._keys_pressed)) if self._keys_pressed else None
    
    def get_any_mouse_button_pressed(self) -> Optional[MouseButton]:
        """Get any currently pressed mouse button (or None)."""
        return next(iter(self._mouse_buttons_pressed)) if self._mouse_buttons_pressed else None


# Global input instance
_input_instance: Optional[Input] = None


def get_input() -> Input:
    """Get global input instance."""
    global _input_instance
    if _input_instance is None:
        _input_instance = Input()
    return _input_instance

