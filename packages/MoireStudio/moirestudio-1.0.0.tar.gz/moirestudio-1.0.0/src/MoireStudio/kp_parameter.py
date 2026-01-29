"""
K·p parameter generation module.
Provides functions to extract continuum model parameters from atomistic calculations.
"""

import numpy as np
from .simple_func import reciprocal_base

__all__ = [
    "gen_mass",
    "gen_potential_one_band",
    "gen_couple_one_band",
    "gen_couple_two_band",
    "gen_hv_a",
    "gen_TBG_parameter",
    "gen_tTMD_parameter",
]


def gen_mass(mono_model, valley_pos, band_index, h: float = 0.01) -> np.ndarray:
    """
    Calculate anisotropic effective mass (m_x, m_y) from monolayer TB model at given valley.

    Equivalent to the mode=0 part of the original twist_kp_parameter.kp_parameter.effictive_mass(),
    with explicit parameters for model, valley position, and band index.

    Args:
        mono_model: Monolayer tight-binding model object with attributes:
            - mono_model._lat: Real space lattice vectors (2x2 or 3x3)
            And method:
            - mono_model.solve_all(k_points): Solve for eigenvalues at given k-points
        valley_pos: Valley position in normalized k-coordinates (fractional coordinates
                   relative to monolayer reciprocal basis) with shape (2,)
        band_index: Band index to fit (0-based)
        h: Finite difference step size in Cartesian k-space (units: 1/Å)

    Returns:
        Effective mass tensor (m_x, m_y) in units of free electron mass m_e

    Raises:
        ValueError: If valley_pos has wrong shape or band_index is out of bounds
    """
    valley_pos = np.asarray(valley_pos, dtype=float)
    if valley_pos.shape != (2,):
        raise ValueError("valley_pos must be a 1D array of length 2, e.g., [kx, ky].")

    # Extract first two real space lattice vectors and construct reciprocal basis
    lat = np.asarray(mono_model._lat, dtype=float)
    mono_lat2 = lat[:2, :2]
    mono_b_base = reciprocal_base(mono_lat2)  # shape (2, 2)

    # Convert valley position to Cartesian coordinates (Å^{-1}) and extend to 3D
    kai_xy = np.dot(valley_pos, mono_b_base)
    kai_xy3 = np.array([kai_xy[0], kai_xy[1], 0.0], dtype=float)

    # Finite difference grid with 6 points (same as original implementation)
    dis_list = np.array(
        [[-h, 0.0, 0.0],
         [0.0, 0.0, 0.0],
         [h, 0.0, 0.0],
         [0.0, -h, 0.0],
         [0.0, 0.0, 0.0],
         [0.0, h, 0.0]],
        dtype=float,
    )
    k_cart = dis_list + kai_xy3  # Cartesian coordinates

    # Convert to TB model's normalized reciprocal coordinates
    inv_b = np.linalg.inv(mono_b_base)
    k_red = k_cart.copy()
    k_red[:, :2] = np.dot(k_cart[:, :2], inv_b)

    evals = mono_model.solve_all(k_red)
    evals = np.asarray(evals, dtype=float)
    if evals.ndim != 2:
        raise ValueError("mono_model.solve_all must return array with shape (Nk, n_band).")

    if not (0 <= band_index < evals.shape[1]):
        raise ValueError(
            f"band_index={band_index} out of bounds, model has only {evals.shape[1]} bands."
        )

    e = evals[:, band_index]

    # Second derivatives ∂²E/∂k_x², ∂²E/∂k_y²
    ppE1 = (e[0] + e[2] - 2.0 * e[1]) / (h * h)
    ppE2 = (e[3] + e[5] - 2.0 * e[4]) / (h * h)

    # Same constant 7.63 as original code, units correspond to E(eV), k(Å^{-1})
    m1 = 7.63 / ppE1
    m2 = 7.63 / ppE2

    return np.array([m1, m2], dtype=float)


def _reshape_pairs(AA_band, AB_band):
    """
    Reshape AA/AB valley energy levels into [E1_top, E1_bottom, E2_top, E2_bottom, ...] format.

    Args:
        AA_band: AA-stacked energy levels
        AB_band: AB-stacked energy levels

    Returns:
        Tuple of (AA_pairs, AB_pairs) reshaped to (N_pair, 2)

    Raises:
        ValueError: If shapes don't match or array length is not even
    """
    AA = np.asarray(AA_band, dtype=float).ravel()
    AB = np.asarray(AB_band, dtype=float).ravel()

    if AA.shape != AB.shape:
        raise ValueError("AA_band and AB_band must have identical shapes.")

    if AA.size % 2 != 0:
        raise ValueError(
            "AA_band / AB_band length must be even: "
            "[E_top0, E_bottom0, E_top1, E_bottom1, ...]."
        )

    n_pair = AA.size // 2
    AA_pairs = AA.reshape(n_pair, 2)
    AB_pairs = AB.reshape(n_pair, 2)

    return AA_pairs, AB_pairs


