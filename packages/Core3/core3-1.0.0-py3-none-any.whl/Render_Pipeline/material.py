"""
Material and shader system for rendering properties.
Supports various material types, textures, and rendering modes.
"""
from typing import Tuple, Optional, Dict, Any
from IntPy.vectors import vector3D


class Material:
    """Material defining surface properties for rendering."""
    
    def __init__(
        self,
        name: str = "Material",
        albedo: Tuple[float, float, float] = (0.8, 0.8, 0.8),
        metallic: float = 0.0,
        roughness: float = 0.5,
        emissive: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        alpha: float = 1.0,
        culling: str = "back",  # "back", "front", "none"
        blend_mode: str = "opaque"  # "opaque", "transparent", "additive"
    ):
        """
        Initialize material.
        
        Args:
            name: Material name
            albedo: Base color (RGB, 0-1 range)
            metallic: Metallic value (0-1)
            roughness: Roughness value (0-1)
            emissive: Emissive color (RGB, 0-1 range)
            alpha: Transparency (0-1)
            culling: Face culling mode
            blend_mode: Blending mode
        """
        self.name = name
        self.albedo = albedo
        self.metallic = metallic
        self.roughness = roughness
        self.emissive = emissive
        self.alpha = alpha
        self.culling = culling
        self.blend_mode = blend_mode
        
        # Texture references (can be file paths or texture IDs)
        self.albedo_texture: Optional[str] = None
        self.normal_texture: Optional[str] = None
        self.metallic_roughness_texture: Optional[str] = None
        self.emissive_texture: Optional[str] = None
        
        # Additional properties
        self.properties: Dict[str, Any] = {}
    
    def set_albedo(self, r: float, g: float, b: float):
        """Set albedo color."""
        self.albedo = (r, g, b)
    
    def set_metallic_roughness(self, metallic: float, roughness: float):
        """Set metallic and roughness values."""
        self.metallic = max(0.0, min(1.0, metallic))
        self.roughness = max(0.0, min(1.0, roughness))
    
    def set_texture(self, texture_type: str, texture_path: str):
        """Set a texture for the material."""
        if texture_type == "albedo":
            self.albedo_texture = texture_path
        elif texture_type == "normal":
            self.normal_texture = texture_path
        elif texture_type == "metallic_roughness":
            self.metallic_roughness_texture = texture_path
        elif texture_type == "emissive":
            self.emissive_texture = texture_path
    
    def copy(self) -> 'Material':
        """Create a copy of this material."""
        mat = Material(
            name=self.name,
            albedo=self.albedo,
            metallic=self.metallic,
            roughness=self.roughness,
            emissive=self.emissive,
            alpha=self.alpha,
            culling=self.culling,
            blend_mode=self.blend_mode
        )
        mat.albedo_texture = self.albedo_texture
        mat.normal_texture = self.normal_texture
        mat.metallic_roughness_texture = self.metallic_roughness_texture
        mat.emissive_texture = self.emissive_texture
        mat.properties = self.properties.copy()
        return mat
    
    def __repr__(self):
        return f"Material(name={self.name}, albedo={self.albedo})"


class MaterialLibrary:
    """Library of predefined materials."""
    
    @staticmethod
    def default() -> Material:
        """Default gray material."""
        return Material(name="Default", albedo=(0.8, 0.8, 0.8))
    
    @staticmethod
    def metallic_rough(metallic: float = 0.5, roughness: float = 0.5) -> Material:
        """Create a metallic material."""
        mat = Material(name="Metallic")
        mat.set_metallic_roughness(metallic, roughness)
        return mat
    
    @staticmethod
    def emissive(color: Tuple[float, float, float], intensity: float = 1.0) -> Material:
        """Create an emissive material."""
        mat = Material(name="Emissive")
        mat.emissive = tuple(c * intensity for c in color)
        return mat
    
    @staticmethod
    def plastic(color: Tuple[float, float, float]) -> Material:
        """Create a plastic material (non-metallic, smooth)."""
        mat = Material(name="Plastic", albedo=color)
        mat.set_metallic_roughness(0.0, 0.1)
        return mat
    
    @staticmethod
    def metal(color: Tuple[float, float, float]) -> Material:
        """Create a metal material."""
        mat = Material(name="Metal", albedo=color)
        mat.set_metallic_roughness(1.0, 0.2)
        return mat
    
    @staticmethod
    def glass(alpha: float = 0.5) -> Material:
        """Create a glass material."""
        mat = Material(
            name="Glass",
            albedo=(0.9, 0.9, 0.95),
            alpha=alpha,
            blend_mode="transparent"
        )
        mat.set_metallic_roughness(0.0, 0.0)
        return mat


class ShaderProgram:
    """Shader program abstraction (for future implementation with actual shaders)."""
    
    def __init__(self, name: str, shader_type: str = "pbr"):
        """
        Initialize shader program.
        
        Args:
            name: Shader name
            shader_type: Shader type ("pbr", "unlit", "wireframe", etc.)
        """
        self.name = name
        self.shader_type = shader_type
        self.uniforms: Dict[str, Any] = {}
    
    def set_uniform(self, name: str, value: Any):
        """Set a shader uniform value."""
        self.uniforms[name] = value
    
    def get_uniform(self, name: str, default: Any = None) -> Any:
        """Get a shader uniform value."""
        return self.uniforms.get(name, default)
    
    def __repr__(self):
        return f"ShaderProgram(name={self.name}, type={self.shader_type})"

