"""
Twisted bilayer tight-binding model generation and manipulation.

This module provides the TwistTB class for constructing and manipulating
tight-binding models of twisted bilayer systems, including Hamiltonian
generation, parallel computation, and format conversion utilities.
"""

import numpy as np
import multiprocessing as mp
import os
import sys
from scipy.sparse import coo_matrix, csr_matrix, save_npz, load_npz
from scipy.sparse.linalg import LinearOperator
from .simple_func import R_theta


def pick_mp_context(start: str | None = None):
    """
    Select appropriate multiprocessing context based on platform.

    Parameters
    ----------
    start : str or None, optional
        Specific context to use (e.g., 'spawn', 'forkserver', 'fork').
        If None, selects based on platform.

    Returns
    -------
    multiprocessing.context.BaseContext
        Appropriate multiprocessing context.

    Notes
    -----
    - Linux: Uses 'forkserver' for better performance
    - Windows/macOS: Uses 'spawn' (only option available)
    """
    import multiprocessing as _mp
    if start:
        return _mp.get_context(start)
    if sys.platform.startswith("linux"):
        return _mp.get_context("forkserver")
    return _mp.get_context("spawn")


# --- Per-process cached TwistTB instance for workers ---
_TB_INST = None


def _init_twist_inst(tb_instance):
    """
    Initializer for worker processes.

    Parameters
    ----------
    tb_instance : TwistTB
        Picklable TwistTB instance to cache in worker processes.
    """
    global _TB_INST
    _TB_INST = tb_instance


def _row_worker_sparse(args):
    """
    Worker function computing sparse matrix entries for one real-space row.

    Parameters
    ----------
    args : tuple
        (k, i, N, drop_tol) where:
        - k: R-vector index
        - i: row index
        - N: total number of states
        - drop_tol: tolerance for dropping small matrix elements

    Returns
    -------
    tuple
        (i, js, vals) where:
        - i: row index
        - js: column indices with non-zero entries
        - vals: corresponding matrix values
    """
    k, i, N, drop_tol = args
    tb = _TB_INST
    js, vals = [], []
    for j in range(N):
        amp = tb.gen_one_r_ham(k, i, j)
        if amp != 0 and (abs(amp) > drop_tol):
            js.append(j)
            vals.append(amp)
    return (i, np.asarray(js, dtype=int), np.asarray(vals, dtype=complex))


# --- NPZ cache for Windows/macOS builders ---
_NPZ_CACHE = {}  # {npz_dir: (R_vectors, H0, [HR1..HR4])}


def _load_npz_dir(npz_dir: str):
    """
    Load and cache sparse Hamiltonian blocks from disk for current process.

    Parameters
    ----------
    npz_dir : str
        Directory containing saved sparse matrix files.

    Returns
    -------
    tuple
        (R_vectors, H0, HRs) where:
        - R_vectors: R-vectors for Hamiltonian blocks
        - H0: R=0 sparse Hamiltonian block
        - HRs: list of R≠0 sparse Hamiltonian blocks

    Notes
    -----
    Uses process-level caching to avoid repeated disk reads.
    """
    key = os.path.abspath(npz_dir)
    item = _NPZ_CACHE.get(key)
    if item is None:
        R = np.load(os.path.join(npz_dir, "R_vectors.npy"))
        H0 = load_npz(os.path.join(npz_dir, "H0.npz")).tocsr()
        HRs = [load_npz(os.path.join(npz_dir, f"HR{m}.npz")).tocsr() for m in range(1, 5)]
        _NPZ_CACHE[key] = (R, H0, HRs)
        item = _NPZ_CACHE[key]
    return item


def build_ham_from_npz(k, npz_dir: str):
    """
    Assemble k-space Hamiltonian from saved sparse blocks.

    Parameters
    ----------
    k : array_like
        k-point in reciprocal space (3-component vector).
    npz_dir : str
        Directory containing saved sparse matrix files.

    Returns
    -------
    scipy.sparse.csr_matrix
        Sparse k-space Hamiltonian matrix in CSR format.

    Notes
    -----
    Suitable for shift-invert eigensolvers. Performs Bloch phase sum:
        H(k) = Σ_R exp(i·2π·k·R) * H_R
    """
    R, H0, HRs = _load_npz_dir(npz_dir)
    phases = np.exp(2j * np.pi * (R @ np.asarray(k)))
    H = H0.copy().astype(np.complex128) * phases[0]
    for p, HR in zip(phases[1:], HRs):
        H = H + p * HR + np.conjugate(p) * HR.T.conjugate()
    return H.tocsr()


def build_linop_from_npz(k, npz_dir: str, N: int):
    """
    Construct LinearOperator for H(k) without assembling full matrix.

    Parameters
    ----------
    k : array_like
        k-point in reciprocal space (3-component vector).
    npz_dir : str
        Directory containing saved sparse matrix files.
    N : int
        Dimension of Hamiltonian matrix.

    Returns
    -------
    scipy.sparse.linalg.LinearOperator
        Linear operator representing H(k) for matrix-vector operations.

    Notes
    -----
    Memory-efficient alternative for sigma=None in eigensolvers.
    """
    R, H0, HRs = _load_npz_dir(npz_dir)
    phases = np.exp(2j * np.pi * (R @ np.asarray(k)))

    def _matvec(x):
        """Matrix-vector multiplication: y = H(k)·x"""
        y = H0 @ x
        for p, HR in zip(phases[1:], HRs):
            y = y + p * (HR @ x) + np.conjugate(p) * (HR.T.conjugate() @ x)
        return y

    def _rmatvec(x):
        """Adjoint matrix-vector multiplication: y = H(k)^†·x"""
        return np.conjugate(_matvec(np.conjugate(x)))

    return LinearOperator(dtype=np.complex128, shape=(N, N),
                          matvec=_matvec, rmatvec=_rmatvec)


