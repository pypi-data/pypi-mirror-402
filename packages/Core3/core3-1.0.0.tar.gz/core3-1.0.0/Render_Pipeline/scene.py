"""
Scene management system for organizing 3D objects, lights, and cameras.
"""
from typing import List, Optional, Dict, Any
from IntPy.vectors import vector3D
from .transform import Transform
from .geometry import Mesh
from .material import Material
from .light import LightManager
from .camera import Camera


class GameObject:
    """Represents a game object in the scene with transform, mesh, and material."""
    
    def __init__(
        self,
        name: str = "GameObject",
        mesh: Optional[Mesh] = None,
        material: Optional[Material] = None,
        transform: Optional[Transform] = None
    ):
        """
        Initialize game object.
        
        Args:
            name: Object name
            mesh: Mesh geometry
            material: Material for rendering
            transform: Transform component
        """
        self.name = name
        self.mesh = mesh
        self.material = material
        self.transform = transform if transform else Transform()
        self.active = True
        self.layer = 0
        self.properties: Dict[str, Any] = {}
    
    def set_mesh(self, mesh: Mesh):
        """Set the mesh."""
        self.mesh = mesh
    
    def set_material(self, material: Material):
        """Set the material."""
        self.material = material
    
    def get_bounds(self) -> tuple:
        """Get world-space bounding box."""
        if not self.mesh:
            return (vector3D(0, 0, 0), vector3D(0, 0, 0))
        
        local_min, local_max = self.mesh.get_bounds()
        # Transform bounds (simplified - would need proper transform in production)
        return (local_min, local_max)
    
    def __repr__(self):
        return f"GameObject(name={self.name}, mesh={self.mesh.name if self.mesh else None}, active={self.active})"


class Scene:
    """Main scene class managing all objects, lights, and cameras."""
    
    def __init__(self, name: str = "Scene"):
        """
        Initialize scene.
        
        Args:
            name: Scene name
        """
        self.name = name
        self.game_objects: List[GameObject] = []
        self.light_manager = LightManager()
        self.main_camera: Optional[Camera] = None
        self.background_color = (0.1, 0.1, 0.1, 1.0)
        self.ambient_color = (0.2, 0.2, 0.2)
        self.fog_enabled = False
        self.fog_color = (0.5, 0.5, 0.5)
        self.fog_density = 0.01
        self.fog_start = 0.0
        self.fog_end = 50.0
    
    def add_object(self, game_object: GameObject) -> GameObject:
        """Add a game object to the scene."""
        self.game_objects.append(game_object)
        return game_object
    
    def remove_object(self, game_object: GameObject):
        """Remove a game object from the scene."""
        if game_object in self.game_objects:
            self.game_objects.remove(game_object)
    
    def find_object(self, name: str) -> Optional[GameObject]:
        """Find a game object by name."""
        for obj in self.game_objects:
            if obj.name == name:
                return obj
        return None
    
    def find_objects_by_name(self, name: str) -> List[GameObject]:
        """Find all game objects matching a name."""
        return [obj for obj in self.game_objects if obj.name == name]
    
    def get_active_objects(self) -> List[GameObject]:
        """Get all active game objects."""
        return [obj for obj in self.game_objects if obj.active]
    
    def set_main_camera(self, camera: Camera):
        """Set the main camera."""
        self.main_camera = camera
    
    def get_main_camera(self) -> Optional[Camera]:
        """Get the main camera."""
        return self.main_camera
    
    def clear(self):
        """Clear all objects from the scene."""
        self.game_objects.clear()
        self.light_manager.clear()
        self.main_camera = None
    
    def get_object_count(self) -> int:
        """Get total number of objects."""
        return len(self.game_objects)
    
    def get_active_object_count(self) -> int:
        """Get number of active objects."""
        return len(self.get_active_objects())
    
    def set_background_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set background clear color."""
        self.background_color = (r, g, b, a)
    
    def enable_fog(self, enabled: bool = True):
        """Enable or disable fog."""
        self.fog_enabled = enabled
    
    def set_fog(self, color: tuple, density: float, start: float, end: float):
        """Configure fog parameters."""
        self.fog_color = color
        self.fog_density = density
        self.fog_start = start
        self.fog_end = end
    
    def __repr__(self):
        return f"Scene(name={self.name}, objects={len(self.game_objects)}, camera={self.main_camera is not None})"


class SceneManager:
    """Manager for multiple scenes."""
    
    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.active_scene: Optional[Scene] = None
    
    def create_scene(self, name: str) -> Scene:
        """Create a new scene."""
        scene = Scene(name)
        self.scenes[name] = scene
        if not self.active_scene:
            self.active_scene = scene
        return scene
    
    def get_scene(self, name: str) -> Optional[Scene]:
        """Get a scene by name."""
        return self.scenes.get(name)
    
    def set_active_scene(self, scene: Scene):
        """Set the active scene."""
        if scene in self.scenes.values():
            self.active_scene = scene
    
    def remove_scene(self, name: str):
        """Remove a scene."""
        if name in self.scenes:
            scene = self.scenes[name]
            if self.active_scene == scene:
                self.active_scene = None
            del self.scenes[name]
    
    def get_active_scene(self) -> Optional[Scene]:
        """Get the active scene."""
        return self.active_scene
    
    def __repr__(self):
        return f"SceneManager(scenes={len(self.scenes)}, active={self.active_scene.name if self.active_scene else None})"

