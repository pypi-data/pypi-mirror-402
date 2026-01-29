"""
Tight-binding parameter generation and manipulation module.

This module provides functionality for generating tight-binding parameters
from bilayer structures, including interlayer coupling calculations,
distance matrix generation, and parameter fitting.
"""

import numpy as np
from pathlib import Path
from .read_tb_model import *


def _arrays_equal(arrays):
    """
    Check if multiple ndarrays have identical shapes, dimensions, and values.

    Parameters
    ----------
    arrays : tuple of numpy.ndarray
        Arbitrary number of ndarrays to compare.

    Returns
    -------
    bool
        True if all arrays have identical shapes, dimensions, and values,
        False otherwise.

    Notes
    -----
    - Returns True if fewer than 2 arrays are provided.
    - Type checking ensures all inputs are numpy.ndarray instances.
    - Comparison includes shape, dimension, and element-wise equality.
    """
    # Return True for empty or single array cases
    if len(arrays) <= 1:
        return True

    # Use first array as reference
    first_array = arrays[0]

    # Compare each subsequent array against the reference
    for array in arrays[1:]:
        # Type validation
        if not isinstance(array, np.ndarray):
            return False

        # Dimension comparison
        if array.ndim != first_array.ndim:
            return False

        # Shape comparison
        if array.shape != first_array.shape:
            return False

        # Element-wise value comparison
        if not np.array_equal(array, first_array):
            return False

    return True


def t_inter(h0, d0, R, ie=2):
    """
    Calculate interlayer coupling based on Gaussian-like spatial decay.

    Parameters
    ----------
    h0 : float or complex
        Reference coupling amplitude at optimal stacking.
    d0 : float
        Optimal interlayer separation for maximum coupling.
    R : array_like
        Relative displacement vector (3 components: [x, y, z]).

    Returns
    -------
    float or complex
        Interlayer coupling value at displacement R.

    Notes
    -----
    The coupling decays as:
        t = h0 * exp(-sign(dz) * (dz)^2 / r0^2) * exp(-(x^2 + y^2) / r0^2)
    where dz = |R[2]| - d0, r0 = 2.0 (fixed decay length).
    The sign ensures different decay behavior for compressions vs separations.
    """
    R = np.abs(R)
    r0 = 2.0  # Fixed decay length
    dz = R[2] - d0

    # Determine sign based on compression/expansion
    sign = 1 if dz >= 0 else -1

    # Gaussian decay formula
    t = h0 * np.exp((-sign * dz ** ie) / r0 ** ie) * \
        np.exp(-(R[0] ** 2 + R[1] ** 2) / r0 ** 2)

    return t


def gen_R_list(t_model, b_model):
    """
    Generate displacement matrix between orbitals of two monolayer models.

    Parameters
    ----------
    t_model : TBModel
        Top layer tight-binding model.
    b_model : TBModel
        Bottom layer tight-binding model.

    Returns
    -------
    numpy.ndarray
        3D array of shape (n_t, n_b, 3) where:
        - n_t: number of orbitals in top layer
        - n_b: number of orbitals in bottom layer
        - 3: x, y, z displacement components (t_orb - b_orb)

    Notes
    -----
    Displacements are calculated in Cartesian coordinates by transforming
    orbital positions via the respective lattice vectors.
    """
    t_num = len(t_model._orb) * t_model._nspin
    b_num = len(b_model._orb) * b_model._nspin

    # Transform orbital positions to Cartesian coordinates
    t_xy_orb = np.dot(t_model._orb, t_model._lat)
    b_xy_orb = np.dot(b_model._orb, b_model._lat)
    if  t_model._nspin == 2:
        t_xy_orb = np.vstack((t_xy_orb, t_xy_orb))
        b_xy_orb = np.vstack((b_xy_orb, b_xy_orb))

    # Initialize displacement array
    dis_arr = np.zeros((t_num, b_num, 3), dtype=float)

    # Calculate all pairwise displacements
    for i in range(t_num):
        for j in range(b_num):
            dis_arr[i, j] = t_xy_orb[i] - b_xy_orb[j]

    return dis_arr


