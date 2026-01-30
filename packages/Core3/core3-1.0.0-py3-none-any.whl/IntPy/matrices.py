"""
Matrix math for 2x2, 3x3, and 4x4 matrices.
Supports common matrix operations, transformations, and utilities.
"""
import math
from typing import List, Optional, Tuple, Union
from .vectors import vector2D, vector3D, vector4D


class Matrix2x2:
    """2x2 matrix class."""
    
    def __init__(self, values: Optional[List[float]] = None):
        """
        Initialize 2x2 matrix.
        
        Args:
            values: 4-element list [m00, m01, m10, m11] (row-major)
                   or None for identity matrix
        """
        if values is None:
            self.m = [1.0, 0.0, 0.0, 1.0]  # Identity
        else:
            if len(values) != 4:
                raise ValueError("Matrix2x2 requires 4 values")
            self.m = [float(v) for v in values]
    
    def __getitem__(self, index: Tuple[int, int]) -> float:
        """Get element at (row, col)."""
        row, col = index
        return self.m[row * 2 + col]
    
    def __setitem__(self, index: Tuple[int, int], value: float):
        """Set element at (row, col)."""
        row, col = index
        self.m[row * 2 + col] = float(value)
    
    def __mul__(self, other: Union['Matrix2x2', vector2D, float]) -> Union['Matrix2x2', vector2D]:
        """Matrix multiplication or scalar multiplication."""
        if isinstance(other, Matrix2x2):
            return self._multiply_matrix(other)
        elif isinstance(other, vector2D):
            return self._multiply_vector(other)
        elif isinstance(other, (int, float)):
            return self._multiply_scalar(float(other))
        return NotImplemented
    
    def __rmul__(self, other: float) -> 'Matrix2x2':
        """Right scalar multiplication."""
        return self._multiply_scalar(float(other))
    
    def __add__(self, other: 'Matrix2x2') -> 'Matrix2x2':
        """Matrix addition."""
        return Matrix2x2([
            self.m[0] + other.m[0], self.m[1] + other.m[1],
            self.m[2] + other.m[2], self.m[3] + other.m[3]
        ])
    
    def __sub__(self, other: 'Matrix2x2') -> 'Matrix2x2':
        """Matrix subtraction."""
        return Matrix2x2([
            self.m[0] - other.m[0], self.m[1] - other.m[1],
            self.m[2] - other.m[2], self.m[3] - other.m[3]
        ])
    
    def _multiply_matrix(self, other: 'Matrix2x2') -> 'Matrix2x2':
        """Multiply two matrices."""
        return Matrix2x2([
            self.m[0] * other.m[0] + self.m[1] * other.m[2],
            self.m[0] * other.m[1] + self.m[1] * other.m[3],
            self.m[2] * other.m[0] + self.m[3] * other.m[2],
            self.m[2] * other.m[1] + self.m[3] * other.m[3]
        ])
    
    def _multiply_vector(self, v: vector2D) -> vector2D:
        """Multiply matrix by vector."""
        return vector2D(
            self.m[0] * v.x + self.m[1] * v.y,
            self.m[2] * v.x + self.m[3] * v.y
        )
    
    def _multiply_scalar(self, s: float) -> 'Matrix2x2':
        """Multiply matrix by scalar."""
        return Matrix2x2([v * s for v in self.m])
    
    def determinant(self) -> float:
        """Calculate determinant."""
        return self.m[0] * self.m[3] - self.m[1] * self.m[2]
    
    def inverse(self) -> 'Matrix2x2':
        """Calculate inverse matrix."""
        det = self.determinant()
        if abs(det) < 1e-9:
            raise ValueError("Matrix is singular (determinant = 0)")
        inv_det = 1.0 / det
        return Matrix2x2([
            self.m[3] * inv_det, -self.m[1] * inv_det,
            -self.m[2] * inv_det, self.m[0] * inv_det
        ])
    
    def transpose(self) -> 'Matrix2x2':
        """Transpose matrix."""
        return Matrix2x2([self.m[0], self.m[2], self.m[1], self.m[3]])
    
    def to_list(self) -> List[float]:
        """Convert to list (row-major)."""
        return self.m.copy()
    
    @staticmethod
    def identity() -> 'Matrix2x2':
        """Identity matrix."""
        return Matrix2x2([1, 0, 0, 1])
    
    @staticmethod
    def rotation(angle: float) -> 'Matrix2x2':
        """Rotation matrix (angle in radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix2x2([c, -s, s, c])
    
    @staticmethod
    def scale(sx: float, sy: float) -> 'Matrix2x2':
        """Scale matrix."""
        return Matrix2x2([sx, 0, 0, sy])
    
    def __repr__(self) -> str:
        return f"Matrix2x2([{self.m[0]}, {self.m[1]}, {self.m[2]}, {self.m[3]}])"


class Matrix3x3:
    """3x3 matrix class."""
    
    def __init__(self, values: Optional[List[float]] = None):
        """
        Initialize 3x3 matrix.
        
        Args:
            values: 9-element list (row-major) or None for identity
        """
        if values is None:
            self.m = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]  # Identity
        else:
            if len(values) != 9:
                raise ValueError("Matrix3x3 requires 9 values")
            self.m = [float(v) for v in values]
    
    def __getitem__(self, index: Tuple[int, int]) -> float:
        """Get element at (row, col)."""
        row, col = index
        return self.m[row * 3 + col]
    
    def __setitem__(self, index: Tuple[int, int], value: float):
        """Set element at (row, col)."""
        row, col = index
        self.m[row * 3 + col] = float(value)
    
    def __mul__(self, other: Union['Matrix3x3', vector3D, float]) -> Union['Matrix3x3', vector3D]:
        """Matrix multiplication."""
        if isinstance(other, Matrix3x3):
            return self._multiply_matrix(other)
        elif isinstance(other, vector3D):
            return self._multiply_vector(other)
        elif isinstance(other, (int, float)):
            return self._multiply_scalar(float(other))
        return NotImplemented
    
    def __rmul__(self, other: float) -> 'Matrix3x3':
        """Right scalar multiplication."""
        return self._multiply_scalar(float(other))
    
    def _multiply_matrix(self, other: 'Matrix3x3') -> 'Matrix3x3':
        """Multiply two matrices."""
        result = [0.0] * 9
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    result[i * 3 + j] += self.m[i * 3 + k] * other.m[k * 3 + j]
        return Matrix3x3(result)
    
    def _multiply_vector(self, v: vector3D) -> vector3D:
        """Multiply matrix by vector."""
        return vector3D(
            self.m[0] * v.x + self.m[1] * v.y + self.m[2] * v.z,
            self.m[3] * v.x + self.m[4] * v.y + self.m[5] * v.z,
            self.m[6] * v.x + self.m[7] * v.y + self.m[8] * v.z
        )
    
    def _multiply_scalar(self, s: float) -> 'Matrix3x3':
        """Multiply matrix by scalar."""
        return Matrix3x3([v * s for v in self.m])
    
    def determinant(self) -> float:
        """Calculate determinant."""
        return (self.m[0] * (self.m[4] * self.m[8] - self.m[5] * self.m[7]) -
                self.m[1] * (self.m[3] * self.m[8] - self.m[5] * self.m[6]) +
                self.m[2] * (self.m[3] * self.m[7] - self.m[4] * self.m[6]))
    
    def transpose(self) -> 'Matrix3x3':
        """Transpose matrix."""
        return Matrix3x3([
            self.m[0], self.m[3], self.m[6],
            self.m[1], self.m[4], self.m[7],
            self.m[2], self.m[5], self.m[8]
        ])
    
    def inverse(self) -> 'Matrix3x3':
        """Calculate inverse matrix."""
        det = self.determinant()
        if abs(det) < 1e-9:
            raise ValueError("Matrix is singular")
        
        inv_det = 1.0 / det
        return Matrix3x3([
            (self.m[4] * self.m[8] - self.m[5] * self.m[7]) * inv_det,
            (self.m[2] * self.m[7] - self.m[1] * self.m[8]) * inv_det,
            (self.m[1] * self.m[5] - self.m[2] * self.m[4]) * inv_det,
            (self.m[5] * self.m[6] - self.m[3] * self.m[8]) * inv_det,
            (self.m[0] * self.m[8] - self.m[2] * self.m[6]) * inv_det,
            (self.m[2] * self.m[3] - self.m[0] * self.m[5]) * inv_det,
            (self.m[3] * self.m[7] - self.m[4] * self.m[6]) * inv_det,
            (self.m[1] * self.m[6] - self.m[0] * self.m[7]) * inv_det,
            (self.m[0] * self.m[4] - self.m[1] * self.m[3]) * inv_det
        ])
    
    def to_list(self) -> List[float]:
        """Convert to list (row-major)."""
        return self.m.copy()
    
    @staticmethod
    def identity() -> 'Matrix3x3':
        """Identity matrix."""
        return Matrix3x3()
    
    @staticmethod
    def rotation_x(angle: float) -> 'Matrix3x3':
        """Rotation around X-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([1, 0, 0, 0, c, -s, 0, s, c])
    
    @staticmethod
    def rotation_y(angle: float) -> 'Matrix3x3':
        """Rotation around Y-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([c, 0, s, 0, 1, 0, -s, 0, c])
    
    @staticmethod
    def rotation_z(angle: float) -> 'Matrix3x3':
        """Rotation around Z-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([c, -s, 0, s, c, 0, 0, 0, 1])
    
    @staticmethod
    def rotation_axis(axis: vector3D, angle: float) -> 'Matrix3x3':
        """Rotation around arbitrary axis (radians)."""
        axis = axis.normalize()
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1 - c
        
        x, y, z = axis.x, axis.y, axis.z
        
        return Matrix3x3([
            t * x * x + c, t * x * y - s * z, t * x * z + s * y,
            t * x * y + s * z, t * y * y + c, t * y * z - s * x,
            t * x * z - s * y, t * y * z + s * x, t * z * z + c
        ])
    
    @staticmethod
    def scale(sx: float, sy: float, sz: float) -> 'Matrix3x3':
        """Scale matrix."""
        return Matrix3x3([sx, 0, 0, 0, sy, 0, 0, 0, sz])
    
    def __repr__(self) -> str:
        return f"Matrix3x3([{', '.join(str(v) for v in self.m)}])"


