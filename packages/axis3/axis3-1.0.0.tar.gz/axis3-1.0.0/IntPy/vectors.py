"""
Vector math for 2D and 3D operations.
Provides vector2D and vector3D classes with comprehensive mathematical operations.
"""
import math
from typing import Union, Tuple


class vector2D:
    """2D vector class with comprehensive math operations."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)
    
    def __add__(self, other: 'vector2D') -> 'vector2D':
        return vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'vector2D') -> 'vector2D':
        return vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: Union[float, 'vector2D']) -> 'vector2D':
        if isinstance(other, vector2D):
            # Component-wise multiplication
            return vector2D(self.x * other.x, self.y * other.y)
        return vector2D(self.x * other, self.y * other)
    
    def __rmul__(self, other: float) -> 'vector2D':
        return self.__mul__(other)
    
    def __truediv__(self, other: Union[float, 'vector2D']) -> 'vector2D':
        if isinstance(other, vector2D):
            return vector2D(self.x / other.x, self.y / other.y)
        return vector2D(self.x / other, self.y / other)
    
    def __floordiv__(self, other: Union[float, 'vector2D']) -> 'vector2D':
        if isinstance(other, vector2D):
            return vector2D(self.x // other.x, self.y // other.y)
        return vector2D(self.x // other, self.y // other)
    
    def __mod__(self, other: Union[float, 'vector2D']) -> 'vector2D':
        if isinstance(other, vector2D):
            return vector2D(self.x % other.x, self.y % other.y)
        return vector2D(self.x % other, self.y % other)
    
    def __neg__(self) -> 'vector2D':
        return vector2D(-self.x, -self.y)
    
    def __eq__(self, other: 'vector2D') -> bool:
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __repr__(self) -> str:
        return f"vector2D({self.x}, {self.y})"
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __len__(self) -> float:
        return self.magnitude()
    
    def magnitude(self) -> float:
        """Calculate vector magnitude (length)."""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def magnitude_squared(self) -> float:
        """Calculate squared magnitude (faster, avoids sqrt)."""
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> 'vector2D':
        """Return normalized (unit) vector."""
        mag = self.magnitude()
        if mag < 1e-9:
            return vector2D(0, 0)
        return vector2D(self.x / mag, self.y / mag)
    
    def normalized(self) -> 'vector2D':
        """Alias for normalize()."""
        return self.normalize()
    
    def dot(self, other: 'vector2D') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'vector2D') -> float:
        """Cross product (returns scalar for 2D)."""
        return self.x * other.y - self.y * other.x
    
    def distance_to(self, other: 'vector2D') -> float:
        """Distance to another vector."""
        return (self - other).magnitude()
    
    def distance_squared_to(self, other: 'vector2D') -> float:
        """Squared distance to another vector."""
        return (self - other).magnitude_squared()
    
    def angle_to(self, other: 'vector2D') -> float:
        """Angle to another vector in radians."""
        dot = self.normalize().dot(other.normalize())
        return math.acos(max(-1.0, min(1.0, dot)))
    
    def lerp(self, other: 'vector2D', t: float) -> 'vector2D':
        """Linear interpolation."""
        return vector2D(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t
        )
    
    def reflect(self, normal: 'vector2D') -> 'vector2D':
        """Reflect vector off a normal."""
        return self - normal * (2.0 * self.dot(normal))
    
    def rotate(self, angle: float) -> 'vector2D':
        """Rotate vector by angle (radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def perpendicular(self) -> 'vector2D':
        """Get perpendicular vector."""
        return vector2D(-self.y, self.x)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)
    
    @staticmethod
    def zero() -> 'vector2D':
        """Zero vector."""
        return vector2D(0, 0)
    
    @staticmethod
    def one() -> 'vector2D':
        """Vector with all components = 1."""
        return vector2D(1, 1)
    
    @staticmethod
    def up() -> 'vector2D':
        """Up vector (0, 1)."""
        return vector2D(0, 1)
    
    @staticmethod
    def down() -> 'vector2D':
        """Down vector (0, -1)."""
        return vector2D(0, -1)
    
    @staticmethod
    def left() -> 'vector2D':
        """Left vector (-1, 0)."""
        return vector2D(-1, 0)
    
    @staticmethod
    def right() -> 'vector2D':
        """Right vector (1, 0)."""
        return vector2D(1, 0)


