"""
Geometry primitives and utilities for 2D and 3D shapes.
Includes lines, planes, spheres, boxes, rays, and intersection tests.
"""
import math
from typing import Optional, Tuple, List
from .vectors import vector2D, vector3D


class Ray2D:
    """2D ray (origin + direction)."""
    
    def __init__(self, origin: vector2D, direction: vector2D):
        """
        Initialize ray.
        
        Args:
            origin: Ray origin point
            direction: Ray direction (will be normalized)
        """
        self.origin = origin
        self.direction = direction.normalize()
    
    def point_at(self, t: float) -> vector2D:
        """Get point along ray at parameter t."""
        return self.origin + self.direction * t
    
    def distance_to_point(self, point: vector2D) -> float:
        """Distance from ray to point."""
        to_point = point - self.origin
        projection_length = to_point.dot(self.direction)
        closest_point = self.origin + self.direction * projection_length
        return point.distance_to(closest_point)
    
    def __repr__(self) -> str:
        return f"Ray2D(origin={self.origin}, direction={self.direction})"


class Ray3D:
    """3D ray (origin + direction)."""
    
    def __init__(self, origin: vector3D, direction: vector3D):
        """
        Initialize ray.
        
        Args:
            origin: Ray origin point
            direction: Ray direction (will be normalized)
        """
        self.origin = origin
        self.direction = direction.normalize()
    
    def point_at(self, t: float) -> vector3D:
        """Get point along ray at parameter t."""
        return self.origin + self.direction * t
    
    def distance_to_point(self, point: vector3D) -> float:
        """Distance from ray to point."""
        to_point = point - self.origin
        projection_length = to_point.dot(self.direction)
        closest_point = self.origin + self.direction * projection_length
        return point.distance_to(closest_point)
    
    def __repr__(self) -> str:
        return f"Ray3D(origin={self.origin}, direction={self.direction})"


class Line2D:
    """2D line segment."""
    
    def __init__(self, start: vector2D, end: vector2D):
        """Initialize line segment."""
        self.start = start
        self.end = end
    
    def length(self) -> float:
        """Line length."""
        return self.start.distance_to(self.end)
    
    def direction(self) -> vector2D:
        """Direction vector (normalized)."""
        return (self.end - self.start).normalize()
    
    def midpoint(self) -> vector2D:
        """Midpoint of line."""
        return (self.start + self.end) * 0.5
    
    def point_at(self, t: float) -> vector2D:
        """Point along line at parameter t (0-1)."""
        return self.start.lerp(self.end, t)
    
    def distance_to_point(self, point: vector2D) -> float:
        """Distance from line to point."""
        line_vec = self.end - self.start
        point_vec = point - self.start
        
        line_len_sq = line_vec.magnitude_squared()
        if line_len_sq < 1e-9:
            return point.distance_to(self.start)
        
        t = max(0.0, min(1.0, point_vec.dot(line_vec) / line_len_sq))
        closest = self.start + line_vec * t
        return point.distance_to(closest)
    
    def __repr__(self) -> str:
        return f"Line2D(start={self.start}, end={self.end})"


class Line3D:
    """3D line segment."""
    
    def __init__(self, start: vector3D, end: vector3D):
        """Initialize line segment."""
        self.start = start
        self.end = end
    
    def length(self) -> float:
        """Line length."""
        return self.start.distance_to(self.end)
    
    def direction(self) -> vector3D:
        """Direction vector (normalized)."""
        return (self.end - self.start).normalize()
    
    def midpoint(self) -> vector3D:
        """Midpoint of line."""
        return (self.start + self.end) * 0.5
    
    def point_at(self, t: float) -> vector3D:
        """Point along line at parameter t (0-1)."""
        return self.start.lerp(self.end, t)
    
    def distance_to_point(self, point: vector3D) -> float:
        """Distance from line to point."""
        line_vec = self.end - self.start
        point_vec = point - self.start
        
        line_len_sq = line_vec.magnitude_squared()
        if line_len_sq < 1e-9:
            return point.distance_to(self.start)
        
        t = max(0.0, min(1.0, point_vec.dot(line_vec) / line_len_sq))
        closest = self.start + line_vec * t
        return point.distance_to(closest)
    
    def __repr__(self) -> str:
        return f"Line3D(start={self.start}, end={self.end})"


