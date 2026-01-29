"""
Twisted bilayer k·p model implementation.
Provides continuum model Hamiltonian construction and band structure calculations.
"""

import numpy as np
from .simple_func import R_theta, reciprocal_base, gen_k_mesh


def inverse_reciprocal(b_base: np.ndarray) -> np.ndarray:
    """
    Convert reciprocal lattice vectors to real space lattice vectors.

    Args:
        b_base: Reciprocal lattice basis vectors (2x2 matrix)

    Returns:
        Real space lattice vectors (2x2 matrix)
    """
    # Transpose reciprocal basis to column arrangement, invert, multiply by 2π
    B_T = np.array(b_base).T
    A = 2 * np.pi * np.linalg.inv(B_T)
    return A


def two_to_one(n: int, i_x: int, i_y: int) -> int:
    """
    Convert 2D grid indices to 1D index using row-major ordering.

    Args:
        n: Grid size (number of columns)
        i_x: Row index
        i_y: Column index

    Returns:
        1D flattened index
    """
    iii = i_x * n + i_y
    return iii


class TwistKP:
    """k·p continuum model for twisted bilayer systems."""

    def __init__(self, theta_360: float, tr: int, valley_pos: np.ndarray, mono_lat: np.ndarray,
                 mass=None, hv_a=None, mono_ham_idxs=None, mono_ham_coes=None,
                 V_z: float = 0, m_z: float = 0):
        """
        Initialize twisted bilayer k·p model.

        Args:
            theta_360: Twist angle in degrees
            tr: Cutoff radius for reciprocal lattice vectors
            valley_pos: Valley position in reciprocal space [kx, ky]
            mono_lat: Monolayer lattice vectors (2x2 matrix)
            mass: Effective mass tensor [mx, my] (optional)
            hv_a: Hopping parameter for Dirac Hamiltonian (optional)
            mono_ham_idxs: Indices for custom monolayer Hamiltonian (optional)
            mono_ham_coes: Coefficients for custom monolayer Hamiltonian (optional)
            V_z: Layer potential difference
            m_z: Zeeman-like term magnitude
        """
        self._theta = theta_360 * np.pi / 180  # Convert to radians
        lat_a = np.linalg.norm(mono_lat[0])

        # Calculate reciprocal lattice bases
        mono_b_base = reciprocal_base(mono_lat)
        self._mono_b_base = mono_b_base

        # Calculate moiré reciprocal lattice basis
        moire_b_base = np.zeros((2, 2), dtype=float)
        moire_b_base[0] = (np.dot(R_theta(-self._theta / 2), mono_b_base[0]) -
                           np.dot(R_theta(self._theta / 2), mono_b_base[0]))
        moire_b_base[1] = (np.dot(R_theta(-self._theta / 2), mono_b_base[1]) -
                           np.dot(R_theta(self._theta / 2), mono_b_base[1]))

        self._moire_b_base = moire_b_base

        # Calculate real space moiré lattice
        Lm = inverse_reciprocal(self._moire_b_base)
        self._Lm = Lm

        self._tr = tr
        self._g_num, self._g_points = self.G_map(tr)
        self._g_idx = self._g_points[:, 2:4].tolist()
        self._g_mesh = self._g_points[:, 0:2]

        self._q_hop = self.gen_q_hop(valley_pos)
        self._valley_pos = valley_pos

        self._G_num = self._g_num * 2
        self._G_mesh = np.zeros((self._G_num, 2), dtype=float)
        self._G_mesh[:self._g_num] = self._g_mesh + self._q_hop[0]
        self._G_mesh[self._g_num:] = self._g_mesh + self._q_hop[1]

        # Setup monolayer Hamiltonian parameters
        if (mass is not None) and (hv_a is None):
            self._if_mass = True
            self._if_hv = False
            self._mass_x = mass[0]
            self._mass_y = mass[1]
            self._coe_x = -((7.63 * 0.5) / mass[0]) * 1000  # kx coefficient
            self._coe_y = -((7.63 * 0.5) / mass[1]) * 1000  # ky coefficient
            self._V_z_t = V_z / 2  # Top layer potential
            self._V_z_b = -V_z / 2  # Bottom layer potential
            self._mono_nbands = 1  # Single band for massive model
            self._m_z = 0  # No Zeeman term for massive model
        elif (mass is None) and (hv_a is not None):
            self._if_mass = False
            self._if_hv = True
            self._hv = hv_a * lat_a  # Dirac velocity
            self._V_z_t = (V_z / 2) * np.eye(2)  # Top layer potential (2x2)
            self._V_z_b = -(V_z / 2) * np.eye(2)  # Bottom layer potential (2x2)
            self._mono_nbands = 2  # Two bands for Dirac model
            self._m_z = np.array([[m_z, 0.0],
                                  [0.0, -m_z]], dtype=float)  # Zeeman term
        else:
            print("Monolayer Hamiltonian custom mode")
            # Custom Hamiltonian parameters would be handled here

        self._nbands = self._mono_nbands * self._G_num

        # Determine valley index based on position
        if valley_pos[0] > 0:
            self._valley = 1
        else:
            self._valley = -1

    def gen_q_hop(self, valley_pos: np.ndarray) -> np.ndarray:
        """
        Generate momentum hop vectors between layers.

        Args:
            valley_pos: Valley position in reciprocal space

        Returns:
            Array of hop vectors (2x2) for top and bottom layers
        """
        valley_pos_xy = np.dot(valley_pos, self._mono_b_base)

        # Calculate momentum shift between rotated layers
        dis_q = (np.dot(R_theta(self._theta / 2), valley_pos_xy) -
                 np.dot(R_theta(-self._theta / 2), valley_pos_xy))

        q_hop = np.zeros((2, 2), dtype=float)
        q_hop[0] = np.dot(valley_pos, self._moire_b_base)  # Top layer
        q_hop[1] = q_hop[0] - dis_q  # Bottom layer

        return q_hop

    def G_map(self, tr: int):
        """
        Generate reciprocal lattice vectors within cutoff radius.

        Args:
            tr: Cutoff radius in reciprocal lattice units

        Returns:
            Tuple of (G_number, G_points) where G_points contains
            [Gx, Gy, i1, i2, 0, distance, index] for each G-vector
        """
        moire_b_base = self._moire_b_base
        N = (2 * tr + 1) ** 2  # Total number of G-vectors

        G_points = np.zeros((N, 5))
        ii = 0

        # Generate all G-vectors within the cutoff
        for i_2 in range(-tr, tr + 1):
            for i_1 in range(-tr, tr + 1):
                G_points[ii, 0:2] = (i_1 * moire_b_base[0] +
                                     i_2 * moire_b_base[1])
                G_points[ii, 2] = i_1  # Index 1
                G_points[ii, 3] = i_2  # Index 2
                G_points[ii, 4] = 0  # Placeholder
                ii += 1

        # Calculate distances from origin
        distances = np.linalg.norm(G_points[:, 0:2], ord=2, axis=1, keepdims=True)
        G_points = np.hstack([G_points, distances])

        G_number = np.shape(G_points)[0]
        G_points_index = np.arange(0, G_number).reshape(G_number, 1)
        G_points = np.hstack([G_points, G_points_index])

        return G_number, G_points

    def k_path(self, path: np.ndarray, nk: int):
        """
        Generate k-points along a specified path in reciprocal space.

        Args:
            path: Array of high-symmetry points in fractional coordinates
            nk: Total number of k-points along the path

        Returns:
            Tuple of (k_vec, k_dist, k_node) where:
            - k_vec: Cartesian coordinates of k-points
            - k_dist: Distance along the path for each k-point
            - k_node: Positions of high-symmetry points
        """
        lat = self._Lm
        k_list = path

        # Metric for distance calculation in reciprocal space
        k_metric = np.linalg.inv(np.dot(lat, lat.T))

        k_node = np.zeros(k_list.shape[0], dtype=float)
        k_dist = np.zeros(nk, dtype=float)
        k_vec = np.zeros((nk, k_list.shape[1]), dtype=float)
        k_vec[0] = k_list[0]

        node_index = [0]

        # Calculate distances between high-symmetry points
        for i in range(1, k_list.shape[0]):
            dk = k_list[i] - k_list[i - 1]
            dklen = np.sqrt(np.dot(dk, np.dot(k_metric, dk)))
            k_node[i] = k_node[i - 1] + dklen

        # Determine indices for high-symmetry points
        for n in range(1, k_list.shape[0] - 1):
            frac = k_node[n] / k_node[-1]
            node_index.append(int(round(frac * (nk - 1))))
        node_index.append(nk - 1)

        # Interpolate k-points along each segment
        for ii in range(1, k_list.shape[0]):
            n_i = node_index[ii - 1]
            n_f = node_index[ii]
            kd_i = k_node[ii - 1]
            kd_f = k_node[ii]
            k_i = k_list[ii - 1]
            k_f = k_list[ii]

            for j in range(n_i, n_f + 1):
                frac = float(j - n_i) / float(n_f - n_i)
                k_dist[j] = kd_i + frac * (kd_f - kd_i)
                k_vec[j] = k_i + frac * (k_f - k_i)

        return k_vec, k_dist, k_node

    def gen_couple(self, inter_idxs: np.ndarray, intra_t_idxs: np.ndarray,
                   intra_b_idxs: np.ndarray, inter_coes: np.ndarray,
                   intra_t_coes: np.ndarray, intra_b_coes: np.ndarray):
        """
        Generate coupling Hamiltonian from Fourier coefficients.

        Args:
            inter_idxs: Interlayer coupling indices
            intra_t_idxs: Intralayer coupling indices (top)
            intra_b_idxs: Intralayer coupling indices (bottom)
            inter_coes: Interlayer coupling coefficients
            intra_t_coes: Intralayer coupling coefficients (top)
            intra_b_coes: Intralayer coupling coefficients (bottom)
        """
        H_inter = np.zeros((self._g_num * self._mono_nbands,
                            self._g_num * self._mono_nbands), dtype=complex)
        H_intra_t = np.zeros((self._g_num * self._mono_nbands,
                              self._g_num * self._mono_nbands), dtype=complex)
        H_intra_b = np.zeros((self._g_num * self._mono_nbands,
                              self._g_num * self._mono_nbands), dtype=complex)

        # Build interlayer coupling
        for i in range(len(inter_idxs)):
            H_inter += self.idx_to_matrix(inter_idxs[i], inter_coes[i])

        # Build intralayer couplings
        for i in range(len(intra_t_idxs)):
            H_intra_t += self.idx_to_matrix(intra_t_idxs[i], intra_t_coes[i])

        for i in range(len(intra_b_idxs)):
            H_intra_b += self.idx_to_matrix(intra_b_idxs[i], intra_b_coes[i])

        # Assemble full coupling Hamiltonian
        H_couple = np.zeros((self._G_num * self._mono_nbands,
                             self._G_num * self._mono_nbands), dtype=complex)

        H_couple[:self._nbands // 2, self._nbands // 2:] = H_inter
        H_couple[self._nbands // 2:, :self._nbands // 2] = H_inter.T.conj()
        H_couple[:self._nbands // 2, :self._nbands // 2] = H_intra_t
        H_couple[self._nbands // 2:, self._nbands // 2:] = H_intra_b

        self._H_couple = H_couple

    def idx_to_matrix(self, inter_GM: np.ndarray, inter_coe: np.ndarray) -> np.ndarray:
        """
        Convert coupling index and coefficient to matrix representation.

        Args:
            inter_GM: Coupling index [i, j]
            inter_coe: Coupling coefficient matrix

        Returns:
            Coupling matrix in the full Hilbert space
        """
        couple_idx = inter_GM.tolist()
        couple_mat = np.zeros((self._g_num, self._g_num), dtype=complex)

        # Build sparse coupling matrix
        for i_g in range(self._g_num):
            i_point = self._g_idx[i_g]
            j_point = [i_point[0] + couple_idx[0],
                       i_point[1] + couple_idx[1]]

            if j_point in self._g_idx:
                couple_mat[i_g, self._g_idx.index(j_point)] = 1

        # Expand to include internal degrees of freedom
        H_part_GM = np.kron(couple_mat, inter_coe)
        return H_part_GM

    def gen_H_diag(self, k: np.ndarray) -> np.ndarray:
        """
        Generate diagonal part of Hamiltonian (monolayer + potentials).

        Args:
            k: Momentum point in Cartesian coordinates

        Returns:
            Diagonal Hamiltonian matrix
        """
        gk_list = self._G_mesh + k  # Shift G-vectors by k
        H_diag = np.zeros((self._nbands, self._nbands), dtype=complex)

        # Top layer diagonal blocks
        for i_G in range(self._g_num):
            start = self._mono_nbands * i_G
            end = self._mono_nbands * (i_G + 1)
            H_diag[start:end, start:end] = (self.gen_mono_H(gk_list[i_G]) +
                                            self._V_z_t + self._m_z)

        # Bottom layer diagonal blocks
        for i_G in range(self._g_num, self._G_num):
            start = self._mono_nbands * i_G
            end = self._mono_nbands * (i_G + 1)
            H_diag[start:end, start:end] = (self.gen_mono_H(gk_list[i_G]) +
                                            self._V_z_b - self._m_z)

        return H_diag

    def gen_mono_H(self, gk: np.ndarray) -> np.ndarray:
        """
        Generate monolayer Hamiltonian at given momentum.

        Args:
            gk: Momentum vector in Cartesian coordinates

        Returns:
            Monolayer Hamiltonian matrix
        """
        if self._if_mass:
            # Massive parabolic band
            H_mono = ((gk[0] ** 2) * self._coe_x +
                      (gk[1] ** 2) * self._coe_y)
        elif self._if_hv:
            # Dirac Hamiltonian
            H_mono = -self._hv * np.array([
                [0, self._valley * gk[0] - gk[1] * 1.j],
                [self._valley * gk[0] - gk[1] * 1.j, 0]
            ])
        else:
            H_mono = 0

        return H_mono

    def gen_ham(self, k: np.ndarray) -> np.ndarray:
        """
        Generate full Hamiltonian at given momentum.

        Args:
            k: Momentum point in Cartesian coordinates

        Returns:
            Full Hamiltonian matrix
        """
        ham = self.gen_H_diag(k) + self._H_couple
        return ham

    def gen_all_ham(self, k_points: np.ndarray) -> np.ndarray:
        """
        Generate Hamiltonians for multiple k-points.

        Args:
            k_points: Array of k-points in fractional coordinates

        Returns:
            Array of Hamiltonian matrices for each k-point
        """
        k_points = np.dot(k_points, self._moire_b_base)  # Convert to Cartesian
        ham = np.zeros((len(k_points), self._nbands, self._nbands), dtype=complex)

        for i in range(len(k_points)):
            ham[i] = self.gen_ham(k_points[i])

        return ham

    def solve_all(self, k_points: np.ndarray, eig: bool = False):
        """
        Solve eigenvalue problem for multiple k-points.

        Args:
            k_points: Array of k-points in fractional coordinates
            eig: If True, return both eigenvalues and eigenvectors

        Returns:
            If eig=False: array of eigenvalues for each k-point
            If eig=True: tuple of (eigenvalues, eigenvectors) for each k-point
        """
        k_points = np.dot(k_points, self._moire_b_base)  # Convert to Cartesian

        if eig:
            evals = np.zeros((len(k_points), self._nbands))
            eiges = np.zeros((len(k_points), self._nbands, self._nbands), dtype=complex)

            for i in range(len(k_points)):
                ham = self.gen_ham(k_points[i])
                evals[i], eiges[i] = np.linalg.eigh(ham)

            return evals, eiges
        else:
            evals = np.zeros((len(k_points), self._nbands))

            for i in range(len(k_points)):
                ham = self.gen_ham(k_points[i])
                evals[i] = np.linalg.eigvalsh(ham)

            return evals

    def gen_band_index(self, band_index: np.ndarray) -> np.ndarray:
        """
        Adjust band indices based on model type.

        Args:
            band_index: Original band indices

        Returns:
            Adjusted band indices
        """
        if self._if_mass:
            band_index = self._G_num * np.ones_like(band_index) - band_index
        else:
            band_index = self._G_num * np.ones_like(band_index) + band_index

        return band_index

    def gen_chern_number(self, n: int, band_index: np.ndarray) -> np.ndarray:
        """
        Calculate Chern number using discretized Brillouin zone.

        Args:
            n: Grid size for Brillouin zone discretization
            band_index: Indices of bands to calculate Chern number for

        Returns:
            Chern number(s) for specified bands
        """
        k_mesh = gen_k_mesh(n, if_edge=True)
        evals, eiges = self.solve_all(k_mesh, eig=True)
        band_index = self.gen_band_index(band_index)
        wf = eiges[:, :, band_index]

        Q = 0
        # Calculate Berry flux through each plaquette
        for i in range(n - 1):
            for j in range(n - 1):
                V1 = wf[two_to_one(n, i, j)]
                V2 = wf[two_to_one(n, i + 1, j)]
                V3 = wf[two_to_one(n, i + 1, j + 1)]
                V4 = wf[two_to_one(n, i, j + 1)]

                # Calculate link variables
                phi_1 = np.einsum('mn,mn->n', V1.conj(), V2)
                phi_2 = np.einsum('mn,mn->n', V2.conj(), V3)
                phi_3 = np.einsum('mn,mn->n', V3.conj(), V4)
                phi_4 = np.einsum('mn,mn->n', V4.conj(), V1)

                # Berry phase around plaquette
                phi_n = np.angle(phi_1 * phi_2 * phi_3 * phi_4)
                Q += phi_n

        Q = np.round(Q / (2 * np.pi))  # Convert to Chern number
        return Q