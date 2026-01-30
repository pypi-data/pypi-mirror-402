"""
Quaternion math for 3D rotations.
Quaternions provide smooth interpolation and avoid gimbal lock.
"""
import math
from typing import Tuple, Optional
from .vectors import vector3D
from .matrices import Matrix3x3, Matrix4x4


class Quaternion:
    """Quaternion class for 3D rotations."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0):
        """
        Initialize quaternion.
        
        Args:
            x, y, z: Vector part
            w: Scalar part
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)
    
    def __add__(self, other: 'Quaternion') -> 'Quaternion':
        """Quaternion addition."""
        return Quaternion(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
            self.w + other.w
        )
    
    def __sub__(self, other: 'Quaternion') -> 'Quaternion':
        """Quaternion subtraction."""
        return Quaternion(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
            self.w - other.w
        )
    
    def __mul__(self, other: 'Quaternion') -> 'Quaternion':
        """Quaternion multiplication (rotation composition)."""
        return Quaternion(
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
        )
    
    def __neg__(self) -> 'Quaternion':
        """Negate quaternion."""
        return Quaternion(-self.x, -self.y, -self.z, -self.w)
    
    def __eq__(self, other: 'Quaternion') -> bool:
        """Check equality."""
        return (abs(self.x - other.x) < 1e-9 and
                abs(self.y - other.y) < 1e-9 and
                abs(self.z - other.z) < 1e-9 and
                abs(self.w - other.w) < 1e-9)
    
    def magnitude(self) -> float:
        """Calculate quaternion magnitude."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)
    
    def magnitude_squared(self) -> float:
        """Calculate squared magnitude."""
        return self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w
    
    def normalize(self) -> 'Quaternion':
        """Normalize quaternion."""
        mag = self.magnitude()
        if mag < 1e-9:
            return Quaternion(0, 0, 0, 1)
        inv_mag = 1.0 / mag
        return Quaternion(
            self.x * inv_mag,
            self.y * inv_mag,
            self.z * inv_mag,
            self.w * inv_mag
        )
    
    def conjugate(self) -> 'Quaternion':
        """Conjugate quaternion (inverse rotation)."""
        return Quaternion(-self.x, -self.y, -self.z, self.w)
    
    def inverse(self) -> 'Quaternion':
        """Inverse quaternion."""
        mag_sq = self.magnitude_squared()
        if mag_sq < 1e-9:
            return Quaternion(0, 0, 0, 1)
        inv_mag_sq = 1.0 / mag_sq
        return Quaternion(
            -self.x * inv_mag_sq,
            -self.y * inv_mag_sq,
            -self.z * inv_mag_sq,
            self.w * inv_mag_sq
        )
    
    def dot(self, other: 'Quaternion') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w
    
    def rotate_vector(self, v: vector3D) -> vector3D:
        """Rotate a vector by this quaternion."""
        # q * v * q^-1
        q_vec = Quaternion(v.x, v.y, v.z, 0)
        result = self * q_vec * self.inverse()
        return vector3D(result.x, result.y, result.z)
    
    def to_euler(self) -> vector3D:
        """
        Convert quaternion to Euler angles (pitch, yaw, roll).
        Returns angles in radians.
        """
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1.0 - 2.0 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2.0 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1.0 - 2.0 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return vector3D(pitch, yaw, roll)
    
    def to_matrix3x3(self) -> Matrix3x3:
        """Convert quaternion to 3x3 rotation matrix."""
        x, y, z, w = self.x, self.y, self.z, self.w
        
        return Matrix3x3([
            1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)
        ])
    
    def to_matrix4x4(self) -> Matrix4x4:
        """Convert quaternion to 4x4 rotation matrix."""
        x, y, z, w = self.x, self.y, self.z, self.w
        
        return Matrix4x4([
            1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0,
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0,
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0,
            0, 0, 0, 1
        ])
    
    def lerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """Linear interpolation (not normalized)."""
        return Quaternion(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t,
            self.w + (other.w - self.w) * t
        ).normalize()
    
    def slerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """Spherical linear interpolation."""
        # Normalize
        q1 = self.normalize()
        q2 = other.normalize()
        
        # Calculate dot product
        dot = q1.dot(q2)
        
        # If dot < 0, negate one quaternion to take shorter path
        if dot < 0:
            q2 = -q2
            dot = -dot
        
        # Clamp dot to [-1, 1]
        dot = max(-1.0, min(1.0, dot))
        
        # If quaternions are very close, use lerp
        if abs(dot) > 0.9995:
            return q1.lerp(q2, t)
        
        # Calculate angle
        theta = math.acos(dot)
        sin_theta = math.sin(theta)
        
        # Calculate weights
        w1 = math.sin((1.0 - t) * theta) / sin_theta
        w2 = math.sin(t * theta) / sin_theta
        
        # Interpolate
        return Quaternion(
            q1.x * w1 + q2.x * w2,
            q1.y * w1 + q2.y * w2,
            q1.z * w1 + q2.z * w2,
            q1.w * w1 + q2.w * w2
        ).normalize()
    
    def nlerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """Normalized linear interpolation (faster than slerp)."""
        return self.lerp(other, t)
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z, self.w)
    
    def to_list(self) -> list:
        """Convert to list."""
        return [self.x, self.y, self.z, self.w]
    
    def __repr__(self) -> str:
        return f"Quaternion({self.x}, {self.y}, {self.z}, {self.w})"
    
    @staticmethod
    def identity() -> 'Quaternion':
        """Identity quaternion (no rotation)."""
        return Quaternion(0, 0, 0, 1)
    
    @staticmethod
    def from_axis_angle(axis: vector3D, angle: float) -> 'Quaternion':
        """
        Create quaternion from axis-angle representation.
        
        Args:
            axis: Rotation axis (will be normalized)
            angle: Rotation angle in radians
        """
        axis = axis.normalize()
        half_angle = angle / 2.0
        s = math.sin(half_angle)
        c = math.cos(half_angle)
        
        return Quaternion(
            axis.x * s,
            axis.y * s,
            axis.z * s,
            c
        )
    
    @staticmethod
    def from_euler(pitch: float, yaw: float, roll: float) -> 'Quaternion':
        """
        Create quaternion from Euler angles.
        
        Args:
            pitch: Rotation around X-axis (radians)
            yaw: Rotation around Y-axis (radians)
            roll: Rotation around Z-axis (radians)
        """
        # Convert to quaternion
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        return Quaternion(
            cy * cp * sr - sy * sp * cr,
            sy * cp * sr + cy * sp * cr,
            sy * cp * cr - cy * sp * sr,
            cy * cp * cr + sy * sp * sr
        )
    
    @staticmethod
    def from_euler_vec(euler: vector3D) -> 'Quaternion':
        """Create quaternion from Euler angles vector."""
        return Quaternion.from_euler(euler.x, euler.y, euler.z)
    
    @staticmethod
    def from_matrix3x3(m: Matrix3x3) -> 'Quaternion':
        """Create quaternion from 3x3 rotation matrix."""
        trace = m[0, 0] + m[1, 1] + m[2, 2]
        
        if trace > 0:
            s = math.sqrt(trace + 1.0) * 2  # s = 4 * qw
            w = 0.25 * s
            x = (m[2, 1] - m[1, 2]) / s
            y = (m[0, 2] - m[2, 0]) / s
            z = (m[1, 0] - m[0, 1]) / s
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
            w = (m[2, 1] - m[1, 2]) / s
            x = 0.25 * s
            y = (m[0, 1] + m[1, 0]) / s
            z = (m[0, 2] + m[2, 0]) / s
        elif m[1, 1] > m[2, 2]:
            s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
            w = (m[0, 2] - m[2, 0]) / s
            x = (m[0, 1] + m[1, 0]) / s
            y = 0.25 * s
            z = (m[1, 2] + m[2, 1]) / s
        else:
            s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
            w = (m[1, 0] - m[0, 1]) / s
            x = (m[0, 2] + m[2, 0]) / s
            y = (m[1, 2] + m[2, 1]) / s
            z = 0.25 * s
        
        return Quaternion(x, y, z, w).normalize()
    
    @staticmethod
    def from_matrix4x4(m: Matrix4x4) -> 'Quaternion':
        """Create quaternion from 4x4 rotation matrix."""
        # Extract 3x3 rotation part
        rot_matrix = Matrix3x3([
            m[0, 0], m[0, 1], m[0, 2],
            m[1, 0], m[1, 1], m[1, 2],
            m[2, 0], m[2, 1], m[2, 2]
        ])
        return Quaternion.from_matrix3x3(rot_matrix)
    
    @staticmethod
    def look_rotation(forward: vector3D, up: vector3D = None) -> 'Quaternion':
        """
        Create quaternion that rotates to look in a direction.
        
        Args:
            forward: Forward direction (will be normalized)
            up: Up direction (defaults to (0, 1, 0))
        """
        if up is None:
            up = vector3D.up()
        
        forward = forward.normalize()
        up = up.normalize()
        
        # Calculate right vector
        right = forward.cross(up).normalize()
        up = right.cross(forward).normalize()
        
        # Build rotation matrix
        m = Matrix3x3([
            right.x, up.x, -forward.x,
            right.y, up.y, -forward.y,
            right.z, up.z, -forward.z
        ])
        
        return Quaternion.from_matrix3x3(m)

