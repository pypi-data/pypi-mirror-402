"""
Transform system for positioning, rotating, and scaling 3D objects.
"""
import math
from IntPy.vectors import vector3D


class Transform:
    """Transform component for 3D objects."""
    
    def __init__(
        self,
        position: vector3D = None,
        rotation: vector3D = None,
        scale: vector3D = None
    ):
        """
        Initialize transform.
        
        Args:
            position: World position
            rotation: Euler angles in degrees (pitch, yaw, roll)
            scale: Scale factors (x, y, z)
        """
        self.position = position if position else vector3D(0, 0, 0)
        self.rotation = rotation if rotation else vector3D(0, 0, 0)
        self.scale = scale if scale else vector3D(1, 1, 1)
        
        # Cached matrix (recalculated when transform changes)
        self._matrix_dirty = True
        self._matrix = None
    
    def get_matrix(self) -> list:
        """
        Get transformation matrix (4x4 as flat list, column-major).
        Combines translation, rotation, and scale.
        """
        if self._matrix_dirty:
            self._matrix = self._calculate_matrix()
            self._matrix_dirty = False
        return self._matrix
    
    def _calculate_matrix(self) -> list:
        """Calculate the combined transformation matrix."""
        # Scale matrix
        sx, sy, sz = self.scale.x, self.scale.y, self.scale.z
        scale_matrix = [
            sx, 0, 0, 0,
            0, sy, 0, 0,
            0, 0, sz, 0,
            0, 0, 0, 1
        ]
        
        # Rotation matrix (Euler angles: pitch, yaw, roll)
        rx = math.radians(self.rotation.x)
        ry = math.radians(self.rotation.y)
        rz = math.radians(self.rotation.z)
        
        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)
        
        # Rotation matrix (ZYX order)
        rot_matrix = [
            cy * cz, cx * sz + sx * sy * cz, sx * sz - cx * sy * cz, 0,
            -cy * sz, cx * cz - sx * sy * sz, sx * cz + cx * sy * sz, 0,
            sy, -sx * cy, cx * cy, 0,
            0, 0, 0, 1
        ]
        
        # Translation matrix
        tx, ty, tz = self.position.x, self.position.y, self.position.z
        trans_matrix = [
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            tx, ty, tz, 1
        ]
        
        # Combine: Translation * Rotation * Scale
        return self._multiply_matrices(self._multiply_matrices(trans_matrix, rot_matrix), scale_matrix)
    
    def _multiply_matrices(self, a: list, b: list) -> list:
        """Multiply two 4x4 matrices."""
        result = [0] * 16
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    result[i * 4 + j] += a[i * 4 + k] * b[k * 4 + j]
        return result
    
    def translate(self, delta: vector3D):
        """Translate the transform by a delta vector."""
        self.position = self.position + delta
        self._matrix_dirty = True
    
    def rotate(self, delta: vector3D):
        """Rotate the transform by delta Euler angles."""
        self.rotation = vector3D(
            self.rotation.x + delta.x,
            self.rotation.y + delta.y,
            self.rotation.z + delta.z
        )
        self._matrix_dirty = True
    
    def set_position(self, position: vector3D):
        """Set the position."""
        self.position = position
        self._matrix_dirty = True
    
    def set_rotation(self, rotation: vector3D):
        """Set the rotation (Euler angles in degrees)."""
        self.rotation = rotation
        self._matrix_dirty = True
    
    def set_scale(self, scale: vector3D):
        """Set the scale."""
        self.scale = scale
        self._matrix_dirty = True
    
    def get_forward(self) -> vector3D:
        """Get forward direction vector based on rotation."""
        rx = math.radians(self.rotation.x)
        ry = math.radians(self.rotation.y)
        
        return vector3D(
            math.sin(ry) * math.cos(rx),
            -math.sin(rx),
            -math.cos(ry) * math.cos(rx)
        )
    
    def get_right(self) -> vector3D:
        """Get right direction vector based on rotation."""
        ry = math.radians(self.rotation.y)
        return vector3D(math.cos(ry), 0, -math.sin(ry))
    
    def get_up(self) -> vector3D:
        """Get up direction vector based on rotation."""
        return self._cross(self.get_forward(), self.get_right())
    
    def _cross(self, a: vector3D, b: vector3D) -> vector3D:
        """Cross product."""
        return vector3D(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )
    
    def __repr__(self):
        return f"Transform(pos={self.position}, rot={self.rotation}, scale={self.scale})"