class Plane:
    """3D plane defined by normal and distance from origin."""
    
    def __init__(self, normal: vector3D, distance: float):
        """
        Initialize plane.
        
        Args:
            normal: Plane normal (will be normalized)
            distance: Distance from origin along normal
        """
        self.normal = normal.normalize()
        self.distance = distance
    
    @classmethod
    def from_point_normal(cls, point: vector3D, normal: vector3D) -> 'Plane':
        """Create plane from point and normal."""
        normal = normal.normalize()
        distance = -point.dot(normal)
        return cls(normal, distance)
    
    @classmethod
    def from_points(cls, p1: vector3D, p2: vector3D, p3: vector3D) -> 'Plane':
        """Create plane from three points."""
        v1 = p2 - p1
        v2 = p3 - p1
        normal = v1.cross(v2).normalize()
        return cls.from_point_normal(p1, normal)
    
    def distance_to_point(self, point: vector3D) -> float:
        """Signed distance from point to plane."""
        return point.dot(self.normal) + self.distance
    
    def point_on_plane(self) -> vector3D:
        """Get a point on the plane."""
        return self.normal * (-self.distance)
    
    def project_point(self, point: vector3D) -> vector3D:
        """Project point onto plane."""
        dist = self.distance_to_point(point)
        return point - self.normal * dist
    
    def __repr__(self) -> str:
        return f"Plane(normal={self.normal}, distance={self.distance})"


class Sphere:
    """3D sphere."""
    
    def __init__(self, center: vector3D, radius: float):
        """Initialize sphere."""
        self.center = center
        self.radius = radius
    
    def contains_point(self, point: vector3D) -> bool:
        """Check if point is inside sphere."""
        return self.center.distance_squared_to(point) <= self.radius * self.radius
    
    def distance_to_point(self, point: vector3D) -> float:
        """Distance from sphere surface to point (negative if inside)."""
        return self.center.distance_to(point) - self.radius
    
    def intersects_sphere(self, other: 'Sphere') -> bool:
        """Check if two spheres intersect."""
        dist = self.center.distance_to(other.center)
        return dist <= (self.radius + other.radius)
    
    def volume(self) -> float:
        """Sphere volume."""
        return (4.0 / 3.0) * math.pi * self.radius ** 3
    
    def surface_area(self) -> float:
        """Sphere surface area."""
        return 4.0 * math.pi * self.radius ** 2
    
    def __repr__(self) -> str:
        return f"Sphere(center={self.center}, radius={self.radius})"


class AABB:
    """Axis-Aligned Bounding Box."""
    
    def __init__(self, min_point: vector3D, max_point: vector3D):
        """
        Initialize AABB.
        
        Args:
            min_point: Minimum corner
            max_point: Maximum corner
        """
        self.min = min_point
        self.max = max_point
    
    @classmethod
    def from_center_size(cls, center: vector3D, size: vector3D) -> 'AABB':
        """Create AABB from center and size."""
        half_size = size * 0.5
        return cls(center - half_size, center + half_size)
    
    def center(self) -> vector3D:
        """Box center."""
        return (self.min + self.max) * 0.5
    
    def size(self) -> vector3D:
        """Box size."""
        return self.max - self.min
    
    def contains_point(self, point: vector3D) -> bool:
        """Check if point is inside box."""
        return (self.min.x <= point.x <= self.max.x and
                self.min.y <= point.y <= self.max.y and
                self.min.z <= point.z <= self.max.z)
    
    def intersects_aabb(self, other: 'AABB') -> bool:
        """Check if two AABBs intersect."""
        return (self.min.x <= other.max.x and self.max.x >= other.min.x and
                self.min.y <= other.max.y and self.max.y >= other.min.y and
                self.min.z <= other.max.z and self.max.z >= other.min.z)
    
    def intersects_sphere(self, sphere: Sphere) -> bool:
        """Check if AABB intersects sphere."""
        closest = vector3D(
            max(self.min.x, min(sphere.center.x, self.max.x)),
            max(self.min.y, min(sphere.center.y, self.max.y)),
            max(self.min.z, min(sphere.center.z, self.max.z))
        )
        return sphere.center.distance_squared_to(closest) <= sphere.radius * sphere.radius
    
    def expand(self, point: vector3D):
        """Expand box to include point."""
        self.min = vector3D(
            min(self.min.x, point.x),
            min(self.min.y, point.y),
            min(self.min.z, point.z)
        )
        self.max = vector3D(
            max(self.max.x, point.x),
            max(self.max.y, point.y),
            max(self.max.z, point.z)
        )
    
    def volume(self) -> float:
        """Box volume."""
        size = self.size()
        return size.x * size.y * size.z
    
    def __repr__(self) -> str:
        return f"AABB(min={self.min}, max={self.max})"


