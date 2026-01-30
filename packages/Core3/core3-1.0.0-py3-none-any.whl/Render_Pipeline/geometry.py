"""
Geometry and mesh system for 3D objects.
Supports vertex buffers, indices, normals, UVs, and various primitive shapes.
"""
from typing import List, Tuple, Optional
from IntPy.vectors import vector3D
import math


class Vertex:
    """Single vertex with position, normal, and UV coordinates."""
    
    def __init__(
        self,
        position: vector3D,
        normal: vector3D = None,
        uv: Tuple[float, float] = (0.0, 0.0),
        color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    ):
        self.position = position
        self.normal = normal if normal else vector3D(0, 1, 0)
        self.uv = uv
        self.color = color
    
    def __repr__(self):
        return f"Vertex(pos={self.position}, norm={self.normal}, uv={self.uv})"


class Mesh:
    """3D mesh containing vertices and indices."""
    
    def __init__(self, name: str = "Mesh"):
        """
        Initialize mesh.
        
        Args:
            name: Name of the mesh
        """
        self.name = name
        self.vertices: List[Vertex] = []
        self.indices: List[int] = []
        self.bounds_min: Optional[vector3D] = None
        self.bounds_max: Optional[vector3D] = None
    
    def add_vertex(self, vertex: Vertex):
        """Add a vertex to the mesh."""
        self.vertices.append(vertex)
        self._update_bounds(vertex.position)
    
    def add_triangle(self, v0: Vertex, v1: Vertex, v2: Vertex):
        """Add a triangle (three vertices)."""
        start_idx = len(self.vertices)
        self.add_vertex(v0)
        self.add_vertex(v1)
        self.add_vertex(v2)
        self.indices.extend([start_idx, start_idx + 1, start_idx + 2])
    
    def calculate_normals(self):
        """Calculate vertex normals from face normals."""
        # Reset normals
        for vertex in self.vertices:
            vertex.normal = vector3D(0, 0, 0)
        
        # Accumulate face normals
        for i in range(0, len(self.indices), 3):
            i0, i1, i2 = self.indices[i], self.indices[i + 1], self.indices[i + 2]
            v0 = self.vertices[i0].position
            v1 = self.vertices[i1].position
            v2 = self.vertices[i2].position
            
            # Face normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = self._cross(edge1, edge2)
            
            # Normalize and accumulate
            mag = math.sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z)
            if mag > 0.0001:
                normal = vector3D(normal.x / mag, normal.y / mag, normal.z / mag)
                self.vertices[i0].normal = self.vertices[i0].normal + normal
                self.vertices[i1].normal = self.vertices[i1].normal + normal
                self.vertices[i2].normal = self.vertices[i2].normal + normal
        
        # Normalize all accumulated normals
        for vertex in self.vertices:
            mag = math.sqrt(
                vertex.normal.x * vertex.normal.x +
                vertex.normal.y * vertex.normal.y +
                vertex.normal.z * vertex.normal.z
            )
            if mag > 0.0001:
                vertex.normal = vector3D(
                    vertex.normal.x / mag,
                    vertex.normal.y / mag,
                    vertex.normal.z / mag
                )
    
    def get_bounds(self) -> Tuple[vector3D, vector3D]:
        """Get bounding box (min, max)."""
        if self.bounds_min is None or self.bounds_max is None:
            return (vector3D(0, 0, 0), vector3D(0, 0, 0))
        return (self.bounds_min, self.bounds_max)
    
    def _update_bounds(self, position: vector3D):
        """Update bounding box."""
        if self.bounds_min is None:
            self.bounds_min = vector3D(position.x, position.y, position.z)
            self.bounds_max = vector3D(position.x, position.y, position.z)
        else:
            self.bounds_min = vector3D(
                min(self.bounds_min.x, position.x),
                min(self.bounds_min.y, position.y),
                min(self.bounds_min.z, position.z)
            )
            self.bounds_max = vector3D(
                max(self.bounds_max.x, position.x),
                max(self.bounds_max.y, position.y),
                max(self.bounds_max.z, position.z)
            )
    
    def _cross(self, a: vector3D, b: vector3D) -> vector3D:
        """Cross product."""
        return vector3D(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )
    
    def __repr__(self):
        return f"Mesh(name={self.name}, vertices={len(self.vertices)}, triangles={len(self.indices) // 3})"