class vector3D:
    """3D vector class with comprehensive math operations."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other: 'vector3D') -> 'vector3D':
        return vector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'vector3D') -> 'vector3D':
        return vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other: Union[float, 'vector3D']) -> 'vector3D':
        if isinstance(other, vector3D):
            # Component-wise multiplication
            return vector3D(self.x * other.x, self.y * other.y, self.z * other.z)
        return vector3D(self.x * other, self.y * other, self.z * other)
    
    def __rmul__(self, other: float) -> 'vector3D':
        return self.__mul__(other)
    
    def __truediv__(self, other: Union[float, 'vector3D']) -> 'vector3D':
        if isinstance(other, vector3D):
            return vector3D(self.x / other.x, self.y / other.y, self.z / other.z)
        return vector3D(self.x / other, self.y / other, self.z / other)
    
    def __floordiv__(self, other: Union[float, 'vector3D']) -> 'vector3D':
        if isinstance(other, vector3D):
            return vector3D(self.x // other.x, self.y // other.y, self.z // other.z)
        return vector3D(self.x // other, self.y // other, self.z // other)
    
    def __mod__(self, other: Union[float, 'vector3D']) -> 'vector3D':
        if isinstance(other, vector3D):
            return vector3D(self.x % other.x, self.y % other.y, self.z % other.z)
        return vector3D(self.x % other, self.y % other, self.z % other)
    
    def __neg__(self) -> 'vector3D':
        return vector3D(-self.x, -self.y, -self.z)
    
    def __eq__(self, other: 'vector3D') -> bool:
        return (abs(self.x - other.x) < 1e-9 and 
                abs(self.y - other.y) < 1e-9 and 
                abs(self.z - other.z) < 1e-9)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))
    
    def __repr__(self) -> str:
        return f"vector3D({self.x}, {self.y}, {self.z})"
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"
    
    def __len__(self) -> float:
        return self.magnitude()
    
    def magnitude(self) -> float:
        """Calculate vector magnitude (length)."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    
    def magnitude_squared(self) -> float:
        """Calculate squared magnitude (faster, avoids sqrt)."""
        return self.x * self.x + self.y * self.y + self.z * self.z
    
    def normalize(self) -> 'vector3D':
        """Return normalized (unit) vector."""
        mag = self.magnitude()
        if mag < 1e-9:
            return vector3D(0, 0, 0)
        return vector3D(self.x / mag, self.y / mag, self.z / mag)
    
    def normalized(self) -> 'vector3D':
        """Alias for normalize()."""
        return self.normalize()
    
    def dot(self, other: 'vector3D') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'vector3D') -> 'vector3D':
        """Cross product."""
        return vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def distance_to(self, other: 'vector3D') -> float:
        """Distance to another vector."""
        return (self - other).magnitude()
    
    def distance_squared_to(self, other: 'vector3D') -> float:
        """Squared distance to another vector."""
        return (self - other).magnitude_squared()
    
    def angle_to(self, other: 'vector3D') -> float:
        """Angle to another vector in radians."""
        dot = self.normalize().dot(other.normalize())
        return math.acos(max(-1.0, min(1.0, dot)))
    
    def lerp(self, other: 'vector3D', t: float) -> 'vector3D':
        """Linear interpolation."""
        return vector3D(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t
        )
    
    def slerp(self, other: 'vector3D', t: float) -> 'vector3D':
        """Spherical linear interpolation."""
        # Normalize vectors
        v1 = self.normalize()
        v2 = other.normalize()
        
        dot = v1.dot(v2)
        dot = max(-1.0, min(1.0, dot))  # Clamp
        
        theta = math.acos(dot)
        if abs(theta) < 1e-9:
            return v1.lerp(v2, t)
        
        sin_theta = math.sin(theta)
        w1 = math.sin((1.0 - t) * theta) / sin_theta
        w2 = math.sin(t * theta) / sin_theta
        
        return (v1 * w1 + v2 * w2).normalize()
    
    def reflect(self, normal: 'vector3D') -> 'vector3D':
        """Reflect vector off a normal."""
        return self - normal * (2.0 * self.dot(normal))
    
    def project(self, other: 'vector3D') -> 'vector3D':
        """Project this vector onto another."""
        return other * (self.dot(other) / other.magnitude_squared())
    
    def project_on_plane(self, normal: 'vector3D') -> 'vector3D':
        """Project vector onto a plane defined by normal."""
        return self - self.project(normal)
    
    def rotate_around_axis(self, axis: 'vector3D', angle: float) -> 'vector3D':
        """Rotate vector around an axis by angle (radians)."""
        axis = axis.normalize()
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # Rodrigues' rotation formula
        return (self * cos_a + 
                axis.cross(self) * sin_a + 
                axis * axis.dot(self) * (1 - cos_a))
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)
    
    def to_list(self) -> list:
        """Convert to list."""
        return [self.x, self.y, self.z]
    
    @staticmethod
    def zero() -> 'vector3D':
        """Zero vector."""
        return vector3D(0, 0, 0)
    
    @staticmethod
    def one() -> 'vector3D':
        """Vector with all components = 1."""
        return vector3D(1, 1, 1)
    
    @staticmethod
    def up() -> 'vector3D':
        """Up vector (0, 1, 0)."""
        return vector3D(0, 1, 0)
    
    @staticmethod
    def down() -> 'vector3D':
        """Down vector (0, -1, 0)."""
        return vector3D(0, -1, 0)
    
    @staticmethod
    def forward() -> 'vector3D':
        """Forward vector (0, 0, -1)."""
        return vector3D(0, 0, -1)
    
    @staticmethod
    def back() -> 'vector3D':
        """Back vector (0, 0, 1)."""
        return vector3D(0, 0, 1)
    
    @staticmethod
    def left() -> 'vector3D':
        """Left vector (-1, 0, 0)."""
        return vector3D(-1, 0, 0)
    
    @staticmethod
    def right() -> 'vector3D':
        """Right vector (1, 0, 0)."""
        return vector3D(1, 0, 0)