class TwistTB:
    """
    Tight-binding model for twisted bilayer systems.

    This class constructs and manipulates tight-binding Hamiltonians for
    twisted bilayer structures, supporting both dense and sparse representations,
    parallel computation, and various output formats.

    Attributes
    ----------
    _theta : float
        Twist angle in radians.
    _Lm : numpy.ndarray
        Moiré superlattice vectors (3x3 matrix).
    _points : numpy.ndarray
        Atomic positions in moiré superlattice (Cartesian coordinates).
    _index : numpy.ndarray
        Indices mapping moiré atoms to original monolayer atoms.
    _t_num : int
        Number of top layer atoms in moiré cell.
    _b_num : int
        Number of bottom layer atoms in moiré cell.
    _atom_name : list
        Element names for all atoms in moiré superlattice.
    _mono_hamR_t : numpy.ndarray
        R-vectors for top monolayer Hamiltonian.
    _mono_ham_up : numpy.ndarray
        Top monolayer Hamiltonian blocks.
    _mono_lat_t : numpy.ndarray
        Top monolayer lattice vectors.
    _mono_orb_t : numpy.ndarray
        Top monolayer orbital positions in direct coordinates.
    _mono_atom_pos_t : numpy.ndarray
        Top monolayer atomic positions in direct coordinates.
    _mono_hamR_b : numpy.ndarray
        R-vectors for bottom monolayer Hamiltonian.
    _mono_ham_dw : numpy.ndarray
        Bottom monolayer Hamiltonian blocks.
    _mono_lat_b : numpy.ndarray
        Bottom monolayer lattice vectors.
    _mono_orb_b : numpy.ndarray
        Bottom monolayer orbital positions in direct coordinates.
    _mono_atom_pos_b : numpy.ndarray
        Bottom monolayer atomic positions in direct coordinates.
    _atom_orb_list_t : list
        Orbital indices for each atom in top monolayer.
    _atom_orb_list_b : list
        Orbital indices for each atom in bottom monolayer.
    _orb_position : numpy.ndarray
        Orbital positions in moiré superlattice.
    _orb_index : numpy.ndarray
        Indices mapping moiré orbitals to monolayer orbitals.
    _num_orb_t : int
        Number of top layer orbitals in moiré cell.
    _num_orb_b : int
        Number of bottom layer orbitals in moiré cell.
    _total_orb_num : int
        Total number of orbitals in moiré cell.
    _twist_hamR : numpy.ndarray
        R-vectors for moiré Hamiltonian (5x3 array).
    _mono_lat_up : numpy.ndarray
        Rotated top monolayer lattice vectors.
    _mono_lat_dw : numpy.ndarray
        Rotated bottom monolayer lattice vectors.
    _model_type : str
        Model type identifier ("twist_tb").
    _orb_name : dict
        Dictionary mapping element names to orbital names.
    _h0 : numpy.ndarray
        Reference interlayer coupling amplitudes.
    _d0 : numpy.ndarray
        Optimal interlayer separations.
    _r0 : numpy.ndarray
        Interlayer coupling decay lengths.
    _spin : bool
        Flag indicating spin-polarized calculation.
    _total_state_num : int
        Total number of quantum states (including spin).
    _num_state_t : int
        Number of top layer states (including spin).
    _num_state_b : int
        Number of bottom layer states (including spin).
    _state_position : numpy.ndarray
        State positions (including spin duplication).
    _state_index : numpy.ndarray
        State indices mapping to monolayer orbitals.
    _mono_state_t : numpy.ndarray
        Top monolayer state positions.
    _mono_state_b : numpy.ndarray
        Bottom monolayer state positions.
    _twist_ham : numpy.ndarray
        Dense real-space Hamiltonian blocks.
    _twist_ham_sparse : list
        Sparse real-space Hamiltonian blocks.
    _sparse_out_dir : str
        Directory for exported sparse matrix files.
    """

    def __init__(self, theta_360, mono_t_model, mono_b_model, TB_structure, h0, d0, r0):
        """
        Initialize TwistTB with monolayer models and twist geometry.

        Parameters
        ----------
        theta_360 : float
            Twist angle in degrees.
        mono_t_model : TBModel
            Tight-binding model for top monolayer.
        mono_b_model : TBModel
            Tight-binding model for bottom monolayer.
        TB_structure : TwistGeometry
            Twist geometry object containing moiré structure.
        h0 : numpy.ndarray
            Reference interlayer coupling amplitudes matrix.
        d0 : numpy.ndarray
            Optimal interlayer separation matrix.
        r0 : numpy.ndarray
            Interlayer coupling decay length matrix.
        """
        self._theta = theta_360 * np.pi / 180
        self._Lm = TB_structure._Lm
        self._points = TB_structure._moire_points
        self._index = TB_structure._atom_index
        self._t_num = TB_structure._t_num
        self._b_num = TB_structure._b_num
        self._atom_name = TB_structure._atom_name

        # Extract top monolayer properties
        self._mono_hamR_t = mono_t_model._hamR
        self._mono_ham_up = mono_t_model._ham
        self._mono_lat_t = mono_t_model._lat
        self._mono_orb_t = mono_t_model._orb
        self._mono_atom_pos_t = mono_t_model._atom_position

        # Extract bottom monolayer properties
        self._mono_hamR_b = mono_b_model._hamR
        self._mono_ham_dw = mono_b_model._ham
        self._mono_lat_b = mono_b_model._lat
        self._mono_orb_b = mono_b_model._orb
        self._mono_atom_pos_b = mono_b_model._atom_position

        # Build atom-to-orbital mapping for top layer
        atom_orb_list_t = []
        for i in range(len(mono_t_model._atom_position)):
            one_use_atom = mono_t_model._atom_position[i]
            list_use = []
            for j in range(len(mono_t_model._orb)):
                one_use_orb = mono_t_model._orb[j]
                if np.allclose(one_use_atom, one_use_orb):
                    list_use.append(j)
            atom_orb_list_t.append(list_use)

        # Build atom-to-orbital mapping for bottom layer
        atom_orb_list_b = []
        for i in range(len(mono_b_model._atom_position)):
            one_use_atom = mono_b_model._atom_position[i]
            list_use = []
            for j in range(len(mono_b_model._orb)):
                one_use_orb = mono_b_model._orb[j]
                if np.allclose(one_use_atom, one_use_orb):
                    list_use.append(j)
            atom_orb_list_b.append(list_use)

        self._atom_orb_list_t = atom_orb_list_t
        self._atom_orb_list_b = atom_orb_list_b

        # Build orbital arrays for moiré cell
        orb_position = []
        orb_index = []
        num_orb_t = 0

        # Top layer orbitals
        for i in range(self._t_num):
            num_orb_t = num_orb_t + len(self._atom_orb_list_t[self._index[i]])
            orb_index.append(self._atom_orb_list_t[self._index[i]])
            for j in range(len(self._atom_orb_list_t[self._index[i]])):
                orb_position.append(self._points[i])

        # Bottom layer orbitals
        num_orb_b = 0
        for i in range(self._t_num, self._t_num + self._b_num):
            num_orb_b = num_orb_b + len(self._atom_orb_list_b[self._index[i]])
            orb_index.append(self._atom_orb_list_b[self._index[i]])
            for j in range(len(self._atom_orb_list_b[self._index[i]])):
                orb_position.append(self._points[i])

        self._orb_position = np.array(orb_position)
        self._orb_index = np.array(sum(orb_index, []))
        self._num_orb_t = num_orb_t
        self._num_orb_b = num_orb_b
        self._total_orb_num = num_orb_t + num_orb_b

        # Define moiré Hamiltonian R-vectors
        self._twist_hamR = np.zeros((5, 3), dtype=int)
        self._twist_hamR[0] = np.array([0, 0, 0])
        self._twist_hamR[1] = np.array([1, 0, 0])
        self._twist_hamR[2] = np.array([0, 1, 0])
        self._twist_hamR[3] = np.array([1, 1, 0])
        self._twist_hamR[4] = np.array([1, -1, 0])

        # Rotate monolayer lattices for twisted configuration
        self._mono_lat_up = np.copy(self._mono_lat_t)
        self._mono_lat_dw = np.copy(self._mono_lat_b)
        self._mono_lat_up[0:2, 0:2] = np.dot(R_theta(self._theta / 2),
                                             self._mono_lat_t[0:2, 0:2].T).T
        self._mono_lat_dw[0:2, 0:2] = np.dot(R_theta(-self._theta / 2),
                                             self._mono_lat_b[0:2, 0:2].T).T

        self._model_type = "twist_tb"

        # Combine orbital name dictionaries
        self._orb_name = {}
        self._orb_name.update(mono_t_model._orb_name)
        self._orb_name.update(mono_b_model._orb_name)

        # Store interlayer coupling parameters
        self._h0 = h0
        self._d0 = d0
        self._r0 = r0

        # Handle spin degrees of freedom
        if (mono_t_model._nspin + mono_b_model._nspin) == 4:
            self._spin = True
            self._total_state_num = self._total_orb_num * 2
            self._num_state_t = self._num_orb_t * 2
            self._num_state_b = self._num_orb_b * 2

            # Build state arrays with spin duplication
            self._state_position = np.zeros((self._total_state_num, 3), dtype=float)
            self._state_position[:self._num_orb_t] = self._orb_position[:self._num_orb_t]
            self._state_position[self._num_orb_t:self._num_state_t] = \
                self._orb_position[0:self._num_orb_t]
            self._state_position[self._num_state_t:self._num_state_t + self._num_orb_b] = \
                self._orb_position[self._num_orb_t:]
            self._state_position[self._num_state_t + self._num_orb_b:] = \
                self._orb_position[self._num_orb_t:]

            # Build state index arrays
            self._state_index = np.zeros((self._total_state_num,), dtype=int)
            self._state_index[:self._num_orb_t] = self._orb_index[:self._num_orb_t]
            self._state_index[self._num_orb_t:self._num_state_t] = \
                self._orb_index[:self._num_orb_t] + mono_t_model._norb
            self._state_index[self._num_state_t:self._num_state_t + self._num_orb_b] = \
                self._orb_index[self._num_orb_t:]
            self._state_index[self._num_state_t + self._num_orb_b:] = \
                self._orb_index[self._num_orb_t:] + mono_b_model._norb

            # Build monolayer state positions
            self._mono_state_t = np.zeros((mono_t_model._nsta, 3), dtype=float)
            self._mono_state_t[:mono_t_model._norb] = self._mono_orb_t
            self._mono_state_t[mono_t_model._norb:] = self._mono_orb_t

            self._mono_state_b = np.zeros((mono_b_model._nsta, 3), dtype=float)
            self._mono_state_b[:mono_b_model._norb] = self._mono_orb_b
            self._mono_state_b[mono_b_model._norb:] = self._mono_orb_b

        elif (mono_t_model._nspin + mono_b_model._nspin) == 2:
            self._spin = False
            self._total_state_num = self._total_orb_num
            self._num_state_t = self._num_orb_t
            self._num_state_b = self._num_orb_b
            self._state_position = self._orb_position
            self._state_index = self._orb_index

            self._mono_state_t = self._mono_orb_t
            self._mono_state_b = self._mono_orb_b
        else:
            raise Exception("The number of spins in the upper and lower layers is different")

    def gen_one_r_ham(self, k, i, j):
        """
        Generate single Hamiltonian matrix element for real-space block.

        Parameters
        ----------
        k : int
            Index of R-vector in self._twist_hamR.
        i : int
            Row index (state index).
        j : int
            Column index (state index).

        Returns
        -------
        complex
            Hamiltonian matrix element H_{ij} for R-vector k.

        Notes
        -----
        Handles four cases:
        1. Diagonal intra-layer elements (k=0, same layer)
        2. Top layer intra-layer hopping
        3. Bottom layer intra-layer hopping
        4. Inter-layer coupling via t_inter function
        """
        # Diagonal intra-layer elements
        if i == j and k == 0 and (i <= self._num_state_t - 1):
            amp = self._mono_ham_up[0, self._state_index[i], self._state_index[j]]
        elif i == j and k == 0 and (i >= self._num_state_t):
            amp = self._mono_ham_dw[0, self._state_index[i], self._state_index[j]]

        # Top layer intra-layer hopping
        elif ((i <= self._num_state_t - 1) & (j <= self._num_state_t - 1)):
            R = self._twist_hamR[k, 0] * self._Lm[0] + \
                self._twist_hamR[k, 1] * self._Lm[1] + \
                self._state_position[j] - self._state_position[i] + \
                np.dot(self._mono_state_t[self._state_index[i]] -
                       self._mono_state_t[self._state_index[j]],
                       self._mono_lat_up)
            R = np.dot(R, np.linalg.inv(self._mono_lat_up))
            R = np.round(R).astype(int)

            mask = (self._mono_hamR_t[:, 0] == R[0]) & (self._mono_hamR_t[:, 1] == R[1])
            use_mono_ham = self._mono_ham_up[mask]

            if use_mono_ham.size == 0:
                amp = 0
            else:
                amp = use_mono_ham[0, self._state_index[i], self._state_index[j]]

        # Bottom layer intra-layer hopping
        elif ((i >= self._num_state_t) & (j >= self._num_state_t)):
            R = self._twist_hamR[k, 0] * self._Lm[0] + \
                self._twist_hamR[k, 1] * self._Lm[1] + \
                self._state_position[j] - self._state_position[i] + \
                np.dot(self._mono_state_b[self._state_index[i]] -
                       self._mono_state_b[self._state_index[j]],
                       self._mono_lat_dw)
            R = np.dot(R, np.linalg.inv(self._mono_lat_dw))
            R = np.round(R).astype(int)

            mask = (self._mono_hamR_b[:, 0] == R[0]) & (self._mono_hamR_b[:, 1] == R[1])
            use_mono_ham = self._mono_ham_dw[mask]

            if use_mono_ham.size == 0:
                amp = 0
            else:
                amp = use_mono_ham[0, self._state_index[i], self._state_index[j]]

        # Inter-layer coupling
        else:
            delta_R = self._twist_hamR[k, 0] * self._Lm[0] + \
                      self._twist_hamR[k, 1] * self._Lm[1] + \
                      self._state_position[j] - self._state_position[i]
            amp = self.t_inter(delta_R, self._state_index[i], self._state_index[j])

        return amp

    def gen_r_ham(self):
        """
        Generate dense real-space Hamiltonian blocks.

        Returns
        -------
        numpy.ndarray
            Dense Hamiltonian blocks (K x N x N) where:
            - K: number of R-vectors
            - N: total number of states

        Notes
        -----
        Uses triple nested loops, can be slow for large systems.
        Prints progress percentage during computation.
        """
        Rnum = len(self._twist_hamR)
        twist_ham = np.zeros((Rnum, self._total_state_num,
                              self._total_state_num), dtype=complex)

        for k in range(5):
            print(f"{int(100 * k / Rnum)}%")
            for i in range(self._total_state_num):
                for j in range(self._total_state_num):
                    twist_ham[k, i, j] = self.gen_one_r_ham(k, i, j)

        self._twist_ham = twist_ham
        return twist_ham

    def gen_r_ham_mulp(self, num_processes):
        """
        Generate dense real-space Hamiltonian blocks using multiprocessing.

        Parameters
        ----------
        num_processes : int
            Number of parallel processes to use.

        Returns
        -------
        numpy.ndarray
            Dense Hamiltonian blocks (K x N x N).

        Notes
        -----
        Distributes computation across multiple processes for speedup.
        Prints progress messages.
        """
        print("Starting to generate real space Hamiltonian")
        Rnum = len(self._twist_hamR)
        index_list = []

        # Create index list for parallel computation
        for k in range(Rnum):
            for i in range(self._total_state_num):
                for j in range(self._total_state_num):
                    use_index = (k, i, j)
                    index_list.append(use_index)

        # Execute parallel computation
        with mp.Pool(num_processes) as pool:
            results = pool.starmap(self.gen_one_r_ham, index_list)

        # Reconstruct Hamiltonian matrix
        results = np.array(results)
        index_list = np.array(index_list)
        twist_ham = np.zeros((Rnum, self._total_state_num,
                              self._total_state_num), dtype=complex)

        for idx, val in zip(index_list, results):
            k, i, j = idx
            twist_ham[k, i, j] = val

        self._twist_ham = twist_ham
        print("Real space Hamiltonian generation completed")
        return twist_ham

    def gen_r_ham_sparse_parallel(self, num_processes=None, drop_tol=1e-6,
                                  verbose=True, mp_start: str | None = None):
        """
        Parallel generation of sparse real-space Hamiltonian blocks.

        Parameters
        ----------
        num_processes : int or None, optional
            Number of parallel processes. If None, uses CPU count.
        drop_tol : float, optional
            Tolerance for dropping small matrix elements (default: 1e-6).
        verbose : bool, optional
            Print progress messages if True (default: True).
        mp_start : str or None, optional
            Multiprocessing start method (see pick_mp_context).

        Returns
        -------
        list of scipy.sparse.spmatrix
            Sparse Hamiltonian blocks for each R-vector.

        Notes
        -----
        Uses process pool with per-process caching of TwistTB instance.
        Suitable for large systems where dense matrices would be memory-intensive.
        """
        N = int(self._total_state_num)
        K = int(len(self._twist_hamR))

        if num_processes is None or num_processes <= 0:
            num_processes = max(1, os.cpu_count() or 1)

        ctx = pick_mp_context(mp_start)
        twist_ham_sparse = []

        for k in range(K):
            if verbose:
                print(f"[gen_r_ham_sparse_parallel] k={k}/{K - 1}")

            rows, cols, data = [], [], []

            with ctx.Pool(processes=num_processes,
                          initializer=_init_twist_inst,
                          initargs=(self,)) as pool:
                iterable = ((k, i, N, drop_tol) for i in range(N))
                ch = max(1, N // (32 * num_processes) or 1)

                for i, js, vals in pool.imap_unordered(_row_worker_sparse,
                                                       iterable,
                                                       chunksize=ch):
                    if js.size:
                        rows.extend([i] * js.size)
                        cols.extend(js.tolist())
                        data.extend(vals.tolist())

            Hk = coo_matrix((data, (rows, cols)), shape=(N, N)).tocsr()
            twist_ham_sparse.append(Hk)

        self._twist_ham_sparse = twist_ham_sparse
        return twist_ham_sparse

    def gen_k_ham_sparse(self, k):
        """
        Assemble sparse k-space Hamiltonian from precomputed real-space blocks.

        Parameters
        ----------
        k : array_like
            k-point in reciprocal space (3-component vector).

        Returns
        -------
        scipy.sparse.csr_matrix
            Sparse k-space Hamiltonian in CSR format.

        Raises
        ------
        RuntimeError
            If sparse real-space blocks have not been computed.

        Notes
        -----
        Performs Bloch sum: H(k) = Σ_R exp(i·2π·k·R) * H_R + h.c.
        """
        if not hasattr(self, "_twist_ham_sparse"):
            raise RuntimeError("Call gen_r_ham_sparse_parallel() first to build self._twist_ham_sparse.")

        ind_R_pos = np.array(self._twist_hamR)

        # Combine forward and backward R-vectors with their matrices
        use_mats = list(self._twist_ham_sparse) + \
                   [self._twist_ham_sparse[1 + i].T.conjugate()
                    for i in range(len(ind_R_pos) - 1)]
        ind_R_all = np.vstack([ind_R_pos, -ind_R_pos[1:]])

        # Compute Bloch phases
        phases = np.exp(2j * np.pi * (ind_R_all @ np.asarray(k)))

        # Sum over R-vectors
        H = None
        for phase, M in zip(phases, use_mats):
            H = M.copy().astype(np.complex128) * phase if H is None else (H + M * phase)

        return H.tocsr()

    def get_k_linear_operator(self, k):
        """
        Create LinearOperator for H(k) without assembling full matrix.

        Parameters
        ----------
        k : array_like
            k-point in reciprocal space (3-component vector).

        Returns
        -------
        scipy.sparse.linalg.LinearOperator
            Linear operator for matrix-vector operations with H(k).

        Notes
        -----
        Uses sparse blocks if available, otherwise falls back to dense blocks.
        Memory-efficient for iterative eigensolvers.
        """
        N = int(self._total_state_num)
        ind_R_pos = np.array(self._twist_hamR)
        phases_pos = np.exp(2j * np.pi * (ind_R_pos @ np.asarray(k)))

        if hasattr(self, "_twist_ham_sparse"):
            # Use sparse blocks
            H0 = self._twist_ham_sparse[0]
            HR_list = self._twist_ham_sparse[1:]

            def _matvec(x):
                y = H0 @ x
                for p, HR in zip(phases_pos[1:], HR_list):
                    y = y + p * (HR @ x) + np.conjugate(p) * (HR.T.conjugate() @ x)
                return y
        else:
            # Use dense blocks (fallback)
            use_ham = np.concatenate([self._twist_ham,
                                      self._twist_ham[1:].transpose((0, 2, 1)).conjugate()],
                                     axis=0)
            ind_R_all = np.vstack([ind_R_pos, -ind_R_pos[1:]])
            phases = np.exp(2j * np.pi * (ind_R_all @ np.asarray(k)))

            def _matvec(x):
                y = np.zeros_like(x, dtype=np.complex128)
                for p, H in zip(phases, use_ham):
                    y = y + p * (H @ x)
                return y

        def _rmatvec(x):
            """Adjoint matrix-vector multiplication"""
            return np.conjugate(_matvec(np.conjugate(x)))

        return LinearOperator(dtype=np.complex128, shape=(N, N),
                              matvec=_matvec, rmatvec=_rmatvec)

    def export_sparse_blocks(self, out_dir: str = "./twist_blocks",
                             overwrite: bool = True):
        """
        Export sparse Hamiltonian blocks and R-vectors to NPZ files.

        Parameters
        ----------
        out_dir : str, optional
            Output directory for NPZ files (default: "./twist_blocks").
        overwrite : bool, optional
            Overwrite existing files if True (default: True).

        Returns
        -------
        str
            Path to output directory.

        Raises
        ------
        RuntimeError
            If sparse blocks have not been computed.

        Notes
        -----
        Exported files allow child processes to load blocks lazily.
        Useful for distributed computation across multiple processes/nodes.
        """
        os.makedirs(out_dir, exist_ok=True)

        if not hasattr(self, "_twist_ham_sparse"):
            raise RuntimeError("Call gen_r_ham_sparse_parallel() first.")

        if (not overwrite) and os.path.exists(os.path.join(out_dir, "H0.npz")):
            return out_dir

        # Save sparse blocks
        save_npz(os.path.join(out_dir, "H0.npz"), self._twist_ham_sparse[0].tocsr())
        for m in range(1, 5):
            save_npz(os.path.join(out_dir, f"HR{m}.npz"),
                     self._twist_ham_sparse[m].tocsr())

        # Save R-vectors
        np.save(os.path.join(out_dir, "R_vectors.npy"),
                np.asarray(self._twist_hamR))

        self._sparse_out_dir = out_dir
        return out_dir

    def convert_dense_to_sparse_blocks(self, drop_tol: float = 1e-12,
                                       format: str = "csr", dtype=None,
                                       inplace: bool = True):
        """
        Convert dense real-space Hamiltonian blocks to sparse format.

        Parameters
        ----------
        drop_tol : float, optional
            Magnitude threshold for dropping entries (default: 1e-12).
        format : {"csr", "csc", "coo"}, optional
            Output sparse format (default: "csr").
        dtype : numpy.dtype or None, optional
            Data type for sparse matrices (default: None = keep from dense).
        inplace : bool, optional
            Store result in self._twist_ham_sparse if True (default: True).

        Returns
        -------
        list of scipy.sparse.spmatrix
            Sparse Hamiltonian blocks.

        Raises
        ------
        RuntimeError
            If dense blocks are not available.
        ValueError
            If dense blocks have incorrect shape.

        Notes
        -----
        Useful when dense blocks already exist and need sparse representation.
        For very large N, ensure dense blocks are available and reasonably sparse.
        """
        import numpy as _np
        from scipy.sparse import coo_matrix

        if not hasattr(self, "_twist_ham"):
            raise RuntimeError("Dense blocks `self._twist_ham` not found.")

        ham = self._twist_ham
        if ham.ndim != 3:
            raise ValueError(f"`self._twist_ham` must have shape [K,N,N], got {ham.shape}.")

        K, N1, N2 = ham.shape
        if N1 != N2:
            raise ValueError("Dense blocks must be square [K, N, N].")

        # Warn about R-vector mismatch
        if hasattr(self, "_twist_hamR") and len(self._twist_hamR) != K:
            import warnings as _warnings
            _warnings.warn(f"len(self._twist_hamR)={len(self._twist_hamR)} != K={K}; "
                           f"continuing with K from dense.")

        out_list = []
        for k in range(K):
            H = ham[k]
            if dtype is not None:
                H = H.astype(dtype, copy=False)

            # Convert to COO format and apply threshold
            coo = coo_matrix(H)
            if drop_tol > 0.0:
                mask = _np.abs(coo.data) > drop_tol
                coo = coo_matrix((coo.data[mask], (coo.row[mask], coo.col[mask])),
                                 shape=H.shape)

            sp = coo.asformat(format)
            sp.eliminate_zeros()
            out_list.append(sp)

        if inplace:
            self._twist_ham_sparse = out_list
            return self._twist_ham_sparse
        return out_list

    def convert_sparse_to_dense_blocks(self, dtype=None, order: str = "C",
                                       inplace: bool = True):
        """
        Convert sparse real-space Hamiltonian blocks back to dense format.

        Parameters
        ----------
        dtype : numpy.dtype or None, optional
            Target dtype for dense array (default: None = infer from sparse).
        order : {"C", "F"}, optional
            Memory layout of dense array (default: "C").
        inplace : bool, optional
            Store result in self._twist_ham if True (default: True).

        Returns
        -------
        numpy.ndarray
            Dense Hamiltonian blocks with shape [K, N, N].

        Raises
        ------
        RuntimeError
            If sparse blocks are not available.
        ValueError
            If sparse blocks have inconsistent shapes.

        Notes
        -----
        Simply calls `.toarray()` for each sparse block.
        For large N, ensure sufficient RAM is available.
        """
        import numpy as _np
        from scipy.sparse import spmatrix

        if not hasattr(self, "_twist_ham_sparse"):
            raise RuntimeError("Sparse blocks `self._twist_ham_sparse` not found.")

        sp_list = self._twist_ham_sparse
        if not isinstance(sp_list, (list, tuple)) or len(sp_list) == 0:
            raise ValueError("`self._twist_ham_sparse` must be a non-empty list of sparse matrices.")

        K = len(sp_list)
        if not isinstance(sp_list[0], spmatrix):
            raise TypeError("Elements of `self._twist_ham_sparse` must be scipy.sparse matrices.")

        N1, N2 = sp_list[0].shape
        if N1 != N2:
            raise ValueError("Sparse blocks must be square.")

        if dtype is None:
            dtype = _np.result_type(sp_list[0].dtype, _np.complex128)

        # Convert each sparse matrix to dense
        out = _np.empty((K, N1, N2), dtype=dtype, order=order)
        for k, M in enumerate(sp_list):
            if M.shape != (N1, N2):
                raise ValueError(f"Inconsistent block shape at k={k}: "
                                 f"got {M.shape}, expected {(N1, N2)}")
            out[k] = M.toarray().astype(dtype, copy=False, order=order)

        if inplace:
            self._twist_ham = out
            return self._twist_ham
        return out

    def prune_sparse_blocks(self, drop_tol: float = 1e-12, inplace: bool = True):
        """
        Remove tiny entries from sparse Hamiltonian blocks.

        Parameters
        ----------
        drop_tol : float, optional
            Magnitude threshold for removing entries (default: 1e-12).
        inplace : bool, optional
            Modify self._twist_ham_sparse in place if True (default: True).

        Returns
        -------
        list of scipy.sparse.spmatrix
            Pruned sparse blocks.

        Raises
        ------
        RuntimeError
            If sparse blocks are not available.

        Notes
        -----
        Useful after arithmetic operations that may introduce small numerical noise.
        """
        import numpy as _np
        from scipy.sparse import coo_matrix

        if not hasattr(self, "_twist_ham_sparse"):
            raise RuntimeError("Sparse blocks `self._twist_ham_sparse` not found.")

        pruned = []
        for M in self._twist_ham_sparse:
            coo = M.tocoo()
            if drop_tol > 0.0:
                mask = _np.abs(coo.data) > drop_tol
                coo = coo_matrix((coo.data[mask], (coo.row[mask], coo.col[mask])),
                                 shape=M.shape)
            sp = coo.tocsr()
            sp.eliminate_zeros()
            pruned.append(sp)

        if inplace:
            self._twist_ham_sparse = pruned
            return self._twist_ham_sparse
        return pruned

    def k_path(self, path, nk):
        """
        Generate k-point path along high-symmetry lines.

        Parameters
        ----------
        path : list or numpy.ndarray
            High-symmetry k-points in reciprocal coordinates (Nx2 or Nx3 array).
        nk : int
            Total number of k-points along the entire path.

        Returns
        -------
        k_vec : numpy.ndarray
            k-points along path (nk x 3 array).
        k_dist : numpy.ndarray
            Cumulative distance along path for each k-point.
        k_node : numpy.ndarray
            Distance of each high-symmetry point along path.

        Notes
        -----
        Uses metric from moiré reciprocal lattice for distance calculation.
        Automatically adds z-component if input is 2D.
        """
        # Convert to 3D if necessary
        path_2d = np.array(path)
        path_3d = np.zeros((len(path_2d), 3), dtype=float)
        path_3d[:, 0:2] = path_2d[:, 0:2]
        path = path_3d

        # Calculate metric for distance
        lat = self._Lm
        k_list = path
        k_metric = np.linalg.inv(np.dot(lat, lat.T))

        # Initialize arrays
        k_node = np.zeros(k_list.shape[0], dtype=float)
        k_dist = np.zeros(nk, dtype=float)
        k_vec = np.zeros((nk, k_list.shape[1]), dtype=float)
        k_vec[0] = k_list[0]

        # Calculate distances between high-symmetry points
        node_index = [0]
        for i in range(1, k_list.shape[0]):
            dk = k_list[i] - k_list[i - 1]
            dklen = np.sqrt(np.dot(dk, np.dot(k_metric, dk)))
            k_node[i] = k_node[i - 1] + dklen

        # Determine k-point indices for high-symmetry points
        for n in range(1, k_list.shape[0] - 1):
            frac = k_node[n] / k_node[-1]
            node_index.append(int(round(frac * (nk - 1))))
        node_index.append(nk - 1)

        # Generate k-points along each segment
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

        self._k_points = k_vec
        return k_vec, k_dist, k_node

    def gen_k_ham(self, k):
        """
        Generate k-space Hamiltonian at given k-point.

        Parameters
        ----------
        k : array_like
            k-point in reciprocal space (3-component vector).

        Returns
        -------
        numpy.ndarray
            Dense k-space Hamiltonian (N x N matrix).

        Notes
        -----
        Performs Bloch sum including both forward and backward R-vectors.
        Uses Hermitian conjugate for R ≠ 0 blocks.
        """
        # Combine forward and backward R-vectors
        ind_R = np.append(self._twist_hamR, -self._twist_hamR[1:], axis=0)
        use_ham = np.append(self._twist_ham,
                            self._twist_ham[1:].transpose(0, 2, 1).conj(),
                            axis=0)

        # Compute Bloch phases and sum
        ph = np.exp(2j * np.pi * (ind_R @ k))
        ham = np.tensordot(ph, use_ham, axes=(0, 0))

        return ham

    def gen_all_k_ham(self, kpoints):
        """
        Generate k-space Hamiltonians for multiple k-points.

        Parameters
        ----------
        kpoints : numpy.ndarray
            Array of k-points (M x 3 array).

        Returns
        -------
        numpy.ndarray
            Array of k-space Hamiltonians (M x N x N).
        """
        ham_k = np.zeros((len(kpoints), self._twist_ham.shape[1],
                          self._twist_ham.shape[2]), dtype=complex)

        for i in range(len(kpoints)):
            ham_k[i] = self.gen_k_ham(kpoints[i])

        return ham_k

    def solve_one_all(self, k_index):
        """
        Solve eigenvalue problem at single k-point index.

        Parameters
        ----------
        k_index : int
            Index of k-point in self._k_points.

        Returns
        -------
        numpy.ndarray
            Eigenvalues at specified k-point.
        """
        k = self._k_points[k_index]

        # Construct Bloch sum manually
        ind_R = np.append(np.array(self._twist_hamR),
                          np.array(-self._twist_hamR[1:]), axis=0)
        ham = np.zeros((self._twist_ham.shape[1],
                        self._twist_ham.shape[2]), dtype=complex)

        # Forward R-vectors
        for j in range(len(self._twist_hamR)):
            ham = ham + np.exp(2.j * np.pi * np.dot(ind_R[j], k)) * self._twist_ham[j]

        # Backward R-vectors (Hermitian conjugate)
        for j in range(1, len(self._twist_hamR)):
            ham = ham + np.exp(2.j * np.pi * np.dot(ind_R[j + 4], k)) * \
                  self._twist_ham[j].T.conjugate()

        # Solve eigenvalue problem
        w = np.real(np.linalg.eigvalsh(ham))
        return w

    def solve_all(self, kpoints, eig_vectors=False):
        """
        Solve eigenvalue problems for multiple k-points.

        Parameters
        ----------
        kpoints : numpy.ndarray
            Array of k-points (M x 3 array).
        eig_vectors : bool, optional
            Return eigenvectors if True (default: False).

        Returns
        -------
        numpy.ndarray or tuple
            If eig_vectors=False: eigenvalues (M x N array)
            If eig_vectors=True: (eigenvalues, eigenvectors) where
                eigenvalues: M x N array
                eigenvectors: M x N x N array
        """
        evals = np.zeros((len(kpoints), self._twist_ham.shape[1]), dtype=float)

        if eig_vectors:
            eigs = np.zeros((len(kpoints), self._twist_ham.shape[1],
                             self._twist_ham.shape[1]), dtype=complex)
            for i in range(len(kpoints)):
                evals[i], eigs[i] = np.linalg.eigh(self.gen_k_ham(kpoints[i]))
            return evals, eigs
        else:
            for i in range(len(kpoints)):
                evals[i] = np.real(np.linalg.eigvalsh(self.gen_k_ham(kpoints[i])))
            return evals

    def solve_all_mulp(self, num_processes):
        """
        Solve eigenvalue problems for all k-points using multiprocessing.

        Parameters
        ----------
        num_processes : int
            Number of parallel processes to use.

        Returns
        -------
        numpy.ndarray
            Eigenvalues for all k-points (M x N array).

        Notes
        -----
        Distributes k-points across processes for parallel diagonalization.
        """
        print("Starting to solve the Hamiltonian in k-space")
        index_list = range(len(self._k_points))

        with mp.Pool(num_processes) as pool:
            results = pool.map(self.solve_one_all, index_list)

        evals = np.array(results)
        print("k-space Hamiltonian generation completed")
        return evals

    def t_inter(self, R, i, j):
        """
        Calculate interlayer coupling between orbitals.

        Parameters
        ----------
        R : numpy.ndarray
            Relative displacement vector (3 components).
        i : int
            Orbital index in bottom layer (if R[2] > 0) or top layer (if R[2] < 0).
        j : int
            Orbital index in top layer (if R[2] > 0) or bottom layer (if R[2] < 0).

        Returns
        -------
        complex
            Interlayer coupling amplitude.

        Notes
        -----
        Uses Gaussian-like spatial decay with separate parameters for
        compression (d_1 < 0) and separation (d_1 > 0) regimes.
        """
        # Select parameters based on direction
        if R[2] > 0:
            h0 = self._h0[j, i]
            d0 = self._d0[j, i]
            r0 = self._r0[j, i]
        else:
            h0 = self._h0[i, j]
            d0 = self._d0[i, j]
            r0 = self._r0[i, j]

        # Calculate coupling with sign-dependent decay
        R = np.abs(R)
        d_1 = R[2] - d0
        symbol = np.sign(d_1)

        t = h0 * np.exp((-1 * symbol * (d_1 ** 2)) / (r0 ** 2)) * \
            np.exp((-1) * (R[0] * R[0] + R[1] * R[1]) / (r0 ** 2))

        return t

    def change_to_pythtb(self, if_range=False):
        """
        Convert TwistTB object to pythTB-compatible format.

        Parameters
        ----------
        if_range : bool, optional
            Reorder atoms by element type if True (default: False).

        Notes
        -----
        Converts internal representation to standard pythTB attributes.
        Handles spin degrees of freedom by reordering Hamiltonian blocks.
        """
        # Set basic attributes
        self._lat = self._Lm
        self._hamR = self._twist_hamR
        self._dim_r = 3
        self._nsta = self._total_state_num
        self._norb = self._total_orb_num
        self._natom = len(self._points)
        self._orb = np.dot(self._orb_position, np.linalg.inv(self._lat))
        self._atom_position = np.dot(self._points, np.linalg.inv(self._lat))
        self._atom_name = self._atom_name
        self._orb_name = self._orb_name

        # Handle spin degrees of freedom
        if self._spin:
            new_ham = np.zeros_like(self._twist_ham)

            n_o_t = self._num_orb_t
            n_o_b = self._num_orb_b
            tol_no = n_o_t + n_o_b
            n_s_t = self._num_state_t
            n_s_b = self._num_state_b

            # Reorder Hamiltonian blocks for spin-paired ordering
            new_ham[:, :n_o_t, n_o_t:n_o_t + n_o_b] = \
                self._twist_ham[:, :n_o_t, n_s_t:n_s_t + n_o_b]
            new_ham[:, :n_o_t, tol_no:tol_no + n_o_t] = \
                self._twist_ham[:, :n_o_t, n_o_t:n_s_t]
            new_ham[:, :n_o_t, tol_no + n_o_t:] = \
                self._twist_ham[:, :n_o_t, tol_no + n_o_t:]

            new_ham[:, n_o_t:tol_no, tol_no:tol_no + n_o_t] = \
                self._twist_ham[:, n_s_t:n_s_t + n_o_b, n_o_t:n_s_t]
            new_ham[:, n_o_t:tol_no, tol_no + n_o_t:] = \
                self._twist_ham[:, n_s_t:n_s_t + n_o_b, n_s_t + n_o_b:]

            new_ham[:, tol_no:tol_no + n_o_t, tol_no + n_o_t:] = \
                self._twist_ham[:, n_o_t:n_s_t, n_s_t + n_o_b:]

            new_ham[:, n_o_t:n_o_t + n_o_b, :n_o_t] = \
                self._twist_ham[:, n_s_t:n_s_t + n_o_b, :n_o_t]
            new_ham[:, tol_no:tol_no + n_o_t, :n_o_t] = \
                self._twist_ham[:, n_o_t:n_s_t, :n_o_t]
            new_ham[:, tol_no + n_o_t:, :n_o_t] = \
                self._twist_ham[:, tol_no + n_o_t:, :n_o_t]

            new_ham[:, tol_no:tol_no + n_o_t, n_o_t:tol_no] = \
                self._twist_ham[:, n_o_t:n_s_t, n_s_t:n_s_t + n_o_b]
            new_ham[:, tol_no + n_o_t:, n_o_t:tol_no] = \
                self._twist_ham[:, n_s_t + n_o_b:, n_s_t:n_s_t + n_o_b]
            new_ham[:, tol_no + n_o_t:, tol_no:tol_no + n_o_t] = \
                self._twist_ham[:, n_s_t + n_o_b:, n_o_t:n_s_t]

            # Diagonal blocks
            new_ham[:, :n_o_t, :n_o_t] = self._twist_ham[:, :n_o_t, :n_o_t]
            new_ham[:, n_o_t:tol_no, n_o_t:tol_no] = \
                self._twist_ham[:, n_s_t:n_s_t + n_o_b, n_s_t:n_s_t + n_o_b]
            new_ham[:, tol_no:tol_no + n_o_t, tol_no:tol_no + n_o_t] = \
                self._twist_ham[:, n_o_t:n_s_t, n_o_t:n_s_t]
            new_ham[:, tol_no + n_o_t:, tol_no + n_o_t:] = \
                self._twist_ham[:, n_s_t + n_o_b:, n_s_t + n_o_b:]

            self._ham = new_ham
            self._nspin = 2
        else:
            self._ham = self._twist_ham
            self._nspin = 1

        # Note: Atom reordering functionality commented out for now
        # if if_range:
        #     '''for homo'''
        #     re_atom_range_list = []
        #     atom_kind = np.unique(self._atom_name)
        #     for i in range(len(atom_kind)):
        #         for j in range(len(self._atom_name)):
        #             if atom_kind[i] == self._atom_name[j]:
        #                 re_atom_range_list.append(j)
        #     re_atom_range_list = np.array(re_atom_range_list, dtype=int)
        #
        #     trans_mat = np.zeros((len(self._atom_name), len(self._atom_name)), dtype=int)
        #     for i in range(len(self._atom_name)):
        #         trans_mat[i, re_atom_range_list[i]] = 1
        #
        #     new_atom_index = np.dot(trans_mat, self._index)
        #     new_points = np.zeros_like(self._points)
        #     new_points[:, 0] = np.dot(trans_mat, self._points[:, 0])
        #     new_points[:, 1] = np.dot(trans_mat, self._points[:, 1])
        #     new_points[:, 2] = np.dot(trans_mat, self._points[:, 2])
        #
        #     orb_trans_mat = np.zeros((self._total_orb_num, self._total_orb_num), dtype=int)
        #     iii = 0
        #     jjj = 0
        #     for i in range(len(self._points)):
        #         for j in range(len(new_points)):
        #             orb_trans_mat[iii:iii+self._mono_atom_list[self._index[i]], jjj:jjj]
        #
        #     orb_trans_mat = np.zeros((), dtype=int)
        #     debug = 1

    def output(self, path=".", prefix="wannier90", isparse=False):
        """
        Output tight-binding model in Wannier90 format.

        Parameters
        ----------
        path : str, optional
            Output directory path (default: current directory).
        prefix : str, optional
            Filename prefix (default: "wannier90").

        Notes
        -----
        Generates three files:
        1. prefix + "_hr.dat": Hamiltonian in Wannier90 format
        2. prefix + "_centres.xyz": Orbital and atomic positions
        3. prefix + ".win": Wannier90 input file
        """
        self.change_to_pythtb(if_range=True)

        # Prepare R-vectors and Hamiltonian
        R0 = np.append(self._hamR, -self._hamR[1:], axis=0)
        n_R = len(R0)

        # Ensure 3D R-vectors
        if self._dim_r == 2:
            R = np.append(R0, np.array([np.zeros(n_R, dtype=int)]).T, axis=1)
        elif self._dim_r == 1:
            R = np.append(R0, np.zeros((n_R, 2), dtype=int), axis=1)
        else:
            R = R0

        # Combine forward and backward blocks
        ham = np.append(self._ham, self._ham[1:].transpose(0, 2, 1).conjugate(), axis=0)

        # Sort R-vectors by (100a + 10b + c) convention
        arg = np.argsort(np.dot(R, [100, 10, 1]), axis=0)
        R = R[arg]
        ham = ham[arg]

        # Write Hamiltonian file
        n_line = int(n_R / 15)
        n0 = int(n_R % 15)

        with open(path + "/" + prefix + "_hr.dat", "w") as f:
            f.write("writen by MoireStudio\n")
            f.write("         " + str(int(self._nsta)) + "\n")
            f.write("         " + str(int(n_R)) + "\n")

            # Write formatting line
            for i in range(n_line):
                f.write("    1    1    1    1    1    1    1    1    1    1    1    1    1    1    1\n")
            for i in range(n0):
                f.write("    1")
            f.write("\n")

            # Write Hamiltonian elements
            for i in range(n_R):
                for j in range(self._nsta):
                    for k in range(self._nsta):
                        for i0 in range(3):
                            if R[i, i0] < 0:
                                f.write("   " + str(R[i, i0]))
                            else:
                                f.write("    " + str(R[i, i0]))

                        f.write("    " + str(j + 1))
                        f.write("    " + str(k + 1))

                        # Real part with formatting
                        if "-" in "%.6f" % ham[i, j, k].real:
                            f.write("   %.6f" % ham[i, j, k].real)
                        else:
                            f.write("    %.6f" % ham[i, j, k].real)

                        # Imaginary part with formatting
                        if "-" in "%.6f" % ham[i, j, k].imag:
                            f.write("   %.6f\n" % ham[i, j, k].imag)
                        else:
                            f.write("    %.6f\n" % ham[i, j, k].imag)

        # Write orbital centers file
        n0 = int(self._norb + self._natom)
        with open(path + "/" + prefix + "_centres.xyz", "w") as f:
            f.write("    " + str(n0) + " \n")
            f.write("writen by MoireStudio\n")

            # Convert to Cartesian coordinates
            if self._dim_r != 3:
                orb = np.append(self._orb, np.zeros((self._norb, 3 - self._dim_r)), axis=1)
                atom_position = np.append(self._atom_position,
                                          np.zeros((self._natom, 3 - self._dim_r)), axis=1)
            else:
                orb = self._orb
                atom_position = self._atom_position

            orb = np.dot(orb, self._lat)
            atom_position = np.dot(atom_position, self._lat)

            # Write orbital positions
            for i in range(self._norb):
                f.write("X")
                for j in range(3):
                    f.write("         ")
                    if "-" in "%.6f" % orb[i, j]:
                        f.write("%.6f" % orb[i, j])
                    else:
                        f.write(" %.6f" % orb[i, j])
                f.write("\n")

            # Write spin-down orbitals if spin-polarized
            if self._nspin == 2:
                for i in range(self._norb):
                    f.write("X")
                    for j in range(3):
                        f.write("         ")
                        if "-" in "%.6f" % orb[i, j]:
                            f.write("%.6f" % orb[i, j])
                        else:
                            f.write(" %.6f" % orb[i, j])
                    f.write("\n")

            # Write atomic positions
            for i in range(self._natom):
                use_name = self._atom_name[i]
                f.write(use_name)
                for j in range(3):
                    f.write("         ")
                    if "-" in "%.6f" % atom_position[i, j]:
                        f.write("%.6f" % atom_position[i, j])
                    else:
                        f.write(" %.6f" % atom_position[i, j])
                f.write("\n")

        # Write Wannier90 input file
        with open(path + "/" + prefix + ".win", "w") as f:
            f.write("begin unit_cell_cart\n")
            for i in range(3):
                for j in range(3):
                    f.write("%.6f    " % self._lat[i, j])
                f.write("\n")
            f.write("end unit_cell_cart\n")

            f.write("begin atoms_cart\n")
            for i in range(self._natom):
                atom0 = np.dot(self._atom_position[i], self._lat)
                use_name = self._atom_name[i]
                f.write(use_name + "    ")
                for j in range(3):
                    f.write("%.6f    " % atom0[j])
                f.write("\n")
            f.write("end atoms_cart\n")

            f.write("begin projections\n")
            atom_name = np.unique(self._atom_name)
            for i in range(len(atom_name)):
                use_name = atom_name[i]
                use_orb_list = self._orb_name[use_name]
                out_orb = use_orb_list[0]
                for j in range(1, len(use_orb_list)):
                    out_orb = out_orb + ";" + use_orb_list[j]
                f.write(use_name + ":" + out_orb + "\n")
            f.write("end projections\n")

            if self._nspin == 2:
                f.write("spinors = .true.")

    def magnetism(self, zeem, shift, intra_layer_m):
        """
        Apply magnetic field and exchange coupling terms.

        Parameters
        ----------
        zeem : float
            Zeeman splitting strength (opposite sign for top/bottom layers).
        shift : float
            Uniform energy shift for all states.
        intra_layer_m : float
            Intra-layer exchange coupling (alternating sign within each layer).

        Notes
        -----
        Adds terms to diagonal Hamiltonian elements:
        1. Zeeman splitting: +zeem for top layer, -zeem for bottom layer
        2. Uniform shift: +shift for all states
        3. Intra-layer exchange: alternating ±intra_layer_m within each layer
        """
        for i in range(self._twist_ham.shape[1]):
            # Top layer
            if (i < self._twist_ham.shape[1] // 2):
                self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + zeem + shift
                if i % 2 == 0:
                    self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + intra_layer_m
                else:
                    self._twist_ham[0, i, i] = self._twist_ham[0, i, i] - intra_layer_m
            # Bottom layer
            else:
                self._twist_ham[0, i, i] = self._twist_ham[0, i, i] - zeem + shift
                if i % 2 == 0:
                    self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + intra_layer_m
                else:
                    self._twist_ham[0, i, i] = self._twist_ham[0, i, i] - intra_layer_m

    def magnetic_moment(self, M_t_list, M_b_list):
        """
        Apply orbital-dependent magnetic moments.

        Parameters
        ----------
        M_t_list : numpy.ndarray
            Magnetic moments for top layer orbitals.
        M_b_list : numpy.ndarray
            Magnetic moments for bottom layer orbitals.

        Notes
        -----
        Adds orbital-specific magnetic moments to diagonal Hamiltonian elements.
        M_t_list and M_b_list should have length equal to number of orbitals
        in respective monolayers.
        """
        for i in range(len(self._orb_index)):
            # Top layer
            if (i < self._twist_ham.shape[1] // 2):
                self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + \
                                           M_t_list[self._orb_index[i]]
            # Bottom layer
            else:
                self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + \
                                           M_b_list[self._orb_index[i]]

    def electric_field(self, E):
        """
        Apply perpendicular electric field.

        Parameters
        ----------
        E : float
            Electric field strength (energy per unit length).

        Notes
        -----
        Adds electrostatic potential V(z) = E·z to diagonal Hamiltonian elements.
        z-coordinates are shifted so minimum z = 0.
        """
        orb_dz = self._orb_position[:, 2] - np.min(self._orb_position[:, 2])
        for i in range(len(orb_dz)):
            self._twist_ham[0, i, i] = self._twist_ham[0, i, i] + E * orb_dz[i]