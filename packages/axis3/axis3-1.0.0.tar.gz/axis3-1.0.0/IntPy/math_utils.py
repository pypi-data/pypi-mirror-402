"""
Basic math utilities and constants.
"""
import math
from typing import Tuple


# Constants
PI = math.pi
TAU = 2.0 * math.pi
E = math.e
EPSILON = 1e-9
DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * DEG2RAD


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * RAD2DEG


def sign(value: float) -> float:
    """Get sign of value (-1, 0, or 1)."""
    if value < 0:
        return -1.0
    elif value > 0:
        return 1.0
    return 0.0


def abs_value(value: float) -> float:
    """Absolute value."""
    return math.fabs(value)


def floor(value: float) -> float:
    """Floor value."""
    return math.floor(value)


def ceil(value: float) -> float:
    """Ceiling value."""
    return math.ceil(value)


def round_value(value: float) -> float:
    """Round value."""
    return round(value)


def min_value(a: float, b: float) -> float:
    """Minimum of two values."""
    return min(a, b)


def max_value(a: float, b: float) -> float:
    """Maximum of two values."""
    return max(a, b)


def sqrt(value: float) -> float:
    """Square root."""
    return math.sqrt(value)


def pow_util(base: float, exponent: float) -> float:
    """Power function."""
    return math.pow(base, exponent)


def exp(value: float) -> float:
    """Exponential function."""
    return math.exp(value)


def log(value: float, base: float = math.e) -> float:
    """Logarithm."""
    if base == math.e:
        return math.log(value)
    return math.log(value, base)


def log10(value: float) -> float:
    """Base-10 logarithm."""
    return math.log10(value)


def sin(angle: float) -> float:
    """Sine."""
    return math.sin(angle)


def cos(angle: float) -> float:
    """Cosine."""
    return math.cos(angle)


def tan(angle: float) -> float:
    """Tangent."""
    return math.tan(angle)


def asin(value: float) -> float:
    """Arc sine."""
    return math.asin(value)


def acos(value: float) -> float:
    """Arc cosine."""
    return math.acos(value)


def atan(value: float) -> float:
    """Arc tangent."""
    return math.atan(value)


def atan2(y: float, x: float) -> float:
    """Arc tangent of y/x."""
    return math.atan2(y, x)


def sinh(value: float) -> float:
    """Hyperbolic sine."""
    return math.sinh(value)


def cosh(value: float) -> float:
    """Hyperbolic cosine."""
    return math.cosh(value)


def tanh(value: float) -> float:
    """Hyperbolic tangent."""
    return math.tanh(value)


def is_close(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    """Check if two floats are approximately equal."""
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def is_zero(value: float, epsilon: float = EPSILON) -> bool:
    """Check if value is approximately zero."""
    return abs(value) < epsilon


def wrap_angle(angle: float) -> float:
    """Wrap angle to [-PI, PI]."""
    while angle > math.pi:
        angle -= TAU
    while angle < -math.pi:
        angle += TAU
    return angle


def normalize_angle(angle: float) -> float:
    """Normalize angle to [0, 2*PI]."""
    while angle < 0:
        angle += TAU
    while angle >= TAU:
        angle -= TAU
    return angle


def lerp_angle(a: float, b: float, t: float) -> float:
    """Linear interpolation of angles (handles wraparound)."""
    # Normalize angles
    a = normalize_angle(a)
    b = normalize_angle(b)
    
    # Find shortest path
    diff = b - a
    if diff > math.pi:
        diff -= TAU
    elif diff < -math.pi:
        diff += TAU
    
    return normalize_angle(a + diff * t)


def delta_angle(current: float, target: float) -> float:
    """Calculate shortest angle difference between two angles."""
    diff = target - current
    while diff > math.pi:
        diff -= TAU
    while diff < -math.pi:
        diff += TAU
    return diff


def ping_pong(t: float, length: float) -> float:
    """Ping-pong value between 0 and length."""
    t = t % (length * 2.0)
    return length - abs(t - length)


def repeat(t: float, length: float) -> float:
    """Repeat value in range [0, length)."""
    return t % length


def ping_pong_repeat(t: float, length: float) -> float:
    """Ping-pong repeat value."""
    return ping_pong(t, length)


def move_towards(current: float, target: float, max_delta: float) -> float:
    """Move value towards target by max_delta."""
    if abs(target - current) <= max_delta:
        return target
    return current + sign(target - current) * max_delta


def smooth_damp(
    current: float, target: float,
    current_velocity: float, smooth_time: float,
    max_speed: float = float('inf'), delta_time: float = 0.016
) -> Tuple[float, float]:
    """
    Smoothly damp value towards target.
    
    Returns:
        (new_value, new_velocity)
    """
    smooth_time = max(0.0001, smooth_time)
    omega = 2.0 / smooth_time
    
    x = omega * delta_time
    exp_val = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    
    change = current - target
    original_target = target
    
    max_change = max_speed * smooth_time
    change = max(-max_change, min(max_change, change))
    target = current - change
    
    temp = (current_velocity + omega * change) * delta_time
    current_velocity = (current_velocity - omega * temp) * exp_val
    output = target + (change + temp) * exp_val
    
    if (original_target - current > 0.0) == (output > original_target):
        output = original_target
        current_velocity = (output - original_target) / delta_time
    
    return (output, current_velocity)


def next_power_of_two(value: int) -> int:
    """Get next power of two greater than or equal to value."""
    if value <= 0:
        return 1
    value -= 1
    value |= value >> 1
    value |= value >> 2
    value |= value >> 4
    value |= value >> 8
    value |= value >> 16
    return value + 1


def is_power_of_two(value: int) -> bool:
    """Check if value is a power of two."""
    return value > 0 and (value & (value - 1)) == 0


def factorial(n: int) -> int:
    """Calculate factorial."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def binomial_coefficient(n: int, k: int) -> int:
    """Calculate binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    
    # Use symmetry
    k = min(k, n - k)
    
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    
    return result


def gcd(a: int, b: int) -> int:
    """Greatest common divisor."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """Least common multiple."""
    return abs(a * b) // gcd(a, b) if a != 0 and b != 0 else 0

