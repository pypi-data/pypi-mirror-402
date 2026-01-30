"""
Main render pipeline orchestrator.
Handles rendering, culling, batching, and rendering state management.
"""
from typing import List, Optional, Dict, Any, Tuple
from IntPy.vectors import vector3D
from .scene import Scene, GameObject
from .camera import Camera
from .geometry import Mesh
from .material import Material
from .light import LightManager
import math


class RenderStats:
    """Statistics about the current frame."""
    
    def __init__(self):
        self.draw_calls = 0
        self.triangles_rendered = 0
        self.objects_culled = 0
        self.objects_rendered = 0
        self.lights_processed = 0
    
    def reset(self):
        """Reset stats for new frame."""
        self.draw_calls = 0
        self.triangles_rendered = 0
        self.objects_culled = 0
        self.objects_rendered = 0
        self.lights_processed = 0
    
    def __repr__(self):
        return (f"RenderStats(draw_calls={self.draw_calls}, triangles={self.triangles_rendered}, "
                f"culled={self.objects_culled}, rendered={self.objects_rendered})")


class RenderPipeline:
    """Main render pipeline orchestrator."""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """
        Initialize render pipeline.
        
        Args:
            width: Render target width
            height: Render target height
        """
        self.width = width
        self.height = height
        self.stats = RenderStats()
        
        # Rendering state
        self.culling_enabled = True
        self.frustum_culling = True
        self.occlusion_culling = False
        self.batching_enabled = True
        self.sort_transparent = True
        
        # Render queues
        self.opaque_queue: List[GameObject] = []
        self.transparent_queue: List[GameObject] = []
        
        # Viewport
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_width = width
        self.viewport_height = height
    
    def render_scene(self, scene: Scene, camera: Optional[Camera] = None):
        """
        Render a scene.
        
        Args:
            scene: Scene to render
            camera: Camera to render from (uses scene's main camera if None)
        """
        # Reset stats
        self.stats.reset()
        
        # Get camera
        render_camera = camera if camera else scene.get_main_camera()
        if not render_camera:
            return
        
        # Update camera aspect ratio
        render_camera.set_aspect_ratio(self.width / self.height)
        
        # Clear render queues
        self.opaque_queue.clear()
        self.transparent_queue.clear()
        
        # Get active objects
        objects = scene.get_active_objects()
        
        # Cull and sort objects
        for obj in objects:
            if not obj.mesh or not obj.material:
                continue
            
            # Frustum culling
            if self.culling_enabled and self.frustum_culling:
                if not self._is_in_frustum(obj, render_camera):
                    self.stats.objects_culled += 1
                    continue
            
            # Sort by render queue
            if obj.material.blend_mode == "opaque":
                self.opaque_queue.append(obj)
            else:
                self.transparent_queue.append(obj)
        
        # Sort transparent objects back-to-front
        if self.sort_transparent and self.transparent_queue:
            camera_pos = render_camera.position
            self.transparent_queue.sort(
                key=lambda o: self._distance_squared(o.transform.position, camera_pos),
                reverse=True
            )
        
        # Render opaque objects
        for obj in self.opaque_queue:
            self._render_object(obj, render_camera, scene.light_manager)
            self.stats.objects_rendered += 1
        
        # Render transparent objects
        for obj in self.transparent_queue:
            self._render_object(obj, render_camera, scene.light_manager)
            self.stats.objects_rendered += 1
    
    def _render_object(self, obj: GameObject, camera: Camera, light_manager: LightManager):
        """Render a single game object."""
        if not obj.mesh or not obj.material:
            return
        
        # Get transformation matrices
        model_matrix = obj.transform.get_matrix()
        view_matrix = camera.get_view_matrix()
        projection_matrix = camera.get_projection_matrix()
        
        # Calculate MVP matrix (Model-View-Projection)
        mvp_matrix = self._multiply_matrices(
            self._multiply_matrices(model_matrix, view_matrix),
            projection_matrix
        )
        
        # Here you would:
        # 1. Set shader uniforms (MVP, material properties, lights)
        # 2. Bind textures
        # 3. Set render state (culling, blending)
        # 4. Draw mesh (vertices + indices)
        
        # For now, we'll just count the draw call and triangles
        self.stats.draw_calls += 1
        if obj.mesh.indices:
            self.stats.triangles_rendered += len(obj.mesh.indices) // 3
        else:
            self.stats.triangles_rendered += len(obj.mesh.vertices) // 3
    
    def _is_in_frustum(self, obj: GameObject, camera: Camera) -> bool:
        """
        Check if object is in camera frustum.
        Simplified version - production would use proper frustum planes.
        """
        # Get object bounds
        if not obj.mesh:
            return False
        
        bounds_min, bounds_max = obj.mesh.get_bounds()
        if bounds_min is None or bounds_max is None:
            return True  # No bounds, render anyway
        
        # Transform bounds to world space (simplified)
        world_min = bounds_min + obj.transform.position
        world_max = bounds_max + obj.transform.position
        
        # Simple distance check (production would use proper frustum culling)
        obj_center = vector3D(
            (world_min.x + world_max.x) / 2,
            (world_min.y + world_max.y) / 2,
            (world_min.z + world_max.z) / 2
        )
        
        # Check if object is too far
        distance = self._distance(camera.position, obj_center)
        if distance > camera.far_plane * 1.5:  # Small margin
            return False
        
        # For a full implementation, would check against all 6 frustum planes
        return True
    
    def _distance_squared(self, a: vector3D, b: vector3D) -> float:
        """Squared distance between two points."""
        dx = a.x - b.x
        dy = a.y - b.y
        dz = a.z - b.z
        return dx * dx + dy * dy + dz * dz
    
    def _distance(self, a: vector3D, b: vector3D) -> float:
        """Distance between two points."""
        return math.sqrt(self._distance_squared(a, b))
    
    def _multiply_matrices(self, a: list, b: list) -> list:
        """Multiply two 4x4 matrices."""
        result = [0] * 16
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    result[i * 4 + j] += a[i * 4 + k] * b[k * 4 + j]
        return result
    
    def set_viewport(self, x: int, y: int, width: int, height: int):
        """Set viewport dimensions."""
        self.viewport_x = x
        self.viewport_y = y
        self.viewport_width = width
        self.viewport_height = height
    
    def set_render_target_size(self, width: int, height: int):
        """Set render target size."""
        self.width = width
        self.height = height
        self.viewport_width = width
        self.viewport_height = height
    
    def enable_culling(self, enabled: bool = True):
        """Enable or disable culling."""
        self.culling_enabled = enabled
    
    def enable_frustum_culling(self, enabled: bool = True):
        """Enable or disable frustum culling."""
        self.frustum_culling = enabled
    
    def enable_batching(self, enabled: bool = True):
        """Enable or disable batching."""
        self.batching_enabled = enabled
    
    def get_stats(self) -> RenderStats:
        """Get render statistics."""
        return self.stats
    
    def __repr__(self):
        return f"RenderPipeline({self.width}x{self.height}, culling={self.culling_enabled})"


class RenderContext:
    """Render context for managing graphics API state (placeholder for actual implementation)."""
    
    def __init__(self):
        self.current_shader = None
        self.current_texture = None
        self.current_material = None
        self.cull_face = "back"
        self.blend_enabled = False
    
    def set_shader(self, shader):
        """Set current shader."""
        self.current_shader = shader
    
    def set_texture(self, texture, slot: int = 0):
        """Set current texture."""
        self.current_texture = texture
    
    def set_material(self, material: Material):
        """Set render state based on material."""
        self.current_material = material
        self.cull_face = material.culling
        self.blend_enabled = material.blend_mode != "opaque"
    
    def clear(self):
        """Clear render state."""
        self.current_shader = None
        self.current_texture = None
        self.current_material = None
    
    def __repr__(self):
        return f"RenderContext(shader={self.current_shader}, texture={self.current_texture})"

