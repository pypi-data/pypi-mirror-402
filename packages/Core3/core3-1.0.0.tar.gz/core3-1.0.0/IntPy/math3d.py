"""
3D math utilities for transformations, intersections, and spatial operations.
"""
import math
from typing import Optional, Tuple, List
from .vectors import vector3D
from .geometry import Ray3D, Plane, Sphere, AABB
from .matrices import Matrix4x4


def distance_point_to_line(point: vector3D, line_start: vector3D, line_end: vector3D) -> float:
    """Distance from point to line segment."""
    line_vec = line_end - line_start
    point_vec = point - line_start
    
    line_len_sq = line_vec.magnitude_squared()
    if line_len_sq < 1e-9:
        return point.distance_to(line_start)
    
    t = max(0.0, min(1.0, point_vec.dot(line_vec) / line_len_sq))
    closest = line_start + line_vec * t
    return point.distance_to(closest)


def distance_point_to_plane(point: vector3D, plane: Plane) -> float:
    """Signed distance from point to plane."""
    return plane.distance_to_point(point)


def project_point_on_plane(point: vector3D, plane: Plane) -> vector3D:
    """Project point onto plane."""
    return plane.project_point(point)


def reflect_vector(vector: vector3D, normal: vector3D) -> vector3D:
    """Reflect vector off a surface normal."""
    return vector.reflect(normal)


def refract_vector(vector: vector3D, normal: vector3D, eta: float) -> Optional[vector3D]:
    """
    Refract vector through a surface.
    
    Args:
        vector: Incident vector
        normal: Surface normal
        eta: Refraction ratio (n1/n2)
    
    Returns:
        Refracted vector or None if total internal reflection
    """
    vector = vector.normalize()
    normal = normal.normalize()
    
    cos_i = -normal.dot(vector)
    sin_t2 = eta * eta * (1.0 - cos_i * cos_i)
    
    if sin_t2 > 1.0:
        return None  # Total internal reflection
    
    cos_t = math.sqrt(1.0 - sin_t2)
    return vector * eta + normal * (eta * cos_i - cos_t)


def barycentric_coordinates(point: vector3D, v0: vector3D, v1: vector3D, v2: vector3D) -> Tuple[float, float, float]:
    """
    Calculate barycentric coordinates of point in triangle.
    
    Returns:
        (u, v, w) barycentric coordinates
    """
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    v0p = point - v0
    
    dot00 = v0v2.dot(v0v2)
    dot01 = v0v2.dot(v0v1)
    dot02 = v0v2.dot(v0p)
    dot11 = v0v1.dot(v0v1)
    dot12 = v0v1.dot(v0p)
    
    inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    w = 1.0 - u - v
    
    return (u, v, w)


def point_in_triangle(point: vector3D, v0: vector3D, v1: vector3D, v2: vector3D) -> bool:
    """Check if point is inside triangle."""
    u, v, w = barycentric_coordinates(point, v0, v1, v2)
    return u >= 0 and v >= 0 and w >= 0


def triangle_area(v0: vector3D, v1: vector3D, v2: vector3D) -> float:
    """Calculate triangle area."""
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    cross = v0v1.cross(v0v2)
    return cross.magnitude() * 0.5


def triangle_normal(v0: vector3D, v1: vector3D, v2: vector3D) -> vector3D:
    """Calculate triangle normal."""
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    return v0v1.cross(v0v2).normalize()


def closest_point_on_line(point: vector3D, line_start: vector3D, line_end: vector3D) -> vector3D:
    """Find closest point on line segment to given point."""
    line_vec = line_end - line_start
    point_vec = point - line_start
    
    line_len_sq = line_vec.magnitude_squared()
    if line_len_sq < 1e-9:
        return line_start
    
    t = max(0.0, min(1.0, point_vec.dot(line_vec) / line_len_sq))
    return line_start + line_vec * t


def closest_point_on_plane(point: vector3D, plane: Plane) -> vector3D:
    """Find closest point on plane to given point."""
    return plane.project_point(point)


def closest_points_between_lines(
    line1_start: vector3D, line1_end: vector3D,
    line2_start: vector3D, line2_end: vector3D
) -> Tuple[vector3D, vector3D]:
    """
    Find closest points between two line segments.
    
    Returns:
        (closest_point_on_line1, closest_point_on_line2)
    """
    d1 = line1_end - line1_start
    d2 = line2_end - line2_start
    r = line1_start - line2_start
    
    a = d1.dot(d1)
    e = d2.dot(d2)
    f = d2.dot(r)
    
    if a < 1e-9 and e < 1e-9:
        # Both segments are points
        return (line1_start, line2_start)
    
    if a < 1e-9:
        # First segment is a point
        t2 = max(0.0, min(1.0, f / e))
        return (line1_start, line2_start + d2 * t2)
    
    c = d1.dot(r)
    
    if e < 1e-9:
        # Second segment is a point
        t1 = max(0.0, min(1.0, -c / a))
        return (line1_start + d1 * t1, line2_start)
    
    b = d1.dot(d2)
    denom = a * e - b * b
    
    if abs(denom) < 1e-9:
        # Lines are parallel
        t1 = 0.0
    else:
        t1 = max(0.0, min(1.0, (b * f - c * e) / denom))
    
    t2 = (b * t1 + f) / e
    
    if t2 < 0.0:
        t2 = 0.0
        t1 = max(0.0, min(1.0, -c / a))
    elif t2 > 1.0:
        t2 = 1.0
        t1 = max(0.0, min(1.0, (b - c) / a))
    
    return (line1_start + d1 * t1, line2_start + d2 * t2)