def gen_potential_one_band(AA_band, AB_band, psi: float = np.pi / 2, phi: float = 2 * np.pi / 3) -> float:
    """
    Calculate moiré scalar potential amplitude V_use for single-band case from AA/AB valley energies.

    Corresponds to single-band part of original twist_kp_parameter.gen_parameter():
        V_use = ((E_AA_top + E_AA_bottom)/2 - (E_AB_top + E_AB_bottom)/2) /
                (2 * |cos(phi-psi) + cos(phi-psi) + cos(-2phi-psi)|)

    Args:
        AA_band: Valley energies at AA stacking for two layers: [E_layer1, E_layer2]
        AB_band: Valley energies at AB stacking for two layers: [E_layer1, E_layer2]
        psi, phi: Phases for moiré potential (usually keep defaults)

    Returns:
        Moiré scalar potential amplitude (same energy units as input)

    Raises:
        ValueError: If input is not for single band with double degeneracy
    """
    AA_pairs, AB_pairs = _reshape_pairs(AA_band, AB_band)

    if AA_pairs.shape[0] != 1:
        raise ValueError("gen_potential_one_band only for single band with double degeneracy (length 2).")

    delta_cos = (
            np.cos(phi - psi)
            + np.cos(phi - psi)
            + np.cos(-2.0 * phi - psi)
    )

    V_use = ((AA_pairs[0].mean()) - (AB_pairs[0].mean())) / (2.0 * np.abs(delta_cos))

    return V_use


def gen_couple_one_band(AA_band) -> float:
    """
    Calculate splitting parameter omega for single-band case from AA stacking valley energies.

    Corresponds to original code: omega = (E_AA_layer2 - E_AA_layer1) / 6

    Args:
        AA_band: AA-stacked valley energies for two layers: [E_layer1, E_layer2]

    Returns:
        Onsite splitting parameter omega for k·p model

    Raises:
        ValueError: If input length is not 2
    """
    AA = np.asarray(AA_band, dtype=float).ravel()

    if AA.size != 2:
        raise ValueError("gen_couple_one_band requires AA_band of length 2.")

    omega = (AA[1] - AA[0]) / 6.0

    return omega


def gen_couple_one_band_sym(band_list, dis_list, mono_b_base, sym_index: int) -> float:
    """
    Calculate coupling parameter omega for single-band case with symmetry consideration.

    Args:
        band_list: Band energy list
        dis_list: Distance list
        mono_b_base: Monolayer reciprocal basis
        sym_index: Symmetry index (2 or 3)

    Returns:
        Coupling parameter omega
    """
    if sym_index == 3:
        omega = (band_list[1] - band_list[0]) / 3
    elif sym_index == 2:
        omega = (band_list[1] - band_list[0]) / 4

    return omega


def gen_couple_two_band(AA_band, AB_band, psi: float = np.pi / 2, phi: float = 2 * np.pi / 3):
    """
    Calculate parameters for two-band (e.g., valence+conduction) k·p model from AA/AB valley energies.

    Clean rewrite of multi-band part from twist_kp_parameter.kp_parameter.gen_parameter(),
    with all I/O and band_index logic removed.

    Input format convention:
        AA_band, AB_band flattened to 1D as:
            [E_AA_valence_top,   E_AA_valence_bottom,
             E_AA_conduction_top, E_AA_conduction_bottom]

    Args:
        AA_band: Valley energies at AA stacking for both bands and layers (length 4)
        AB_band: Valley energies at AB stacking for both bands and layers (length 4)
        psi, phi: Moiré potential phases (usually keep defaults)

    Returns:
        Tuple of (gap_or_mass, omega, V_use) where:
            gap_or_mass: Effective gap between bands at AA stacking
            omega: Splitting matrix (N_pair x N_pair)
            V_use: Moiré scalar potential amplitudes for each band (length N_pair)

    Raises:
        ValueError: If insufficient pairs
    """
    AA_pairs, AB_pairs = _reshape_pairs(AA_band, AB_band)
    n_pair = AA_pairs.shape[0]

    if n_pair < 1:
        raise ValueError("At least one (top, bottom) energy level pair required.")

    delta_cos = (
            np.cos(phi - psi)
            + np.cos(phi - psi)
            + np.cos(-2.0 * phi - psi)
    )

    # Potential amplitude from average energy difference for each band
    V_use = (AA_pairs.mean(axis=1) - AB_pairs.mean(axis=1)) / (2.0 * np.abs(delta_cos))

    # Gap definition follows original: valence_top - conduction_bottom
    if n_pair >= 2:
        gap_or_mass = AA_pairs[0, 1] - AA_pairs[1, 0]
        dAA = np.abs(AA_pairs[0, 1] - AA_pairs[1, 0])
        dAB = np.abs(AB_pairs[0, 1] - AB_pairs[1, 0])
    else:
        gap_or_mass = 0.0
        dAA = dAB = 0.0

    # Build splitting matrix
    omega = np.zeros((n_pair, n_pair), dtype=float)

    for i in range(n_pair):
        # Intraband splitting
        omega[i, i] = (AA_pairs[i, 1] - AA_pairs[i, 0]) / 6.0

        # Interband splitting (same for all i≠j)
        for j in range(n_pair):
            if i != j:
                omega[i, j] = (dAA - dAB) / 3.0

    return gap_or_mass, omega, V_use


