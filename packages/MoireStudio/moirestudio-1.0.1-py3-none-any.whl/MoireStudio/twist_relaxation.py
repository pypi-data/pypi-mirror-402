"""
Twist relaxation module for moiré superlattice calculations.
Provides functionality for geometric relaxation and k-space perturbation.
"""

import numpy as np
from .simple_func import reciprocal_base, get_perpendicular_unit_vector


def factorial_recursive(n: int) -> int:
    """
    Compute factorial of a non-negative integer using recursion.

    Args:
        n: Non-negative integer

    Returns:
        Factorial of n

    Raises:
        ValueError: If n is negative or non-integer
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Factorial is only defined for non-negative integers")

    # Base cases: 0! = 1! = 1
    if n <= 1:
        return 1

    # Recursive case: n! = n × (n-1)!
    return n * factorial_recursive(n - 1)


def load_relax_field(file_path: str, file_prefix: str):
    """
    Load relaxation field data from files.

    Args:
        file_path: Directory containing the files
        file_prefix: Prefix for the filenames

    Returns:
        Tuple of (u_idxs, u_coes) loaded from files
    """
    file_name = f"{file_path}/{file_prefix}"
    u_idxs = np.loadtxt(f"{file_name}_idxs.txt", dtype=int)
    u_coes = np.loadtxt(f"{file_name}_coes.txt", dtype=float)

    return u_idxs, u_coes


class TwistRelaxGeometry:
    """Class for handling geometric relaxation in twisted bilayer systems."""

    def __init__(self, twist_struc, u_in_idxs=None, u_out_idxs=None):
        """
        Initialize with a twisted structure.

        Args:
            twist_struc: Twisted structure object containing lattice information
        """
        moire_b_base = reciprocal_base(twist_struc._Lm)
        use_mono_b_base_t = reciprocal_base(twist_struc._mono_lat_t)
        use_mono_b_base_b = reciprocal_base(twist_struc._mono_lat_b)

        self._t_num = twist_struc._t_num
        self._b_num = twist_struc._b_num
        self._mono_b_base_t = use_mono_b_base_t
        self._mono_b_base_b = use_mono_b_base_b
        self._moire_b_base = moire_b_base

        if u_in_idxs == None:
            self._u_in_idxs = np.array([
                [1, 0], [1, 1], [0, 1],
                [-1, 0], [-1, -1], [0, -1]
            ], dtype=int)
        else:
            self._u_in_idxs = u_in_idxs

        if u_out_idxs == None:
            self._u_out_idxs = np.array([
                [1, 0], [1, 1], [0, 1],
                [-1, 0], [-1, -1], [0, -1]
            ], dtype=int)
        else:
            self._u_out_idxs = u_out_idxs

    def relax_one_point_in_plane(self, layer_idx: int, point: np.ndarray) -> np.ndarray:
        """
        Apply relaxation displacement to a single point.

        Args:
            layer_idx: Layer index (-1 for top, 1 for bottom)
            point: Original coordinates [x, y, z]

        Returns:
            Relaxed coordinates as real array
        """
        # Select coefficients based on layer
        if layer_idx == -1:
            use_u_coes = self._u_in_coes_b
        else:
            use_u_coes = self._u_in_coes_t

        new_point = np.zeros_like(point, dtype=complex)
        new_point[2] = point[2]  # z-coordinate unchanged

        # Apply Fourier expansion of displacement field
        for j in range(len(self._u_in_idxs_xy)):
            phase = (self._u_in_idxs_xy[j, 0] * point[0] +
                     self._u_in_idxs_xy[j, 1] * point[1])
            exp_phase = np.exp(1j * phase)

            # Accumulate displacement components
            new_point[0] += (use_u_coes[j, 0] * exp_phase * layer_idx * 0.5 * (-1))
            new_point[1] += (use_u_coes[j, 1] * exp_phase * layer_idx * 0.5 * (-1))

        # Add displacement to original position
        new_point[0:2] = new_point[0:2] + point[0:2]

        return new_point.real

    def relax_one_point_out_plane(self, layer_idx: int, point: np.ndarray) -> np.ndarray:
        if layer_idx == -1:
            use_u_coes = self._u_out_coes_b
        else:
            use_u_coes = self._u_out_coes_t

        new_point_z = point[2]

        for j in range(len(self._u_out_idxs_xy)):
            phase = (self._u_out_idxs_xy[j, 0] * point[0] +
                     self._u_out_idxs_xy[j, 1] * point[1])
            exp_phase = np.exp(1j * phase)
            new_point_z += (use_u_coes[j] * exp_phase * layer_idx * 0.5)
        out_point = np.zeros_like(point)
        out_point[0:2] = point[0:2]
        out_point[2] = new_point_z.real
        return out_point

    def gen_relax_pattern_in_plane(self, theta_360: float, kappa_parallel: float):
        """
        Generate relaxation pattern using analytical approximation.

        Args:
            theta_360: Twist angle in degrees
            kappa_parallel: Parallel relaxation parameter

        Returns:
            Tuple of (u_idxs, u_coes_t, u_coes_b) for Fourier expansion
        """
        theta_360 = np.max((theta_360, 1))
        theta_pi = theta_360 * np.pi / 180  # Convert to radians

        # Define G-vectors for hexagonal lattice
        # u_idxs = np.array([
        #     [1, 0], [1, 1], [0, 1],
        #     [-1, 0], [-1, -1], [0, -1]
        # ], dtype=int)
        u_idxs = self._u_in_idxs

        # Top layer coefficients
        u_coes_t = np.zeros((len(u_idxs), 2), dtype=complex)
        G_norm = np.linalg.norm(self._mono_b_base_t[0])

        for i in range(len(u_idxs)):
            numerator = np.dot(u_idxs[i], self._mono_b_base_t) * kappa_parallel
            denominator = (theta_pi ** 2) * (G_norm ** 2)
            u_coes_t[i] = numerator / denominator

        u_coes_t = u_coes_t / (2.j)

        # Bottom layer coefficients
        u_coes_b = np.zeros((len(u_idxs), 2), dtype=complex)
        G_norm = np.linalg.norm(self._mono_b_base_b[0])

        for i in range(len(u_idxs)):
            numerator = np.dot(u_idxs[i], self._mono_b_base_b) * kappa_parallel
            denominator = (theta_pi ** 2) * (G_norm ** 2)
            u_coes_b[i] = numerator / denominator

        u_coes_b = u_coes_b / (2.j)

        # Store results as instance variables
        self._u_in_idxs = u_idxs
        self._u_in_idxs_xy = np.dot(u_idxs, self._moire_b_base)
        self._u_in_coes_t = u_coes_t
        self._u_in_coes_b = u_coes_b

        return u_idxs, u_coes_t, u_coes_b

    def gen_relax_pattern_out_plane(self, theta_360: float, kappa_perp: float, max_dis=0.3):
        G_norm = (np.linalg.norm(self._mono_b_base_b[0]) + np.linalg.norm(self._mono_b_base_t[0])) / 2
        max_angle = kappa_perp / ((G_norm ** 2) * max_dis)

        theta_pi = theta_360 * np.pi / 180  # Convert to radians
        theta_pi = np.max((theta_pi, max_angle))

        # Define G-vectors for hexagonal lattice
        u_idxs = self._u_out_idxs
        # u_idxs = np.array([
        #     [1, 0], [1, 1], [0, 1],
        #     [-1, 0], [-1, -1], [0, -1]
        # ], dtype=int)

        u_coes_t = np.zeros((len(u_idxs),), dtype=complex)
        G_norm = np.linalg.norm(self._mono_b_base_t[0])

        for i in range(len(u_idxs)):
            numerator = kappa_perp
            denominator = (theta_pi ** 2) * (G_norm ** 2)
            u_coes_t[i] = numerator / denominator
        u_coes_t = u_coes_t / 2

        u_coes_b = np.zeros((len(u_idxs),), dtype=complex)
        G_norm = np.linalg.norm(self._mono_b_base_b[0])

        for i in range(len(u_idxs)):
            numerator = kappa_perp
            denominator = (theta_pi ** 2) * (G_norm ** 2)
            u_coes_b[i] = numerator / denominator
        u_coes_b = u_coes_b / 2

        # self._u_out_idxs = u_idxs
        self._u_out_idxs_xy = np.dot(u_idxs, self._moire_b_base)
        self._u_out_coes_t = u_coes_t
        self._u_out_coes_b = u_coes_b

        return u_idxs, u_coes_t, u_coes_b


    def gen_relaxed_struc(self, atom_points: np.ndarray) -> np.ndarray:
        """
               Generate relaxed structure for all atoms.

               Args:
                   atom_points: Array of atom positions [x, y, z]

               Returns:
                   Array of relaxed atom positions
               """
        atom_num = len(atom_points)
        relaxed_points = np.zeros_like(atom_points)

        for i in range(self._t_num):
            out_point_out = self.relax_one_point_out_plane(1, atom_points[i])
            out_point_in = self.relax_one_point_in_plane(1, atom_points[i])
            relaxed_points[i, 0:2] = out_point_in[0:2]
            relaxed_points[i, 2] = out_point_out[2]

        for i in range(self._t_num, atom_num):
            out_point_out = self.relax_one_point_out_plane(-1, atom_points[i])
            out_point_in = self.relax_one_point_in_plane(-1, atom_points[i])
            relaxed_points[i, 0:2] = out_point_in[0:2]
            relaxed_points[i, 2] = out_point_out[2]
        return relaxed_points

class TwistRelaxKP:
    """Class for handling k·p perturbation with relaxation effects."""

    def __init__(self, twist_model):
        """
        Initialize with a twisted model.

        Args:
            twist_model: Twisted model object containing reciprocal lattice info
        """
        moire_b_base = twist_model._moire_b_base
        mono_b_base = twist_model._mono_b_base

        self._moire_b_base = moire_b_base
        self._mono_b_base = mono_b_base
        self._twist_model = twist_model

    def gen_relax_pattern(self, theta_360: float, kappa_parallel: float):
        """
        Generate relaxation pattern for k·p model.

        Args:
            theta_360: Twist angle in degrees
            kappa_parallel: Parallel relaxation parameter

        Returns:
            Tuple of (u_idxs, u_coes) for Fourier expansion
        """
        theta_pi = theta_360 * np.pi / 180  # Convert to radians

        # Define G-vectors for hexagonal lattice
        u_idxs = np.array([
            [1, 0], [1, 1], [0, 1],
            [-1, 0], [-1, -1], [0, -1]
        ], dtype=int)

        # Calculate coefficients
        u_coes = np.zeros((len(u_idxs), 2), dtype=complex)
        G_norm = np.linalg.norm(self._mono_b_base[0])

        for i in range(len(u_idxs)):
            numerator = np.dot(u_idxs[i], self._mono_b_base) * kappa_parallel
            denominator = (theta_pi ** 2) * (G_norm ** 2)
            u_coes[i] = numerator / denominator

        u_coes = u_coes / (2.j)

        # Store results as instance variables
        self._u_idxs = u_idxs
        self._u_idxs_xy = np.dot(u_idxs, self._moire_b_base)
        self._u_coes = u_coes

        return u_idxs, u_coes

    def gen_relax_coupling(self, couple_idxs: np.ndarray, couple_coes: np.ndarray,
                           order_num: int, valley_pos: np.ndarray = np.zeros(2)):
        """
        Generate relaxed coupling terms up to given order.

        Args:
            couple_idxs: Coupling indices
            couple_coes: Coupling coefficients
            order_num: Maximum perturbation order
            valley_pos: Valley position offset (default: [0, 0])

        Returns:
            Tuple of (relaxed_idxs, relaxed_coes) including all orders
        """

        def expand_sum(coes_arr_1, idxs_arr_1, coes_arr_2, idxs_arr_2):
            """
            Expand product of two Fourier series.

            Returns:
                Tuple of (new_coes_arr, new_idxs_arr) for expanded series
            """
            num_1 = len(coes_arr_1)
            num_2 = len(coes_arr_2)
            new_coes_arr = np.zeros(num_1 * num_2, dtype=complex)
            new_idxs_arr = np.zeros((num_1 * num_2, 2), dtype=int)

            idx = 0
            for j_1 in range(num_1):
                for j_2 in range(num_2):
                    new_coes_arr[idx] = coes_arr_1[j_1] * coes_arr_2[j_2]
                    new_idxs_arr[idx] = idxs_arr_1[j_1] + idxs_arr_2[j_2]
                    idx += 1

            return new_coes_arr, new_idxs_arr

        # Convert indices to reciprocal space vectors
        Q_list = np.dot(couple_idxs + valley_pos, self._mono_b_base)
        num_couple = len(Q_list)
        num_u = len(self._u_idxs)

        # Precompute dot products Q·ũ
        Q_i_dot_u_tilde_j = np.zeros((num_couple, num_u), dtype=complex)
        for i in range(num_couple):
            for j in range(num_u):
                Q_i_dot_u_tilde_j[i, j] = np.dot(Q_list[i], self._u_coes[j])

        # Generate perturbation terms for each coupling
        Q_u_coes_all = []
        Q_u_idxs_all = []

        for i in range(num_couple):
            Qi_u_coes = []
            Qi_u_idxs = []

            for order_id in range(order_num):
                out_coes = np.copy(Q_i_dot_u_tilde_j[i])
                out_idxs = np.copy(self._u_idxs)
                factor_im = 1.j

                # Expand to current order
                for _ in range(order_id - 1):
                    factor_im *= 1.j
                    out_coes, out_idxs = expand_sum(
                        out_coes, out_idxs,
                        Q_i_dot_u_tilde_j[i], self._u_idxs
                    )

                # Divide by factorial for Taylor expansion
                Qi_u_coes.append(factor_im * out_coes / factorial_recursive(order_id))
                Qi_u_idxs.append(out_idxs)

            Q_u_coes_all.append(Qi_u_coes)
            Q_u_idxs_all.append(Qi_u_idxs)

        # Collect all terms including original couplings
        relaxed_coes = []
        relaxed_idxs = []

        # Add zeroth-order (original) terms
        for i in range(num_couple):
            relaxed_coes.append(couple_coes[i])
            relaxed_idxs.append(couple_idxs[i])

        # Add perturbation terms
        for i in range(num_couple):
            relax_Qi_coes = Q_u_coes_all[i]
            relax_Qi_idxs = Q_u_idxs_all[i]

            for order_id in range(order_num):
                relax_Qi_order_coes = relax_Qi_coes[order_id]
                relax_Qi_order_idxs = relax_Qi_idxs[order_id]

                for j in range(len(relax_Qi_order_idxs)):
                    use_idxs = relax_Qi_order_idxs[j] + couple_idxs[i]
                    use_coes = relax_Qi_order_coes[j] * couple_coes[i]

                    relaxed_idxs.append(use_idxs)
                    relaxed_coes.append(use_coes)

        # Convert to numpy arrays
        relaxed_idxs = np.asarray(relaxed_idxs)
        relaxed_coes = np.asarray(relaxed_coes)

        return relaxed_idxs, relaxed_coes