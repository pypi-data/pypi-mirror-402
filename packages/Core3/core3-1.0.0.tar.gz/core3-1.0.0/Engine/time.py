"""
Time and clock system for managing delta time, frame rate, and timing.
"""
import time
from typing import Optional


class Clock:
    """High-precision clock for timing."""
    
    def __init__(self):
        """Initialize clock."""
        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.paused_time = 0.0
        self.pause_start_time: Optional[float] = None
    
    def reset(self):
        """Reset clock."""
        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.paused_time = 0.0
        self.pause_start_time = None
    
    def elapsed_time(self) -> float:
        """Get elapsed time since clock start (in seconds)."""
        if self.pause_start_time is not None:
            return self.pause_start_time - self.start_time - self.paused_time
        return time.perf_counter() - self.start_time - self.paused_time
    
    def pause(self):
        """Pause the clock."""
        if self.pause_start_time is None:
            self.pause_start_time = time.perf_counter()
    
    def resume(self):
        """Resume the clock."""
        if self.pause_start_time is not None:
            self.paused_time += time.perf_counter() - self.pause_start_time
            self.pause_start_time = None
    
    def is_paused(self) -> bool:
        """Check if clock is paused."""
        return self.pause_start_time is not None


class Time:
    """Global time manager for the engine."""
    
    def __init__(self):
        """Initialize time manager."""
        self.clock = Clock()
        self.delta_time = 0.0
        self.fixed_delta_time = 1.0 / 60.0  # 60 FPS default
        self.time_scale = 1.0
        self.frame_count = 0
        self.fps = 0.0
        self.smooth_fps = 0.0
        
        # FPS calculation
        self.fps_update_interval = 1.0
        self.fps_last_update = 0.0
        self.fps_frame_count = 0
        self.fps_accumulator = 0.0
    
    def update(self):
        """Update time (called each frame)."""
        current_time = self.clock.elapsed_time()
        self.delta_time = (current_time - self.clock.last_time) * self.time_scale
        self.clock.last_time = current_time
        
        self.frame_count += 1
        self.fps_frame_count += 1
        self.fps_accumulator += self.delta_time
        
        # Update FPS
        if self.fps_accumulator >= self.fps_update_interval:
            self.fps = self.fps_frame_count / self.fps_accumulator
            self.smooth_fps = self.smooth_fps * 0.9 + self.fps * 0.1  # Smoothing
            self.fps_frame_count = 0
            self.fps_accumulator = 0.0
    
    def get_delta_time(self) -> float:
        """Get delta time (time since last frame)."""
        return self.delta_time
    
    def get_fixed_delta_time(self) -> float:
        """Get fixed delta time (for physics)."""
        return self.fixed_delta_time
    
    def get_time(self) -> float:
        """Get total elapsed time."""
        return self.clock.elapsed_time()
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
    
    def get_smooth_fps(self) -> float:
        """Get smoothed FPS."""
        return self.smooth_fps
    
    def set_time_scale(self, scale: float):
        """Set time scale (1.0 = normal, 2.0 = double speed, 0.5 = half speed)."""
        self.time_scale = max(0.0, scale)
    
    def set_fixed_delta_time(self, dt: float):
        """Set fixed delta time."""
        self.fixed_delta_time = max(0.001, dt)
    
    def pause(self):
        """Pause time."""
        self.clock.pause()
    
    def resume(self):
        """Resume time."""
        self.clock.resume()
    
    def is_paused(self) -> bool:
        """Check if time is paused."""
        return self.clock.is_paused()
    
    def reset(self):
        """Reset time."""
        self.clock.reset()
        self.delta_time = 0.0
        self.frame_count = 0
        self.fps = 0.0
        self.smooth_fps = 0.0


# Global time instance
_time_instance: Optional[Time] = None


def get_time() -> Time:
    """Get global time instance."""
    global _time_instance
    if _time_instance is None:
        _time_instance = Time()
    return _time_instance