class Frustum:
    """View frustum (for culling)."""
    
    def __init__(self):
        """Initialize empty frustum."""
        self.planes: List[Plane] = []
    
    def from_matrix(self, mvp_matrix) -> 'Frustum':
        """
        Create frustum from MVP matrix.
        Note: This is a simplified version - full implementation would extract 6 planes.
        """
        # This would extract the 6 frustum planes from the matrix
        # Left, Right, Bottom, Top, Near, Far
        # Implementation depends on matrix format
        return self
    
    def contains_point(self, point: vector3D) -> bool:
        """Check if point is inside frustum."""
        for plane in self.planes:
            if plane.distance_to_point(point) < 0:
                return False
        return True
    
    def contains_sphere(self, sphere: Sphere) -> bool:
        """Check if sphere intersects frustum."""
        for plane in self.planes:
            dist = plane.distance_to_point(sphere.center)
            if dist < -sphere.radius:
                return False  # Completely outside
        return True
    
    def __repr__(self) -> str:
        return f"Frustum(planes={len(self.planes)})"


# Intersection functions
def ray_plane_intersection(ray: Ray3D, plane: Plane) -> Optional[vector3D]:
    """Find intersection point between ray and plane."""
    denom = ray.direction.dot(plane.normal)
    if abs(denom) < 1e-9:
        return None  # Ray is parallel to plane
    
    t = -(ray.origin.dot(plane.normal) + plane.distance) / denom
    if t < 0:
        return None  # Intersection is behind ray origin
    
    return ray.point_at(t)


def ray_sphere_intersection(ray: Ray3D, sphere: Sphere) -> Optional[Tuple[vector3D, vector3D]]:
    """Find intersection points between ray and sphere. Returns (point1, point2) or None."""
    oc = ray.origin - sphere.center
    a = ray.direction.dot(ray.direction)
    b = 2.0 * oc.dot(ray.direction)
    c = oc.dot(oc) - sphere.radius * sphere.radius
    
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    
    sqrt_d = math.sqrt(discriminant)
    t1 = (-b - sqrt_d) / (2 * a)
    t2 = (-b + sqrt_d) / (2 * a)
    
    if t1 < 0 and t2 < 0:
        return None
    
    p1 = ray.point_at(t1) if t1 >= 0 else None
    p2 = ray.point_at(t2) if t2 >= 0 else None
    
    return (p1, p2)


def ray_aabb_intersection(ray: Ray3D, aabb: AABB) -> Optional[Tuple[float, float]]:
    """
    Find intersection between ray and AABB.
    Returns (t_min, t_max) or None if no intersection.
    """
    inv_dir = vector3D(1.0 / ray.direction.x, 1.0 / ray.direction.y, 1.0 / ray.direction.z)
    
    t1 = (aabb.min.x - ray.origin.x) * inv_dir.x
    t2 = (aabb.max.x - ray.origin.x) * inv_dir.x
    t3 = (aabb.min.y - ray.origin.y) * inv_dir.y
    t4 = (aabb.max.y - ray.origin.y) * inv_dir.y
    t5 = (aabb.min.z - ray.origin.z) * inv_dir.z
    t6 = (aabb.max.z - ray.origin.z) * inv_dir.z
    
    t_min = max(max(min(t1, t2), min(t3, t4)), min(t5, t6))
    t_max = min(min(max(t1, t2), max(t3, t4)), max(t5, t6))
    
    if t_max < 0 or t_min > t_max:
        return None
    
    return (t_min, t_max)

