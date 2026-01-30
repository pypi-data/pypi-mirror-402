"""
Advanced math utilities including interpolation, easing functions, and noise generation.
"""
import math
from typing import Callable, Optional
from .vectors import vector2D, vector3D


# Interpolation functions
def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, value: float) -> float:
    """Inverse linear interpolation (get t from value)."""
    if abs(b - a) < 1e-9:
        return 0.0
    return (value - a) / (b - a)


def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Remap value from one range to another."""
    t = inverse_lerp(in_min, in_max, value)
    return lerp(out_min, out_max, t)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smoothstep interpolation."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0: float, edge1: float, x: float) -> float:
    """Smootherstep interpolation (smoother than smoothstep)."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def clamp01(value: float) -> float:
    """Clamp value between 0 and 1."""
    return clamp(value, 0.0, 1.0)


# Easing functions (for animations)
def ease_in_quad(t: float) -> float:
    """Quadratic ease in."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease out."""
    return t * (2.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease in-out."""
    return 2.0 * t * t if t < 0.5 else -1.0 + (4.0 - 2.0 * t) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease out."""
    return (t - 1.0) * (t - 1.0) * (t - 1.0) + 1.0


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in-out."""
    return 4.0 * t * t * t if t < 0.5 else (t - 1.0) * (2.0 * t - 2.0) * (2.0 * t - 2.0) + 1.0


def ease_in_sine(t: float) -> float:
    """Sine ease in."""
    return 1.0 - math.cos(t * math.pi / 2.0)


def ease_out_sine(t: float) -> float:
    """Sine ease out."""
    return math.sin(t * math.pi / 2.0)


def ease_in_out_sine(t: float) -> float:
    """Sine ease in-out."""
    return -(math.cos(math.pi * t) - 1.0) / 2.0


def ease_in_expo(t: float) -> float:
    """Exponential ease in."""
    return 0.0 if t == 0.0 else math.pow(2.0, 10.0 * (t - 1.0))


def ease_out_expo(t: float) -> float:
    """Exponential ease out."""
    return 1.0 if t == 1.0 else 1.0 - math.pow(2.0, -10.0 * t)


def ease_in_out_expo(t: float) -> float:
    """Exponential ease in-out."""
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return math.pow(2.0, 20.0 * t - 10.0) / 2.0
    return (2.0 - math.pow(2.0, -20.0 * t + 10.0)) / 2.0


def ease_in_back(t: float) -> float:
    """Back ease in."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return c3 * t * t * t - c1 * t * t


def ease_out_back(t: float) -> float:
    """Back ease out."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * math.pow(t - 1.0, 3) + c1 * math.pow(t - 1.0, 2)


def ease_in_out_back(t: float) -> float:
    """Back ease in-out."""
    c1 = 1.70158
    c2 = c1 * 1.525
    
    if t < 0.5:
        return (t * t * ((c2 + 1.0) * 2.0 * t - c2)) / 2.0
    else:
        return ((2.0 * t - 2.0) * (2.0 * t - 2.0) * ((c2 + 1.0) * (t * 2.0 - 2.0) + c2) + 2.0) / 2.0


def ease_in_elastic(t: float) -> float:
    """Elastic ease in."""
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    return -math.pow(2.0, 10.0 * (t - 1.0)) * math.sin((t - 1.1) * 5.0 * math.pi)


def ease_out_elastic(t: float) -> float:
    """Elastic ease out."""
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    return math.pow(2.0, -10.0 * t) * math.sin((t - 0.1) * 5.0 * math.pi) + 1.0


def ease_bounce(t: float) -> float:
    """Bounce ease out."""
    if t < 1.0 / 2.75:
        return 7.5625 * t * t
    elif t < 2.0 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


# Noise functions (simplified Perlin-like noise)
def hash_float(x: float) -> float:
    """Simple hash function for noise."""
    return math.sin(x * 12.9898) * 43758.5453


def noise_1d(x: float) -> float:
    """1D noise function."""
    i = math.floor(x)
    f = x - i
    u = f * f * (3.0 - 2.0 * f)
    
    a = hash_float(i)
    b = hash_float(i + 1.0)
    
    return lerp(a % 1.0, b % 1.0, u)


def noise_2d(x: float, y: float) -> float:
    """2D noise function."""
    i = math.floor(x)
    j = math.floor(y)
    fx = x - i
    fy = y - j
    
    u = fx * fx * (3.0 - 2.0 * fx)
    v = fy * fy * (3.0 - 2.0 * fy)
    
    a = hash_float(i + j * 57.0) % 1.0
    b = hash_float((i + 1.0) + j * 57.0) % 1.0
    c = hash_float(i + (j + 1.0) * 57.0) % 1.0
    d = hash_float((i + 1.0) + (j + 1.0) * 57.0) % 1.0
    
    return lerp(lerp(a, b, u), lerp(c, d, u), v)


def noise_3d(x: float, y: float, z: float) -> float:
    """3D noise function."""
    i = math.floor(x)
    j = math.floor(y)
    k = math.floor(z)
    fx = x - i
    fy = y - j
    fz = z - k
    
    u = fx * fx * (3.0 - 2.0 * fx)
    v = fy * fy * (3.0 - 2.0 * fy)
    w = fz * fz * (3.0 - 2.0 * fz)
    
    # Hash 8 corners
    corners = []
    for di in range(2):
        for dj in range(2):
            for dk in range(2):
                corners.append(hash_float((i + di) + (j + dj) * 57.0 + (k + dk) * 131.0) % 1.0)
    
    # Trilinear interpolation
    c00 = lerp(corners[0], corners[1], u)
    c01 = lerp(corners[2], corners[3], u)
    c10 = lerp(corners[4], corners[5], u)
    c11 = lerp(corners[6], corners[7], u)
    
    c0 = lerp(c00, c10, v)
    c1 = lerp(c01, c11, v)
    
    return lerp(c0, c1, w)


def fbm_1d(x: float, octaves: int = 4, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """1D fractional Brownian motion (fractal noise)."""
    value = 0.0
    amplitude = 0.5
    frequency = 1.0
    
    for _ in range(octaves):
        value += amplitude * noise_1d(x * frequency)
        frequency *= lacunarity
        amplitude *= gain
    
    return value


def fbm_2d(x: float, y: float, octaves: int = 4, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """2D fractional Brownian motion."""
    value = 0.0
    amplitude = 0.5
    frequency = 1.0
    
    for _ in range(octaves):
        value += amplitude * noise_2d(x * frequency, y * frequency)
        frequency *= lacunarity
        amplitude *= gain
    
    return value


def fbm_3d(x: float, y: float, z: float, octaves: int = 4, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """3D fractional Brownian motion."""
    value = 0.0
    amplitude = 0.5
    frequency = 1.0
    
    for _ in range(octaves):
        value += amplitude * noise_3d(x * frequency, y * frequency, z * frequency)
        frequency *= lacunarity
        amplitude *= gain
    
    return value


# Bezier curves
def bezier_quadratic(t: float, p0: float, p1: float, p2: float) -> float:
    """Quadratic Bezier curve."""
    u = 1.0 - t
    return u * u * p0 + 2.0 * u * t * p1 + t * t * p2


def bezier_cubic(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Cubic Bezier curve."""
    u = 1.0 - t
    uu = u * u
    uuu = uu * u
    tt = t * t
    ttt = tt * t
    return uuu * p0 + 3.0 * uu * t * p1 + 3.0 * u * tt * p2 + ttt * p3


def bezier_quadratic_vec(t: float, p0: vector2D, p1: vector2D, p2: vector2D) -> vector2D:
    """Quadratic Bezier curve for 2D vectors."""
    u = 1.0 - t
    return p0 * (u * u) + p1 * (2.0 * u * t) + p2 * (t * t)


def bezier_cubic_vec(t: float, p0: vector2D, p1: vector2D, p2: vector2D, p3: vector2D) -> vector2D:
    """Cubic Bezier curve for 2D vectors."""
    u = 1.0 - t
    uu = u * u
    uuu = uu * u
    tt = t * t
    ttt = tt * t
    return p0 * uuu + p1 * (3.0 * uu * t) + p2 * (3.0 * u * tt) + p3 * ttt


# Catmull-Rom splines
def catmull_rom(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Catmull-Rom spline interpolation."""
    t2 = t * t
    t3 = t2 * t
    
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )


def catmull_rom_vec(t: float, p0: vector2D, p1: vector2D, p2: vector2D, p3: vector2D) -> vector2D:
    """Catmull-Rom spline for 2D vectors."""
    t2 = t * t
    t3 = t2 * t
    
    return (p1 * 2.0 +
            (p2 - p0) * t +
            (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2 +
            (-p0 + p1 * 3.0 - p2 * 3.0 + p3) * t3) * 0.5