def gen_hv_a(*args, **kwargs):
    """
    Calculate Dirac velocity parameter hv_a from monolayer band structure.

    TODO: Auto-generation of hv_a not implemented in original twist_kp_parameter.py.

    Suggested implementation:
        1. Choose direction near valley_pos (e.g., along reciprocal lattice vector).
        2. Take k = K + δk, K - δk points, calculate conduction and valence band energies.
        3. Fit ΔE(k) = E_c(k) - E_v(k) ≈ 2 * (ħ v_F) * |δk|,
           get hv = ħ v_F, then hv_a = hv / a, where a is monolayer lattice constant.

    Raises:
        NotImplementedError: Function not yet implemented
    """
    raise NotImplementedError(
        "Auto-fitting of hv_a not implemented in kp_parameter.gen_hv_a, "
        "need to decide fitting scheme based on specific monolayer system (e.g., graphene)."
    )


def gen_TBG_parameter(lat_a: float, valley_idx: int, u_1: float, u_2: float):
    """
    Generate parameters for twisted bilayer graphene (TBG) continuum model.

    Args:
        lat_a: Lattice constant
        valley_idx: Valley index (+1 for K, -1 for K')
        u_1: Intra-sublattice interlayer hopping parameter
        u_2: Inter-sublattice interlayer hopping parameter

    Returns:
        Tuple of (mono_lat, valley_pos, valley_name, inter_idxs, intra_t_idxs,
                 intra_b_idxs, inter_coes, intra_t_coes, intra_b_coes)
    """
    mono_lat = lat_a * np.array([
        [1, 0],
        [1 / 2, np.sqrt(3) / 2]
    ], dtype=float)

    valley_pos = valley_idx * np.array([2 / 3, 1 / 3], dtype=float)
    valley_name = "K"

    inter_idxs = np.array([
        [0, 0],
        [-1, -1],
        [-1, 0]
    ]) * valley_idx

    omega = np.exp(valley_idx * 1.j * (2 * np.pi) / 3)
    omega_p = np.exp(-1.j * valley_idx * (2 * np.pi) / 3)

    inter_coes = np.zeros((3, 2, 2), dtype=complex)
    inter_coes[0] = np.array([
        [u_1, u_2],
        [u_2, u_1]
    ])
    inter_coes[1] = np.array([
        [u_1, u_2 * omega_p],
        [u_2 * omega, u_1]
    ])
    inter_coes[2] = np.array([
        [u_1, u_2 * omega],
        [u_2 * omega_p, u_1]
    ])

    intra_t_idxs = np.array([[0, 0]])
    intra_t_coes = np.zeros((1, 2, 2), dtype=complex)
    intra_b_idxs = np.array([[0, 0]])
    intra_b_coes = np.zeros((1, 2, 2), dtype=complex)

    return (mono_lat, valley_pos, valley_name, inter_idxs, intra_t_idxs,
            intra_b_idxs, inter_coes, intra_t_coes, intra_b_coes)


def gen_tTMD_parameter(lat_a: float, valley_idx: int, omega: float, V: float, psi: float):
    """
    Generate parameters for twisted transition metal dichalcogenide (tTMD) continuum model.

    Args:
        lat_a: Lattice constant
        valley_idx: Valley index (+1 for K, -1 for K')
        omega: Interlayer hopping parameter
        V: Intralayer potential amplitude
        psi: Phase angle in degrees

    Returns:
        Tuple of (mono_lat, valley_pos, valley_name, inter_idxs, intra_t_idxs,
                 intra_b_idxs, inter_coes, intra_t_coes, intra_b_coes)
    """
    mono_lat = lat_a * np.array([
        [1, 0],
        [1 / 2, np.sqrt(3) / 2]
    ], dtype=float)

    valley_pos = valley_idx * np.array([2 / 3, 1 / 3], dtype=float)
    valley_name = "K"

    inter_idxs = np.array([
        [0, 0],
        [-1, -1],
        [-1, 0]
    ]) * valley_idx

    inter_coes = np.array([1, 1, 1], dtype=complex) * omega

    psi_pi = psi * np.pi / 180  # Convert to radians
    pha_fac = np.exp(-1.j * psi_pi)
    pha_fac_c = np.exp(1.j * psi_pi)

    intra_t_idxs = np.array([
        [1, 0],
        [1, 1],
        [0, 1],
        [-1, 0],
        [-1, -1],
        [0, -1]
    ])

    intra_t_coes = np.array([pha_fac_c, pha_fac, pha_fac_c, pha_fac, pha_fac_c, pha_fac]) * V
    intra_b_idxs = intra_t_idxs
    intra_b_coes = intra_t_coes.conj()

    return (mono_lat, valley_pos, valley_name, inter_idxs, intra_t_idxs,
            intra_b_idxs, inter_coes, intra_t_coes, intra_b_coes)