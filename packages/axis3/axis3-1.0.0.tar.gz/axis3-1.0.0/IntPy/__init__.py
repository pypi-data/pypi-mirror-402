"""
IntPy - Comprehensive math library for Core.

IntPy provides all the mathematical foundations for the engine including:
- Vector math (2D, 3D, 4D)
- Matrix math (2x2, 3x3, 4x4)
- Quaternion math for rotations
- Geometry primitives (lines, planes, spheres, boxes, rays)
- 3D math utilities (intersections, distances, transformations)
- Advanced math (interpolation, easing, noise)
- Basic math utilities and constants
"""

# Vectors
from .vectors import vector2D, vector3D, vector4D

# Matrices
from .matrices import Matrix2x2, Matrix3x3, Matrix4x4

# Quaternions
from .quaternion import Quaternion

# Geometry
from .geometry import (
    Ray2D, Ray3D,
    Line2D, Line3D,
    Plane,
    Sphere,
    AABB,
    Frustum,
    ray_plane_intersection,
    ray_sphere_intersection,
    ray_aabb_intersection
)

# 3D Math
from .math3d import (
    distance_point_to_line,
    distance_point_to_plane,
    project_point_on_plane,
    reflect_vector,
    refract_vector,
    barycentric_coordinates,
    point_in_triangle,
    triangle_area,
    triangle_normal,
    closest_point_on_line,
    closest_point_on_plane,
    closest_points_between_lines,
    transform_point,
    transform_direction,
    decompose_matrix,
    screen_to_world_ray,
    calculate_tangent_space
)

# Advanced Math
from .advanced_math import (
    lerp,
    inverse_lerp,
    remap,
    smoothstep,
    smootherstep,
    clamp,
    clamp01,
    ease_in_quad,
    ease_out_quad,
    ease_in_out_quad,
    ease_in_cubic,
    ease_out_cubic,
    ease_in_out_cubic,
    ease_in_sine,
    ease_out_sine,
    ease_in_out_sine,
    ease_in_expo,
    ease_out_expo,
    ease_in_out_expo,
    ease_in_back,
    ease_out_back,
    ease_in_out_back,
    ease_in_elastic,
    ease_out_elastic,
    ease_bounce,
    noise_1d,
    noise_2d,
    noise_3d,
    fbm_1d,
    fbm_2d,
    fbm_3d,
    bezier_quadratic,
    bezier_cubic,
    bezier_quadratic_vec,
    bezier_cubic_vec,
    catmull_rom,
    catmull_rom_vec
)

# Math Utils
from .math_utils import (
    PI,
    TAU,
    E,
    EPSILON,
    DEG2RAD,
    RAD2DEG,
    degrees_to_radians,
    radians_to_degrees,
    sign,
    abs_value,
    floor,
    ceil,
    round_value,
    min_value,
    max_value,
    sqrt,
    pow_util,
    exp,
    log,
    log10,
    sin,
    cos,
    tan,
    asin,
    acos,
    atan,
    atan2,
    sinh,
    cosh,
    tanh,
    is_close,
    is_zero,
    wrap_angle,
    normalize_angle,
    lerp_angle,
    delta_angle,
    ping_pong,
    repeat,
    ping_pong_repeat,
    move_towards,
    smooth_damp,
    next_power_of_two,
    is_power_of_two,
    factorial,
    binomial_coefficient,
    gcd,
    lcm
)

__all__ = [
    # Vectors
    'vector2D',
    'vector3D',
    'vector4D',
    
    # Matrices
    'Matrix2x2',
    'Matrix3x3',
    'Matrix4x4',
    
    # Quaternions
    'Quaternion',
    
    # Geometry
    'Ray2D',
    'Ray3D',
    'Line2D',
    'Line3D',
    'Plane',
    'Sphere',
    'AABB',
    'Frustum',
    'ray_plane_intersection',
    'ray_sphere_intersection',
    'ray_aabb_intersection',
    
    # 3D Math
    'distance_point_to_line',
    'distance_point_to_plane',
    'project_point_on_plane',
    'reflect_vector',
    'refract_vector',
    'barycentric_coordinates',
    'point_in_triangle',
    'triangle_area',
    'triangle_normal',
    'closest_point_on_line',
    'closest_point_on_plane',
    'closest_points_between_lines',
    'transform_point',
    'transform_direction',
    'decompose_matrix',
    'screen_to_world_ray',
    'calculate_tangent_space',
    
    # Advanced Math
    'lerp',
    'inverse_lerp',
    'remap',
    'smoothstep',
    'smootherstep',
    'clamp',
    'clamp01',
    'ease_in_quad',
    'ease_out_quad',
    'ease_in_out_quad',
    'ease_in_cubic',
    'ease_out_cubic',
    'ease_in_out_cubic',
    'ease_in_sine',
    'ease_out_sine',
    'ease_in_out_sine',
    'ease_in_expo',
    'ease_out_expo',
    'ease_in_out_expo',
    'ease_in_back',
    'ease_out_back',
    'ease_in_out_back',
    'ease_in_elastic',
    'ease_out_elastic',
    'ease_bounce',
    'noise_1d',
    'noise_2d',
    'noise_3d',
    'fbm_1d',
    'fbm_2d',
    'fbm_3d',
    'bezier_quadratic',
    'bezier_cubic',
    'bezier_quadratic_vec',
    'bezier_cubic_vec',
    'catmull_rom',
    'catmull_rom_vec',
    
    # Math Utils
    'PI',
    'TAU',
    'E',
    'EPSILON',
    'DEG2RAD',
    'RAD2DEG',
    'degrees_to_radians',
    'radians_to_degrees',
    'sign',
    'abs_value',
    'floor',
    'ceil',
    'round_value',
    'min_value',
    'max_value',
    'sqrt',
    'pow_util',
    'exp',
    'log',
    'log10',
    'sin',
    'cos',
    'tan',
    'asin',
    'acos',
    'atan',
    'atan2',
    'sinh',
    'cosh',
    'tanh',
    'is_close',
    'is_zero',
    'wrap_angle',
    'normalize_angle',
    'lerp_angle',
    'delta_angle',
    'ping_pong',
    'repeat',
    'ping_pong_repeat',
    'move_towards',
    'smooth_damp',
    'next_power_of_two',
    'is_power_of_two',
    'factorial',
    'binomial_coefficient',
    'gcd',
    'lcm',
]

__version__ = '1.0.0'