class vector4D:
    """4D vector class (useful for homogeneous coordinates)."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)
    
    def __add__(self, other: 'vector4D') -> 'vector4D':
        return vector4D(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)
    
    def __sub__(self, other: 'vector4D') -> 'vector4D':
        return vector4D(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)
    
    def __mul__(self, other: Union[float, 'vector4D']) -> 'vector4D':
        if isinstance(other, vector4D):
            return vector4D(self.x * other.x, self.y * other.y, self.z * other.z, self.w * other.w)
        return vector4D(self.x * other, self.y * other, self.z * other, self.w * other)
    
    def __rmul__(self, other: float) -> 'vector4D':
        return self.__mul__(other)
    
    def __truediv__(self, other: Union[float, 'vector4D']) -> 'vector4D':
        if isinstance(other, vector4D):
            return vector4D(self.x / other.x, self.y / other.y, self.z / other.z, self.w / other.w)
        return vector4D(self.x / other, self.y / other, self.z / other, self.w / other)
    
    def __neg__(self) -> 'vector4D':
        return vector4D(-self.x, -self.y, -self.z, -self.w)
    
    def __eq__(self, other: 'vector4D') -> bool:
        return (abs(self.x - other.x) < 1e-9 and 
                abs(self.y - other.y) < 1e-9 and 
                abs(self.z - other.z) < 1e-9 and
                abs(self.w - other.w) < 1e-9)
    
    def __repr__(self) -> str:
        return f"vector4D({self.x}, {self.y}, {self.z}, {self.w})"
    
    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)
    
    def normalize(self) -> 'vector4D':
        mag = self.magnitude()
        if mag < 1e-9:
            return vector4D(0, 0, 0, 0)
        return vector4D(self.x / mag, self.y / mag, self.z / mag, self.w / mag)
    
    def dot(self, other: 'vector4D') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w
    
    def xyz(self) -> vector3D:
        """Get xyz components as vector3D."""
        return vector3D(self.x, self.y, self.z)
    
    @staticmethod
    def from_vector3D(v: vector3D, w: float = 1.0) -> 'vector4D':
        """Create from vector3D with w component."""
        return vector4D(v.x, v.y, v.z, w)
