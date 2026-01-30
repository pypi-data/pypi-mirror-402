"""
Lighting system for 3D scenes.
Supports ambient, directional, point, and spot lights.
"""
from typing import Tuple, Optional
from IntPy.vectors import vector3D
import math


class Light:
    """Base light class."""
    
    def __init__(
        self,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 1.0,
        shadows_enabled: bool = False
    ):
        """
        Initialize light.
        
        Args:
            color: Light color (RGB, 0-1 range)
            intensity: Light intensity
            shadows_enabled: Whether this light casts shadows
        """
        self.color = color
        self.intensity = intensity
        self.shadows_enabled = shadows_enabled
    
    def get_type(self) -> str:
        """Get light type (to be overridden)."""
        return "base"
    
    def __repr__(self):
        return f"{self.get_type().title()}Light(color={self.color}, intensity={self.intensity})"


class AmbientLight(Light):
    """Ambient light (global illumination)."""
    
    def __init__(self, color: Tuple[float, float, float] = (1.0, 1.0, 1.0), intensity: float = 0.2):
        super().__init__(color, intensity, False)
    
    def get_type(self) -> str:
        return "ambient"


class DirectionalLight(Light):
    """Directional light (like sunlight)."""
    
    def __init__(
        self,
        direction: vector3D,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 1.0,
        shadows_enabled: bool = False
    ):
        """
        Initialize directional light.
        
        Args:
            direction: Light direction (will be normalized)
        """
        super().__init__(color, intensity, shadows_enabled)
        self.direction = self._normalize(direction)
    
    def set_direction(self, direction: vector3D):
        """Set light direction."""
        self.direction = self._normalize(direction)
    
    def get_type(self) -> str:
        return "directional"
    
    def _normalize(self, v: vector3D) -> vector3D:
        """Normalize a vector."""
        mag = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        if mag < 0.0001:
            return vector3D(0, -1, 0)
        return vector3D(v.x / mag, v.y / mag, v.z / mag)
    
    def __repr__(self):
        return f"DirectionalLight(direction={self.direction}, color={self.color}, intensity={self.intensity})"


class PointLight(Light):
    """Point light (omnidirectional, like a lightbulb)."""
    
    def __init__(
        self,
        position: vector3D,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 1.0,
        range: float = 10.0,
        shadows_enabled: bool = False
    ):
        """
        Initialize point light.
        
        Args:
            position: Light position in world space
            range: Light range (attenuation distance)
        """
        super().__init__(color, intensity, shadows_enabled)
        self.position = position
        self.range = range
        self.constant_attenuation = 1.0
        self.linear_attenuation = 0.7
        self.quadratic_attenuation = 1.8
    
    def set_position(self, position: vector3D):
        """Set light position."""
        self.position = position
    
    def set_range(self, range: float):
        """Set light range."""
        self.range = range
    
    def get_type(self) -> str:
        return "point"
    
    def __repr__(self):
        return f"PointLight(position={self.position}, color={self.color}, intensity={self.intensity}, range={self.range})"


class SpotLight(Light):
    """Spot light (cone-shaped light)."""
    
    def __init__(
        self,
        position: vector3D,
        direction: vector3D,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 1.0,
        inner_cone_angle: float = 30.0,
        outer_cone_angle: float = 45.0,
        range: float = 10.0,
        shadows_enabled: bool = False
    ):
        """
        Initialize spot light.
        
        Args:
            position: Light position
            direction: Light direction (will be normalized)
            inner_cone_angle: Inner cone angle in degrees
            outer_cone_angle: Outer cone angle in degrees
            range: Light range
        """
        super().__init__(color, intensity, shadows_enabled)
        self.position = position
        self.direction = self._normalize(direction)
        self.inner_cone_angle = math.radians(inner_cone_angle)
        self.outer_cone_angle = math.radians(outer_cone_angle)
        self.range = range
    
    def set_position(self, position: vector3D):
        """Set light position."""
        self.position = position
    
    def set_direction(self, direction: vector3D):
        """Set light direction."""
        self.direction = self._normalize(direction)
    
    def set_cone_angles(self, inner: float, outer: float):
        """Set cone angles in degrees."""
        self.inner_cone_angle = math.radians(inner)
        self.outer_cone_angle = math.radians(outer)
    
    def get_type(self) -> str:
        return "spot"
    
    def _normalize(self, v: vector3D) -> vector3D:
        """Normalize a vector."""
        mag = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        if mag < 0.0001:
            return vector3D(0, -1, 0)
        return vector3D(v.x / mag, v.y / mag, v.z / mag)
    
    def __repr__(self):
        return f"SpotLight(position={self.position}, direction={self.direction}, color={self.color})"


class LightManager:
    """Manages all lights in a scene."""
    
    def __init__(self):
        self.ambient_light: Optional[AmbientLight] = None
        self.directional_lights: list = []
        self.point_lights: list = []
        self.spot_lights: list = []
        self.max_directional_lights = 4
        self.max_point_lights = 8
        self.max_spot_lights = 4
    
    def set_ambient(self, light: AmbientLight):
        """Set ambient light."""
        self.ambient_light = light
    
    def add_directional(self, light: DirectionalLight):
        """Add a directional light."""
        if len(self.directional_lights) < self.max_directional_lights:
            self.directional_lights.append(light)
    
    def add_point(self, light: PointLight):
        """Add a point light."""
        if len(self.point_lights) < self.max_point_lights:
            self.point_lights.append(light)
    
    def add_spot(self, light: SpotLight):
        """Add a spot light."""
        if len(self.spot_lights) < self.max_spot_lights:
            self.spot_lights.append(light)
    
    def remove_directional(self, light: DirectionalLight):
        """Remove a directional light."""
        if light in self.directional_lights:
            self.directional_lights.remove(light)
    
    def remove_point(self, light: PointLight):
        """Remove a point light."""
        if light in self.point_lights:
            self.point_lights.remove(light)
    
    def remove_spot(self, light: SpotLight):
        """Remove a spot light."""
        if light in self.spot_lights:
            self.spot_lights.remove(light)
    
    def clear(self):
        """Clear all lights."""
        self.ambient_light = None
        self.directional_lights.clear()
        self.point_lights.clear()
        self.spot_lights.clear()
    
    def get_all_lights(self) -> list:
        """Get all lights as a flat list."""
        lights = []
        if self.ambient_light:
            lights.append(self.ambient_light)
        lights.extend(self.directional_lights)
        lights.extend(self.point_lights)
        lights.extend(self.spot_lights)
        return lights
    
    def __repr__(self):
        return f"LightManager(ambient=1, directional={len(self.directional_lights)}, point={len(self.point_lights)}, spot={len(self.spot_lights)})"

