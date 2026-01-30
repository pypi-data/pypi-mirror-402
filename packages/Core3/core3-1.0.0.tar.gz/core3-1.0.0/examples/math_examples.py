"""
Math Library Examples

Demonstrates usage of the IntPy math library.
"""
from IntPy import (
    vector2D, vector3D, vector4D,
    Matrix2x2, Matrix3x3, Matrix4x4,
    Quaternion,
    lerp, smoothstep, clamp,
    noise_2d, fbm_2d,
    bezier_quadratic_vec,
    degrees_to_radians
)


def vector_examples():
    """Vector operations examples."""
    print("=== Vector Examples ===")
    
    # 2D Vectors
    v1 = vector2D(1, 2)
    v2 = vector2D(3, 4)
    print(f"v1 + v2 = {v1 + v2}")
    print(f"v1.dot(v2) = {v1.dot(v2)}")
    print(f"v1.magnitude() = {v1.magnitude()}")
    print(f"v1.normalize() = {v1.normalize()}")
    
    # 3D Vectors
    v3 = vector3D(1, 2, 3)
    v4 = vector3D(4, 5, 6)
    print(f"\nv3 + v4 = {v3 + v4}")
    print(f"v3.cross(v4) = {v3.cross(v4)}")
    print(f"v3.distance_to(v4) = {v3.distance_to(v4)}")
    
    # Vector interpolation
    result = v3.lerp(v4, 0.5)
    print(f"v3.lerp(v4, 0.5) = {result}")
    
    print()


def matrix_examples():
    """Matrix operations examples."""
    print("=== Matrix Examples ===")
    
    # 2x2 Matrix
    m2 = Matrix2x2.rotation(degrees_to_radians(45))
    print(f"2x2 Rotation Matrix:\n{m2}")
    print(f"Determinant: {m2.determinant()}")
    
    # 4x4 Matrix
    translation = Matrix4x4.translation(10, 20, 30)
    rotation = Matrix4x4.rotation_y(degrees_to_radians(90))
    scale = Matrix4x4.scale(2, 2, 2)
    
    # Combine transformations
    transform = translation * rotation * scale
    print(f"\n4x4 Transform Matrix created")
    
    # Transform a point
    point = vector3D(1, 0, 0)
    transformed = transform * point
    print(f"Point {point} transformed: {transformed}")
    
    print()


def quaternion_examples():
    """Quaternion examples."""
    print("=== Quaternion Examples ===")
    
    # Create quaternion from Euler angles
    quat = Quaternion.from_euler(
        degrees_to_radians(45),  # Pitch
        degrees_to_radians(90),  # Yaw
        degrees_to_radians(0)     # Roll
    )
    print(f"Quaternion from Euler: {quat}")
    
    # Create from axis-angle
    axis = vector3D(0, 1, 0)
    quat2 = Quaternion.from_axis_angle(axis, degrees_to_radians(90))
    print(f"Quaternion from axis-angle: {quat2}")
    
    # Rotate a vector
    vec = vector3D(1, 0, 0)
    rotated = quat2.rotate_vector(vec)
    print(f"Vector {vec} rotated: {rotated}")
    
    # Interpolation
    quat3 = Quaternion.from_euler(0, 0, 0)
    interpolated = quat2.slerp(quat3, 0.5)
    print(f"Interpolated quaternion: {interpolated}")
    
    # Convert to matrix
    matrix = quat2.to_matrix4x4()
    print(f"Quaternion to matrix conversion complete")
    
    print()


def advanced_math_examples():
    """Advanced math examples."""
    print("=== Advanced Math Examples ===")
    
    # Interpolation
    value = lerp(0.0, 100.0, 0.5)
    print(f"lerp(0, 100, 0.5) = {value}")
    
    smooth = smoothstep(0.0, 1.0, 0.5)
    print(f"smoothstep(0, 1, 0.5) = {smooth}")
    
    clamped = clamp(150.0, 0.0, 100.0)
    print(f"clamp(150, 0, 100) = {clamped}")
    
    # Noise
    noise_value = noise_2d(10.5, 20.3)
    print(f"noise_2d(10.5, 20.3) = {noise_value}")
    
    fbm_value = fbm_2d(10.5, 20.3, octaves=4)
    print(f"fbm_2d(10.5, 20.3, octaves=4) = {fbm_value}")
    
    # Bezier curve
    p0 = vector2D(0, 0)
    p1 = vector2D(1, 2)
    p2 = vector2D(2, 0)
    bezier_point = bezier_quadratic_vec(0.5, p0, p1, p2)
    print(f"Bezier curve point at t=0.5: {bezier_point}")
    
    print()


if __name__ == "__main__":
    print("Core Math Library Examples\n")
    
    vector_examples()
    matrix_examples()
    quaternion_examples()
    advanced_math_examples()
    
    print("Examples complete!")

