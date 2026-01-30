"""
Camera system for managing viewport, projection, and view matrices.
Supports perspective and orthographic projections.
"""
import math
from typing import Tuple
from IntPy.vectors import vector3D


class Camera:
    """Main camera class for 3D rendering."""
    
    def __init__(
        self,
        position: vector3D = None,
        target: vector3D = None,
        up: vector3D = None,
        fov: float = 60.0,
        aspect_ratio: float = 16.0 / 9.0,
        near_plane: float = 0.1,
        far_plane: float = 1000.0,
        projection_type: str = "perspective"
    ):
        """
        Initialize camera.
        
        Args:
            position: Camera position in world space
            target: Point the camera is looking at
            up: Up vector for camera orientation
            fov: Field of view in degrees (for perspective)
            aspect_ratio: Width/Height ratio
            near_plane: Near clipping plane
            far_plane: Far clipping plane
            projection_type: "perspective" or "orthographic"
        """
        self.position = position if position else vector3D(0, 0, 5)
        self.target = target if target else vector3D(0, 0, 0)
        self.up = up if up else vector3D(0, 1, 0)
        self.fov = math.radians(fov)
        self.aspect_ratio = aspect_ratio
        self.near_plane = near_plane
        self.far_plane = far_plane
        self.projection_type = projection_type
        
        # Orthographic parameters
        self.ortho_size = 10.0
        
    def get_view_matrix(self) -> list:
        """
        Calculate view matrix (world to camera space).
        Returns 4x4 matrix as a flat list (column-major).
        """
        forward = self._normalize(self.target - self.position)
        right = self._normalize(self._cross(forward, self.up))
        up = self._cross(right, forward)
        
        # View matrix (inverse of camera transform)
        return [
            right.x, up.x, -forward.x, 0,
            right.y, up.y, -forward.y, 0,
            right.z, up.z, -forward.z, 0,
            -self._dot(right, self.position),
            -self._dot(up, self.position),
            self._dot(forward, self.position),
            1
        ]
    
    def get_projection_matrix(self) -> list:
        """
        Calculate projection matrix (camera to clip space).
        Returns 4x4 matrix as a flat list (column-major).
        """
        if self.projection_type == "perspective":
            return self._perspective_projection()
        else:
            return self._orthographic_projection()
    
    def _perspective_projection(self) -> list:
        """Calculate perspective projection matrix."""
        f = 1.0 / math.tan(self.fov / 2.0)
        range_inv = 1.0 / (self.near_plane - self.far_plane)
        
        return [
            f / self.aspect_ratio, 0, 0, 0,
            0, f, 0, 0,
            0, 0, (self.near_plane + self.far_plane) * range_inv, -1,
            0, 0, self.near_plane * self.far_plane * range_inv * 2, 0
        ]
    
    def _orthographic_projection(self) -> list:
        """Calculate orthographic projection matrix."""
        w = self.ortho_size * self.aspect_ratio
        h = self.ortho_size
        range_inv = 1.0 / (self.near_plane - self.far_plane)
        
        return [
            2.0 / w, 0, 0, 0,
            0, 2.0 / h, 0, 0,
            0, 0, 2.0 * range_inv, 0,
            0, 0, (self.near_plane + self.far_plane) * range_inv, 1
        ]
    
    def look_at(self, target: vector3D, up: vector3D = None):
        """Set camera to look at a specific target."""
        self.target = target
        if up:
            self.up = up
    
    def set_position(self, position: vector3D):
        """Set camera position."""
        self.position = position
    
    def set_fov(self, fov: float):
        """Set field of view in degrees."""
        self.fov = math.radians(fov)
    
    def set_aspect_ratio(self, aspect_ratio: float):
        """Set aspect ratio (width / height)."""
        self.aspect_ratio = aspect_ratio
    
    def set_ortho_size(self, size: float):
        """Set orthographic projection size."""
        self.ortho_size = size
    
    def _normalize(self, v: vector3D) -> vector3D:
        """Normalize a vector."""
        mag = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        if mag < 0.0001:
            return vector3D(0, 0, 0)
        return vector3D(v.x / mag, v.y / mag, v.z / mag)
    
    def _cross(self, a: vector3D, b: vector3D) -> vector3D:
        """Cross product of two vectors."""
        return vector3D(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )
    
    def _dot(self, a: vector3D, b: vector3D) -> float:
        """Dot product of two vectors."""
        return a.x * b.x + a.y * b.y + a.z * b.z
    
    def __repr__(self):
        return f"Camera(position={self.position}, target={self.target}, fov={math.degrees(self.fov)}°)"

