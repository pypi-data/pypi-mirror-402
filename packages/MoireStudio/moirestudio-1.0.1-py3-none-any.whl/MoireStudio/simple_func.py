"""
Basic mathematical functions for lattice and geometry operations.
Provides utilities for rotations, reciprocal lattice calculations, and mesh generation.
"""

import numpy as np


def R_theta(theta: float) -> np.ndarray:
    """
    Generate 2D rotation matrix for given angle.

    Args:
        theta: Rotation angle in radians

    Returns:
        2x2 rotation matrix
    """
    R_use = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])
    return R_use


def linearly_dependent(v1, v2, if_sign: bool = False, accurate: float = 1e-3):
    """
    Check if two 2D vectors are collinear (optimized version).

    Mathematical principle:
        2D vectors are collinear ⇔ cross product is zero (v1[0]*v2[1] - v2[0]*v1[1] ≈ 0)
        Zero vector is collinear with any vector.

    Args:
        v1, v2: 2D vectors (list/tuple/numpy array supported)
        if_sign: Whether to return sign (valid when collinear, sign of k in v1 = k*v2)
        accurate: Floating-point precision threshold (default: 1e-3)

    Returns:
        If if_sign=False: Boolean (whether collinear)
        If if_sign=True: Tuple (is_collinear, sign) (sign is None when not collinear)

    Raises:
        ValueError: If vectors are not 2D
    """
    # Convert to numpy arrays for element-wise operations
    v1 = np.asarray(v1, dtype=np.float64)
    v2 = np.asarray(v2, dtype=np.float64)

    # Validate vector dimensions (must be 2D)
    if v1.shape != (2,) or v2.shape != (2,):
        raise ValueError("Only 2D vectors are supported")

    # Check if either vector is zero (all components < accurate)
    is_v1_zero = np.all(np.abs(v1) < accurate)
    is_v2_zero = np.all(np.abs(v2) < accurate)

    # Core: cross product check for collinearity (avoid division by zero)
    cross_product = v1[0] * v2[1] - v2[0] * v1[1]
    is_collinear = np.abs(cross_product) < accurate

    # Handle sign (only valid when collinear and not both zero vectors)
    out_sign = None
    if is_collinear and if_sign:
        if is_v2_zero:
            # v2 is zero vector: if v1 is also zero, sign=0; otherwise sign meaningless (set to 0)
            out_sign = 0
        else:
            # Find non-zero component in v2 to calculate ratio sign (avoid division by zero)
            if np.abs(v2[0]) >= accurate:
                ratio = v1[0] / v2[0]
            else:
                ratio = v1[1] / v2[1]
            out_sign = np.sign(ratio)

    return (is_collinear, out_sign) if if_sign else is_collinear


def reciprocal_base(Lm: np.ndarray) -> np.ndarray:
    """
    Calculate reciprocal lattice basis vectors from real space lattice.

    Args:
        Lm: Real space lattice vectors (at least 2x2, uses first 2x2 submatrix)

    Returns:
        2x2 reciprocal lattice basis vectors
    """
    Lm = Lm[0:2, 0:2]
    b_base = np.zeros((2, 2), dtype=float)

    # Calculate reciprocal basis vectors using rotation by π/2
    b_base[0] = 2 * np.pi * np.dot(R_theta(np.pi / 2), Lm[1]) / np.dot(Lm[0], np.dot(R_theta(np.pi / 2), Lm[1]))
    b_base[1] = 2 * np.pi * np.dot(R_theta(np.pi / 2), Lm[0]) / np.dot(Lm[1], np.dot(R_theta(np.pi / 2), Lm[0]))

    return b_base


def from_base_to_lat(b_base: np.ndarray) -> np.ndarray:
    """
    Convert reciprocal lattice basis to real space lattice basis.

    Args:
        b_base: Reciprocal lattice basis vectors (2x2)

    Returns:
        2x2 real space lattice vectors
    """
    coe = -b_base[0, 1] * b_base[1, 0] + b_base[0, 0] * b_base[1, 1]
    lat = np.zeros((2, 2), dtype=float)

    lat[0, 0] = 2 * np.pi * b_base[1, 1] / coe
    lat[0, 1] = -2 * np.pi * b_base[1, 0] / coe
    lat[1, 0] = -2 * np.pi * b_base[0, 1] / coe
    lat[1, 1] = 2 * np.pi * b_base[0, 0] / coe

    return lat


def gen_k_mesh(n: int, if_edge: bool = False) -> np.ndarray:
    """
    Generate a uniform k-mesh in 2D Brillouin zone.

    Args:
        n: Number of points along each dimension
        if_edge: If True, include endpoint at 1; if False, exclude endpoint

    Returns:
        Array of k-points with shape (n*n, 2) in fractional coordinates
    """
    k_mesh = np.zeros((n * n, 2), dtype=float)
    iii = 0
    use_list = np.linspace(0, 1, n + (not if_edge))

    for i in range(n):
        for j in range(n):
            k_mesh[iii, 0] = use_list[i]
            k_mesh[iii, 1] = use_list[j]
            iii = iii + 1

    return k_mesh


def get_perpendicular_unit_vector(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Get two perpendicular unit vectors to a given 2D vector.

    Args:
        v: Input 2D vector

    Returns:
        Tuple of (clockwise_perpendicular_unit_vector, counterclockwise_perpendicular_unit_vector)

    Raises:
        ValueError: If input vector has zero norm
    """
    norm_v = np.linalg.norm(v)
    if norm_v < 1e-10:  # Avoid floating-point precision issues
        raise ValueError("Input vector has zero norm, cannot compute perpendicular unit vectors")

    # Calculate two perpendicular vectors
    v_perp_clockwise = np.array([v[1], -v[0]])  # Clockwise perpendicular
    v_perp_counterclock = np.array([-v[1], v[0]])  # Counterclockwise perpendicular

    # Normalize to unit vectors
    v_perp_clockwise_unit = v_perp_clockwise / norm_v
    v_perp_counterclock_unit = v_perp_counterclock / norm_v

    return v_perp_clockwise_unit, v_perp_counterclock_unit