class PrimitiveFactory:
    """Factory for creating primitive mesh shapes."""
    
    @staticmethod
    def create_cube(size: float = 1.0) -> Mesh:
        """Create a cube mesh."""
        mesh = Mesh("Cube")
        s = size / 2.0
        
        # Define 8 vertices
        vertices = [
            Vertex(vector3D(-s, -s, -s)),  # 0
            Vertex(vector3D(s, -s, -s)),   # 1
            Vertex(vector3D(s, s, -s)),    # 2
            Vertex(vector3D(-s, s, -s)),   # 3
            Vertex(vector3D(-s, -s, s)),   # 4
            Vertex(vector3D(s, -s, s)),    # 5
            Vertex(vector3D(s, s, s)),     # 6
            Vertex(vector3D(-s, s, s)),    # 7
        ]
        
        # Define 12 triangles (2 per face)
        faces = [
            # Front
            (0, 1, 2), (0, 2, 3),
            # Back
            (5, 4, 7), (5, 7, 6),
            # Top
            (3, 2, 6), (3, 6, 7),
            # Bottom
            (4, 5, 1), (4, 1, 0),
            # Right
            (1, 5, 6), (1, 6, 2),
            # Left
            (4, 0, 3), (4, 3, 7),
        ]
        
        for face in faces:
            mesh.add_triangle(vertices[face[0]], vertices[face[1]], vertices[face[2]])
        
        mesh.calculate_normals()
        return mesh
    
    @staticmethod
    def create_sphere(radius: float = 1.0, segments: int = 32) -> Mesh:
        """Create a sphere mesh."""
        mesh = Mesh("Sphere")
        vertices = []
        
        # Generate vertices
        for y in range(segments + 1):
            theta = math.pi * y / segments
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            
            for x in range(segments + 1):
                phi = 2 * math.pi * x / segments
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)
                
                pos = vector3D(
                    radius * sin_theta * cos_phi,
                    radius * cos_theta,
                    radius * sin_theta * sin_phi
                )
                normal = vector3D(
                    sin_theta * cos_phi,
                    cos_theta,
                    sin_theta * sin_phi
                )
                uv = (x / segments, y / segments)
                
                vertices.append(Vertex(pos, normal, uv))
        
        # Generate indices
        for y in range(segments):
            for x in range(segments):
                i0 = y * (segments + 1) + x
                i1 = i0 + 1
                i2 = (y + 1) * (segments + 1) + x
                i3 = i2 + 1
                
                mesh.indices.extend([i0, i2, i1])
                mesh.indices.extend([i1, i2, i3])
        
        mesh.vertices = vertices
        return mesh
    
    @staticmethod
    def create_plane(width: float = 1.0, height: float = 1.0, segments_x: int = 1, segments_y: int = 1) -> Mesh:
        """Create a plane mesh."""
        mesh = Mesh("Plane")
        
        w2 = width / 2.0
        h2 = height / 2.0
        
        vertices = []
        for y in range(segments_y + 1):
            for x in range(segments_x + 1):
                px = -w2 + (width * x / segments_x)
                pz = -h2 + (height * y / segments_y)
                pos = vector3D(px, 0, pz)
                normal = vector3D(0, 1, 0)
                uv = (x / segments_x, y / segments_y)
                vertices.append(Vertex(pos, normal, uv))
        
        for y in range(segments_y):
            for x in range(segments_x):
                i0 = y * (segments_x + 1) + x
                i1 = i0 + 1
                i2 = (y + 1) * (segments_x + 1) + x
                i3 = i2 + 1
                
                mesh.indices.extend([i0, i2, i1])
                mesh.indices.extend([i1, i2, i3])
        
        mesh.vertices = vertices
        return mesh