def fit_r0(h0_list, R_list, d0_list):
    """
    Fit decay length r0 from interlayer coupling data.

    Parameters
    ----------
    h0_list : array_like
        Interlayer coupling values for different stacking configurations.
        Shape: (n_structures,) (can be complex).
    R_list : array_like
        Relative displacement vectors for each configuration.
        Shape: (n_structures, 3).
    d0_list : array_like
        Interlayer separations for each configuration.
        Shape: (n_structures,).

    Returns
    -------
    float
        Fitted decay length r0 (default 2.0 if insufficient data).

    Raises
    ------
    ValueError
        If R_list doesn't have shape (n_structures, 3).

    Notes
    -----
    Fitting model assumes exponential decay:
        |t(R)| ~ |h_ref| * exp(-((|Rz| - d0_ref)^2 + Rx^2 + Ry^2) / r0^2)
    where h_ref and d0_ref are taken from the configuration with maximum |h0|.

    The fitting uses linear regression on log-transformed amplitude ratios
    after filtering low-quality data points.
    """
    h0_arr = np.asarray(h0_list, dtype=np.complex128).ravel()
    R_arr = np.asarray(R_list, dtype=float)
    d0_arr = np.asarray(d0_list, dtype=float).ravel()

    # Basic validation
    if h0_arr.size == 0:
        return 2.0  # Default value for empty data

    if R_arr.ndim != 2 or R_arr.shape[1] != 3:
        raise ValueError("R_list must have shape (n_structures, 3)")

    abs_h = np.abs(h0_arr)

    # Filter near-zero couplings
    mask_nonzero = abs_h > 1e-3
    if np.count_nonzero(mask_nonzero) <= 1:
        return 2.0  # Insufficient data

    abs_h = abs_h[mask_nonzero]
    R_arr = R_arr[mask_nonzero]
    d0_arr = d0_arr[mask_nonzero]

    # Reference configuration (maximum coupling)
    ref_idx = np.argmax(abs_h)
    h_ref = abs_h[ref_idx]
    d0_ref = d0_arr[ref_idx]

    # Calculate geometric distance metric
    Rx = R_arr[:, 0]
    Ry = R_arr[:, 1]
    Rz_abs = np.abs(R_arr[:, 2])  # Consistent with t_inter's R = np.abs(R)
    d1 = Rz_abs - d0_ref
    beta = d1 * d1 + Rx * Rx + Ry * Ry

    # Amplitude ratios for fitting
    ratio = abs_h / h_ref

    # Select valid fitting points
    mask = (beta > 1e-8) & (ratio > 0.0) & (ratio < 1.0)
    if np.count_nonzero(mask) < 2:
        return 2.0  # Too few points for fitting

    beta_use = beta[mask]
    ratio_use = ratio[mask]
    y = -np.log(ratio_use)  # Linear relationship: y ~ beta / r0^2

    # Filter numerically unstable points
    mask2 = y > 1e-8
    if np.count_nonzero(mask2) < 2:
        return 2.0

    beta_use = beta_use[mask2]
    y = y[mask2]

    # Least squares fitting: beta ≈ r0^2 * y
    num = np.sum(beta_use * y)
    den = np.sum(y * y)

    if den <= 0 or num <= 0:
        # Fallback estimation for degenerate cases
        r0_sq = np.sum(beta_use) / np.sum(y)
    else:
        r0_sq = num / den

    # Validate and return result
    if (not np.isfinite(r0_sq)) or (r0_sq <= 0):
        return 2.0
    if float(np.sqrt(r0_sq)) > 4 :
        return 2.0

    return float(np.sqrt(r0_sq))