def transform_point(point: vector3D, matrix: Matrix4x4) -> vector3D:
    """Transform point by 4x4 matrix."""
    return matrix * point


def transform_direction(direction: vector3D, matrix: Matrix4x4) -> vector3D:
    """Transform direction vector by 4x4 matrix (ignores translation)."""
    # Extract 3x3 rotation part
    result = vector3D(
        matrix[0, 0] * direction.x + matrix[0, 1] * direction.y + matrix[0, 2] * direction.z,
        matrix[1, 0] * direction.x + matrix[1, 1] * direction.y + matrix[1, 2] * direction.z,
        matrix[2, 0] * direction.x + matrix[2, 1] * direction.y + matrix[2, 2] * direction.z
    )
    return result.normalize()


def decompose_matrix(matrix: Matrix4x4) -> Tuple[vector3D, vector3D, vector3D]:
    """
    Decompose matrix into translation, rotation (euler), and scale.
    
    Returns:
        (translation, rotation_euler, scale)
    """
    # Extract translation
    translation = vector3D(matrix[0, 3], matrix[1, 3], matrix[2, 3])
    
    # Extract scale from columns
    scale_x = vector3D(matrix[0, 0], matrix[1, 0], matrix[2, 0]).magnitude()
    scale_y = vector3D(matrix[0, 1], matrix[1, 1], matrix[2, 1]).magnitude()
    scale_z = vector3D(matrix[0, 2], matrix[1, 2], matrix[2, 2]).magnitude()
    scale = vector3D(scale_x, scale_y, scale_z)
    
    # Extract rotation (simplified - would use quaternion in production)
    # For now, return zero rotation
    rotation = vector3D(0, 0, 0)
    
    return (translation, rotation, scale)


def screen_to_world_ray(
    screen_x: float, screen_y: float,
    screen_width: int, screen_height: int,
    view_matrix: Matrix4x4, projection_matrix: Matrix4x4
) -> Ray3D:
    """
    Convert screen coordinates to world space ray.
    
    Args:
        screen_x, screen_y: Screen coordinates (0 to width/height)
        screen_width, screen_height: Screen dimensions
        view_matrix: View matrix
        projection_matrix: Projection matrix
    
    Returns:
        Ray in world space
    """
    # Normalize screen coordinates to [-1, 1]
    x = (2.0 * screen_x / screen_width) - 1.0
    y = 1.0 - (2.0 * screen_y / screen_height)
    
    # Create ray in clip space
    near_point = vector3D(x, y, -1.0)
    far_point = vector3D(x, y, 1.0)
    
    # Invert matrices to get world space
    inv_view = view_matrix.inverse()
    inv_proj = projection_matrix.inverse()
    
    # Transform to world space
    world_near = inv_view * (inv_proj * near_point)
    world_far = inv_view * (inv_proj * far_point)
    
    direction = (world_far - world_near).normalize()
    
    return Ray3D(world_near, direction)


def calculate_tangent_space(
    v0: vector3D, v1: vector3D, v2: vector3D,
    uv0: Tuple[float, float], uv1: Tuple[float, float], uv2: Tuple[float, float]
) -> Tuple[vector3D, vector3D, vector3D]:
    """
    Calculate tangent space (tangent, bitangent, normal) for a triangle.
    
    Returns:
        (tangent, bitangent, normal)
    """
    edge1 = v1 - v0
    edge2 = v2 - v0
    
    delta_uv1 = (uv1[0] - uv0[0], uv1[1] - uv0[1])
    delta_uv2 = (uv2[0] - uv0[0], uv2[1] - uv0[1])
    
    f = 1.0 / (delta_uv1[0] * delta_uv2[1] - delta_uv2[0] * delta_uv1[1])
    
    tangent = vector3D(
        f * (delta_uv2[1] * edge1.x - delta_uv1[1] * edge2.x),
        f * (delta_uv2[1] * edge1.y - delta_uv1[1] * edge2.y),
        f * (delta_uv2[1] * edge1.z - delta_uv1[1] * edge2.z)
    ).normalize()
    
    bitangent = vector3D(
        f * (-delta_uv2[0] * edge1.x + delta_uv1[0] * edge2.x),
        f * (-delta_uv2[0] * edge1.y + delta_uv1[0] * edge2.y),
        f * (-delta_uv2[0] * edge1.z + delta_uv1[0] * edge2.z)
    ).normalize()
    
    normal = edge1.cross(edge2).normalize()
    
    return (tangent, bitangent, normal)