class Matrix4x4:
    """4x4 matrix class (for 3D transformations)."""
    
    def __init__(self, values: Optional[List[float]] = None):
        """
        Initialize 4x4 matrix.
        
        Args:
            values: 16-element list (row-major) or None for identity
        """
        if values is None:
            # Identity matrix
            self.m = [1.0, 0.0, 0.0, 0.0,
                     0.0, 1.0, 0.0, 0.0,
                     0.0, 0.0, 1.0, 0.0,
                     0.0, 0.0, 0.0, 1.0]
        else:
            if len(values) != 16:
                raise ValueError("Matrix4x4 requires 16 values")
            self.m = [float(v) for v in values]
    
    def __getitem__(self, index: Union[Tuple[int, int], int]) -> Union[float, List[float]]:
        """Get element at (row, col) or row."""
        if isinstance(index, tuple):
            row, col = index
            return self.m[row * 4 + col]
        else:
            # Return entire row
            row = index
            return self.m[row * 4:(row + 1) * 4]
    
    def __setitem__(self, index: Tuple[int, int], value: float):
        """Set element at (row, col)."""
        row, col = index
        self.m[row * 4 + col] = float(value)
    
    def __mul__(self, other: Union['Matrix4x4', vector4D, vector3D, float]) -> Union['Matrix4x4', vector4D, vector3D]:
        """Matrix multiplication."""
        if isinstance(other, Matrix4x4):
            return self._multiply_matrix(other)
        elif isinstance(other, vector4D):
            return self._multiply_vector4(other)
        elif isinstance(other, vector3D):
            return self._multiply_vector3(other)
        elif isinstance(other, (int, float)):
            return self._multiply_scalar(float(other))
        return NotImplemented
    
    def __rmul__(self, other: float) -> 'Matrix4x4':
        """Right scalar multiplication."""
        return self._multiply_scalar(float(other))
    
    def _multiply_matrix(self, other: 'Matrix4x4') -> 'Matrix4x4':
        """Multiply two matrices."""
        result = [0.0] * 16
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    result[i * 4 + j] += self.m[i * 4 + k] * other.m[k * 4 + j]
        return Matrix4x4(result)
    
    def _multiply_vector4(self, v: vector4D) -> vector4D:
        """Multiply matrix by vector4D."""
        return vector4D(
            self.m[0] * v.x + self.m[1] * v.y + self.m[2] * v.z + self.m[3] * v.w,
            self.m[4] * v.x + self.m[5] * v.y + self.m[6] * v.z + self.m[7] * v.w,
            self.m[8] * v.x + self.m[9] * v.y + self.m[10] * v.z + self.m[11] * v.w,
            self.m[12] * v.x + self.m[13] * v.y + self.m[14] * v.z + self.m[15] * v.w
        )
    
    def _multiply_vector3(self, v: vector3D) -> vector3D:
        """Multiply matrix by vector3D (treats as homogeneous coordinate)."""
        x = self.m[0] * v.x + self.m[1] * v.y + self.m[2] * v.z + self.m[3]
        y = self.m[4] * v.x + self.m[5] * v.y + self.m[6] * v.z + self.m[7]
        z = self.m[8] * v.x + self.m[9] * v.y + self.m[10] * v.z + self.m[11]
        w = self.m[12] * v.x + self.m[13] * v.y + self.m[14] * v.z + self.m[15]
        if abs(w) > 1e-9:
            return vector3D(x / w, y / w, z / w)
        return vector3D(x, y, z)
    
    def _multiply_scalar(self, s: float) -> 'Matrix4x4':
        """Multiply matrix by scalar."""
        return Matrix4x4([v * s for v in self.m])
    
    def transpose(self) -> 'Matrix4x4':
        """Transpose matrix."""
        return Matrix4x4([
            self.m[0], self.m[4], self.m[8], self.m[12],
            self.m[1], self.m[5], self.m[9], self.m[13],
            self.m[2], self.m[6], self.m[10], self.m[14],
            self.m[3], self.m[7], self.m[11], self.m[15]
        ])
    
    def determinant(self) -> float:
        """Calculate determinant."""
        # Using cofactor expansion
        a = self.m[0] * (self.m[5] * (self.m[10] * self.m[15] - self.m[11] * self.m[14]) -
                         self.m[6] * (self.m[9] * self.m[15] - self.m[11] * self.m[13]) +
                         self.m[7] * (self.m[9] * self.m[14] - self.m[10] * self.m[13]))
        b = self.m[1] * (self.m[4] * (self.m[10] * self.m[15] - self.m[11] * self.m[14]) -
                         self.m[6] * (self.m[8] * self.m[15] - self.m[11] * self.m[12]) +
                         self.m[7] * (self.m[8] * self.m[14] - self.m[10] * self.m[12]))
        c = self.m[2] * (self.m[4] * (self.m[9] * self.m[15] - self.m[11] * self.m[13]) -
                         self.m[5] * (self.m[8] * self.m[15] - self.m[11] * self.m[12]) +
                         self.m[7] * (self.m[8] * self.m[13] - self.m[9] * self.m[12]))
        d = self.m[3] * (self.m[4] * (self.m[9] * self.m[14] - self.m[10] * self.m[13]) -
                         self.m[5] * (self.m[8] * self.m[14] - self.m[10] * self.m[12]) +
                         self.m[6] * (self.m[8] * self.m[13] - self.m[9] * self.m[12]))
        return a - b + c - d
    
    def inverse(self) -> 'Matrix4x4':
        """Calculate inverse matrix."""
        det = self.determinant()
        if abs(det) < 1e-9:
            raise ValueError("Matrix is singular")
        
        inv_det = 1.0 / det
        result = [0.0] * 16
        
        # Calculate cofactors
        for i in range(4):
            for j in range(4):
                # Get 3x3 submatrix
                submatrix = []
                for row in range(4):
                    if row != i:
                        for col in range(4):
                            if col != j:
                                submatrix.append(self.m[row * 4 + col])
                
                # Calculate determinant of 3x3 submatrix
                sub_det = (submatrix[0] * (submatrix[4] * submatrix[8] - submatrix[5] * submatrix[7]) -
                          submatrix[1] * (submatrix[3] * submatrix[8] - submatrix[5] * submatrix[6]) +
                          submatrix[2] * (submatrix[3] * submatrix[7] - submatrix[4] * submatrix[6]))
                
                # Cofactor with sign
                sign = 1 if (i + j) % 2 == 0 else -1
                result[j * 4 + i] = sub_det * sign * inv_det
        
        return Matrix4x4(result)
    
    def to_list(self, column_major: bool = False) -> List[float]:
        """
        Convert to list.
        
        Args:
            column_major: If True, return column-major order (for OpenGL)
        """
        if column_major:
            return [
                self.m[0], self.m[4], self.m[8], self.m[12],
                self.m[1], self.m[5], self.m[9], self.m[13],
                self.m[2], self.m[6], self.m[10], self.m[14],
                self.m[3], self.m[7], self.m[11], self.m[15]
            ]
        return self.m.copy()
    
    @staticmethod
    def identity() -> 'Matrix4x4':
        """Identity matrix."""
        return Matrix4x4()
    
    @staticmethod
    def translation(tx: float, ty: float, tz: float) -> 'Matrix4x4':
        """Translation matrix."""
        return Matrix4x4([
            1, 0, 0, tx,
            0, 1, 0, ty,
            0, 0, 1, tz,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def translation_vec(v: vector3D) -> 'Matrix4x4':
        """Translation matrix from vector."""
        return Matrix4x4.translation(v.x, v.y, v.z)
    
    @staticmethod
    def scale(sx: float, sy: float, sz: float) -> 'Matrix4x4':
        """Scale matrix."""
        return Matrix4x4([
            sx, 0, 0, 0,
            0, sy, 0, 0,
            0, 0, sz, 0,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def rotation_x(angle: float) -> 'Matrix4x4':
        """Rotation around X-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix4x4([
            1, 0, 0, 0,
            0, c, -s, 0,
            0, s, c, 0,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def rotation_y(angle: float) -> 'Matrix4x4':
        """Rotation around Y-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix4x4([
            c, 0, s, 0,
            0, 1, 0, 0,
            -s, 0, c, 0,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def rotation_z(angle: float) -> 'Matrix4x4':
        """Rotation around Z-axis (radians)."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix4x4([
            c, -s, 0, 0,
            s, c, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def rotation_axis(axis: vector3D, angle: float) -> 'Matrix4x4':
        """Rotation around arbitrary axis (radians)."""
        axis = axis.normalize()
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1 - c
        x, y, z = axis.x, axis.y, axis.z
        
        return Matrix4x4([
            t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0,
            t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0,
            t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0,
            0, 0, 0, 1
        ])
    
    @staticmethod
    def look_at(eye: vector3D, target: vector3D, up: vector3D) -> 'Matrix4x4':
        """Look-at matrix (view matrix)."""
        forward = (target - eye).normalize()
        right = forward.cross(up).normalize()
        up_new = right.cross(forward).normalize()
        
        return Matrix4x4([
            right.x, up_new.x, -forward.x, 0,
            right.y, up_new.y, -forward.y, 0,
            right.z, up_new.z, -forward.z, 0,
            -right.dot(eye), -up_new.dot(eye), forward.dot(eye), 1
        ])
    
    @staticmethod
    def perspective(fov: float, aspect: float, near: float, far: float) -> 'Matrix4x4':
        """Perspective projection matrix."""
        f = 1.0 / math.tan(fov / 2.0)
        range_inv = 1.0 / (near - far)
        
        return Matrix4x4([
            f / aspect, 0, 0, 0,
            0, f, 0, 0,
            0, 0, (near + far) * range_inv, -1,
            0, 0, near * far * range_inv * 2, 0
        ])
    
    @staticmethod
    def orthographic(left: float, right: float, bottom: float, top: float, near: float, far: float) -> 'Matrix4x4':
        """Orthographic projection matrix."""
        rl = 1.0 / (right - left)
        tb = 1.0 / (top - bottom)
        fn = 1.0 / (far - near)
        
        return Matrix4x4([
            2 * rl, 0, 0, 0,
            0, 2 * tb, 0, 0,
            0, 0, -2 * fn, 0,
            -(right + left) * rl, -(top + bottom) * tb, -(far + near) * fn, 1
        ])
    
    def __repr__(self) -> str:
        return f"Matrix4x4([{', '.join(str(v) for v in self.m)}])"

