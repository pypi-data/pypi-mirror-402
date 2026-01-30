"""
Powerful render pipeline system for Core.

This package provides a comprehensive 3D rendering system including:
- Camera system with perspective and orthographic projections
- Transform system for positioning and orienting objects
- Geometry and mesh system with primitives
- Material and shader system
- Lighting system (ambient, directional, point, spot)
- Scene management
- Main render pipeline orchestrator
"""

# Core components
from .camera import Camera
from .transform import Transform
from .geometry import Vertex, Mesh, PrimitiveFactory
from .material import Material, MaterialLibrary, ShaderProgram
from .light import (
    Light, AmbientLight, DirectionalLight, PointLight, SpotLight, LightManager
)
from .scene import Scene, GameObject, SceneManager
from .render_pipeline import (
    RenderPipeline, RenderStats, RenderContext
)

__all__ = [
    # Camera
    'Camera',
    
    # Transform
    'Transform',
    
    # Geometry
    'Vertex',
    'Mesh',
    'PrimitiveFactory',
    
    # Material
    'Material',
    'MaterialLibrary',
    'ShaderProgram',
    
    # Lighting
    'Light',
    'AmbientLight',
    'DirectionalLight',
    'PointLight',
    'SpotLight',
    'LightManager',
    
    # Scene
    'Scene',
    'GameObject',
    'SceneManager',
    
    # Render Pipeline
    'RenderPipeline',
    'RenderStats',
    'RenderContext',
]

__version__ = '1.0.0'