def gen_tb_parameter(number, in_dir, prefix, ihetero=False):
    """
    Generate tight-binding parameters from multiple bilayer calculations.

    Parameters
    ----------
    number : int
        Number of bilayer structures to process.
    in_dir : str or Path
        Directory containing bilayer structure files.
    prefix : str
        Prefix for Wannier function files.
    ihetero : bool, optional
        Flag for heterostructure processing (currently not fully implemented).

    Returns
    -------
    tuple
        (out_mono_t, out_mono_b, out_h0, out_d0, out_r0) where:
        - out_mono_t: TBModel for top monolayer
        - out_mono_b: TBModel for bottom monolayer
        - out_h0: Reference coupling matrix (complex)
        - out_d0: Optimal interlayer separation matrix (float)
        - out_r0: Decay length matrix (float)

    Raises
    ------
    Exception
        If atomic arrangements are inconsistent across structures.

    Notes
    -----
    Processes multiple bilayer structures to extract:
    1. Reference monolayer models (from first structure)
    2. Optimal coupling parameters (h0, d0) for each orbital pair
    3. Fitted decay lengths (r0) for spatial dependence

    For heterostructures (ihetero=True), additional processing may be needed
    but current implementation requires further development.
    """
    all_atom_list = []
    all_h0 = []
    all_d0 = []
    all_R = []
    mono_t, mono_b = None, None
    out_mono_t, out_mono_b = None, None

    # Process each bilayer structure
    for i in range(1, number + 1):
        # Read Fermi energy
        efpath = Path(str(in_dir) + "/FERMI_ENERGY_" + str(i))
        ef = read_fermi_energy(efpath)

        # Read bilayer model
        wpref = prefix + "_" + str(i)
        bilayer_model = read_mono(in_dir, wpref, fermi_energy=ef)

        # Process atomic ranges
        atom_range_list = gen_atom_range_list(bilayer_model)
        bilayer_model.change_range(atom_range_list)

        # Split into monolayers and extract parameters
        mono_t, mono_b, h0, d0 = devide2mono(bilayer_model)
        use_R_list = gen_R_list(mono_t, mono_b)

        # Store data
        all_R.append(use_R_list)
        all_atom_list.append(bilayer_model._atom_list)
        all_h0.append(h0)
        all_d0.append(d0)

        # Store first structure's models as reference
        if i == 1:
            out_mono_t, out_mono_b = mono_t, mono_b

        # Handle potential layer interchange for certain structures
        if np.abs(np.linalg.norm(mono_t._atom_position[0, 0:2] -
                                 mono_b._atom_position[0, 0:2])) > 1e-3:
            # Re-read and process with layer interchange
            ef = read_fermi_energy(efpath)
            bilayer_model = read_mono(in_dir, wpref, fermi_energy=ef)
            atom_range_list = gen_atom_range_list(bilayer_model,
                                                  layer_inerchange=True)
            bilayer_model.change_range(atom_range_list)
            mono_b, mono_t, h0, d0 = devide2mono(bilayer_model)
            use_R_list = gen_R_list(mono_t, mono_b)

            # Append alternate configuration data
            all_R.append(use_R_list)
            all_atom_list.append(bilayer_model._atom_list)
            all_h0.append(h0)
            all_d0.append(d0)

    # Convert to numpy arrays
    all_R = np.array(all_R)
    all_h0 = np.array(all_h0)
    all_d0 = np.array(all_d0)

    # Validate atomic arrangement consistency
    if not _arrays_equal(all_atom_list):
        raise Exception("Error: Atomic arrangement sequence must be consistent across bilayer structures")

    # Initialize output matrices
    all_abs_h0 = np.abs(all_h0)
    orb_num = all_h0.shape[1]

    out_h0 = np.zeros((orb_num, orb_num), dtype=complex)
    out_d0 = np.zeros((orb_num, orb_num), dtype=float)
    out_r0 = np.zeros((orb_num, orb_num), dtype=float)

    # Fit parameters for each orbital pair
    for i in range(orb_num):
        for j in range(orb_num):
            use_h0_list = all_h0[:, i, j]
            use_d0_list = all_d0[:, i, j]
            use_abs_list = all_abs_h0[:, i, j]
            use_R_list = all_R[:, i, j]

            # Identify optimal stacking configuration
            stack_con_max_id = np.argmax(use_abs_list)
            out_h0[i, j] = use_h0_list[stack_con_max_id]
            out_d0[i, j] = use_d0_list[stack_con_max_id]

            # Fit decay length
            out_r0[i, j] = fit_r0(use_h0_list, use_R_list, use_d0_list)

    return out_mono_t, out_mono_b, out_h0, out_d0, out_r0