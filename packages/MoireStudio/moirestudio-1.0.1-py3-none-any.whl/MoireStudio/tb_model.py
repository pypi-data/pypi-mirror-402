"""
Tight-binding model class for electronic structure calculations.

This module defines the tb_model class which represents a tight-binding model
for electronic structure calculations. It includes methods for setting up
the model, calculating band structures, and various transformations.
"""

import functools
from multiprocessing import Pool
from typing import List, Optional, Tuple, Union
import numpy as np


class tb_model:
    """
    Tight-binding model class.

    This class represents a tight-binding Hamiltonian in real space
    with periodic boundary conditions in selected directions.

    Attributes:
        _dim_k: Dimension of k-space (number of periodic directions).
        _dim_r: Dimension of real space.
        _lat: Lattice vectors (dim_r × dim_r array).
        _orb: Orbital positions in fractional coordinates (norb × dim_r array).
        _norb: Number of orbitals.
        _per: List of periodic directions.
        _nspin: Number of spin components (1 or 2).
        _nsta: Total number of states (norb × nspin).
        _ham: Hamiltonian matrices for each R-vector (nR × nsta × nsta).
        _hamR: R-vectors for each Hamiltonian term (nR × dim_r).
        _atom: List of atoms (number of orbitals per atom).
        _natom: Number of atoms.
        _atom_position: Atom positions in fractional coordinates.
        _atom_name: Atom names.
        _orb_name: Orbital names per atom.
        _atom_list: List of atoms (same as _atom, for compatibility).
        _model_type: Type of model.
    """

    def __init__(
        self,
        k_dim: int,
        r_dim: int,
        lat: Optional[np.ndarray] = None,
        orb: Optional[Union[int, np.ndarray]] = None,
        per: Optional[List[int]] = None,
        atom_list: Optional[List[int]] = None,
        atom_position: Optional[np.ndarray] = None,
        atom_name: Optional[List[str]] = None,
        orb_name: Optional[dict] = None,
        nspin: int = 1,
    ) -> None:
        """
        Initialize tight-binding model.

        Args:
            k_dim: Dimension of k-space (number of periodic directions).
            r_dim: Dimension of real space.
            lat: Lattice vectors (r_dim × r_dim array).
            orb: Orbital positions (norb × r_dim array) or number of orbitals.
            per: List of periodic directions (default: first k_dim directions).
            atom_list: List of atoms (number of orbitals per atom).
            atom_position: Atom positions in fractional coordinates.
            atom_name: Atom names.
            orb_name: Orbital names per atom.
            nspin: Number of spin components (1 or 2).

        Raises:
            Exception: For various input validation errors.
        """
        # Validate k_dim
        if type(k_dim).__name__ != "int":
            raise Exception("\n\nArgument dim_k not an integer")
        if k_dim < 0 or k_dim > 4:
            raise Exception(
                "\n\nArgument dim_k out of range. Must be between 0 and 4."
            )
        self._dim_k = k_dim

        # Validate r_dim
        if type(r_dim).__name__ != "int":
            raise Exception("\n\nArgument dim_r not an integer")
        if r_dim < 0 or r_dim > 4:
            raise Exception(
                "\n\nArgument dim_r out of range. Must be between 0 and 4."
            )
        self._dim_r = r_dim

        # Validate and set lattice vectors
        if type(lat).__name__ not in ["list", "ndarray"]:
            raise Exception("\n\nArgument lat is not a list.")
        else:
            self._lat = np.array(lat, dtype=float)
            if self._lat.shape != (r_dim, r_dim):
                raise Exception("\n\nWrong lat array dimensions")

        if r_dim > 0:
            if np.abs(np.linalg.det(self._lat)) < 1.0e-6:
                raise Exception(
                    "\n\nLattice vectors length/area/volume too close to zero, or zero."
                )
            if np.linalg.det(self._lat) < 0.0:
                raise Exception(
                    "\n\nLattice vectors need to form right handed system."
                )

        # Validate and set orbitals
        if orb is None:
            self._norb = 1
            self._orb = np.zeros((1, r_dim))
            print(
                " Orbital positions not specified. I will assume a single orbital at the origin."
            )
        elif type(orb).__name__ == "int":
            self._norb = orb
            self._orb = np.zeros((orb, r_dim))
        elif type(orb).__name__ not in ["list", "ndarray"]:
            raise Exception("\n\nArgument orb is not a list or an integer")
        else:
            self._orb = np.array(orb, dtype=float)
            if len(self._orb.shape) != 2:
                raise Exception("\n\nWrong orb array rank")
            self._norb = self._orb.shape[0]  # number of orbitals
            if self._orb.shape[1] != r_dim:
                raise Exception("\n\nWrong orb array dimensions")

        # Set periodic directions
        if per is None:
            # by default first _dim_k dimensions are periodic
            self._per = list(range(self._dim_k))
        else:
            if len(per) != self._dim_k:
                raise Exception(
                    "\n\nWrong choice of periodic/infinite direction!"
                )
            # store which directions are the periodic ones
            self._per = per

        # Validate and set spin
        if nspin not in [1, 2]:
            raise Exception("\n\nWrong value of nspin, must be 1 or 2!")
        self._nspin = nspin

        # by default, assume model did not come from w90 object and that
        # position operator is diagonal
        self._assume_position_operator_diagonal = True
        self._nsta = self._norb * self._nspin
        self._ham = np.zeros((1, self._nsta, self._nsta), dtype=complex)
        self._hamR = np.zeros((1, self._dim_r), dtype=int)

        # Set up atom information
        if atom_list is None:
            if atom_position is not None:
                raise Exception("Wrong, you should input the atom_list")
            else:
                self._atom = [1]
                self._atom_position = [self._orb[0]]
                for a in range(1, self._norb):
                    if np.any(
                        np.linalg.norm(self._orb[a] - self._atom_position, axis=1)
                        < 1e-1
                    ):
                        index = np.argwhere(
                            np.linalg.norm(
                                self._orb[a] - self._atom_position, axis=1
                            )
                            < 1e-1
                        )
                        self._atom[-1] += 1
                    else:
                        self._atom.append(1)
                        self._atom_position.append(self._orb[a])
            self._atom_position = np.array(self._atom_position)
            self._atom = np.array(self._atom, dtype=int)
            self._natom = int(len(self._atom))
        else:
            self._atom = np.array(atom_list, dtype=int)
            self._natom = len(atom_list)
            if atom_position is None:
                raise Exception("Wrong, you should input the atom_position")
            else:
                if len(atom_position) != self._natom:
                    raise Exception(
                        "Wrong, the atom_list's length must equal to atom_position"
                    )
                else:
                    atom_position = np.array(atom_position)
                    for atom in atom_position:
                        if (
                            np.sum(
                                np.linalg.norm(atom - atom_position, axis=1) < 1e-5
                            )
                            > 1
                        ):
                            raise Exception(
                                "Wrong, have two atom position locals too short"
                            )
                    self._atom_position = np.array(atom_position)

        self._atom_name = atom_name
        self._orb_name = orb_name
        self._atom_list = atom_list
        self._model_type = "mono_tb"

    def set_hop(
        self,
        tmp: Union[complex, np.ndarray],
        ind: List[int],
        ind_R: List[int],
        mode: str = "set",
        conjugate_set: bool = True,
    ) -> None:
        """
        Set hopping term in the Hamiltonian.

        Args:
            tmp: Hopping amplitude (complex scalar or 2×2 matrix for spin).
            ind: Pair of orbital indices [i, j].
            ind_R: R-vector for the hopping term.
            mode: 'set', 'add', or 'reset'.
            conjugate_set: Whether to automatically set the conjugate term.

        Raises:
            Exception: For various input validation errors.
        """
        ind = np.array(ind, dtype=int)
        ind_R = np.array(ind_R, dtype=int)

        if np.any(ind < 0) or np.any(ind >= self._norb):
            raise Exception("\n\nIndex ind out of scope.")
        if len(ind) != 2:
            raise Exception("\n\n length of ind need to be 2")
        if len(ind_R) != self._dim_r:
            raise Exception("\n\n Wrong, the length of ind_R must equal to dim_r")

        # Check diagonal terms at R=0 must be real
        if np.all(ind_R == 0) and ind[0] == ind[1]:
            if type(tmp).__name__ == "complex" and tmp.imag != 0:
                raise Exception(
                    "\n\n Wrong, the diagonal of [0,0,0] hamiltonian must be real"
                )
            elif type(tmp).__name__ in ["list", "ndarray"]:
                tmp = np.array(tmp)
                if tmp.shape[0] != tmp.shape[1]:
                    raise Exception("\n\n Wrong, you must use pauli matrix")
                for i in range(len(tmp)):
                    if type(tmp[i, i]).__name__ == "complex" and tmp[i, i].imag != 0:
                        raise Exception(
                            "\n\n Wrong, the diagonal of [0,0,0] hamiltonian must be real"
                        )

        useham = np.zeros((self._norb, self._norb), dtype=complex)
        if self._nspin == 2:
            useham[ind[0], ind[1]] = 1
            if type(tmp).__name__ in ["list", "ndarray"]:
                useham = np.kron(tmp, useham)
            else:
                useham = np.kron(tmp * np.identity(2), useham)
        else:
            if type(tmp).__name__ in ["list", "ndarray"]:
                raise Exception("\n\n Wrong, using the pauli matrix must take spin=2")
            useham[ind[0], ind[1]] = tmp

        # Add conjugate term if needed
        if np.all(ind_R == 0) and ind[0] != ind[1] and conjugate_set:
            useham += useham.T.conjugate()

        if mode.lower() == "add":
            if np.any(np.all(self._hamR == ind_R, axis=1)):
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[[0]]
                self._ham[index] += useham
            elif np.any(np.all(self._hamR == -ind_R, axis=1)):
                ind_R *= -1
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[[0]]
                self._ham[index] += useham.transpose().conjugate()
            else:
                self._hamR = np.append(self._hamR, [ind_R], axis=0)
                self._ham = np.append(self._ham, [useham], axis=0)

        elif mode.lower() == "set":
            if np.any(np.all(self._hamR == ind_R, axis=1)):
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[0, 0]
                a = np.sum(self._ham[index] * useham)
                if a != 0:
                    raise Exception(
                        "\n\n Wrong, the mode=set but the value had be setted, please use add or reset"
                    )
                self._ham[index] += useham
            elif np.any(np.all(self._hamR == -ind_R, axis=1)):
                ind_R *= -1
                useham = useham.transpose().conjugate()
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[[0]]
                a = np.sum(self._ham[index] * useham)
                if a != 0:
                    raise Exception(
                        "\n\n Wrong, the mode=set but the value had be setted, please use add or reset"
                    )
                self._ham[index] += useham
            else:
                self._hamR = np.append(self._hamR, [ind_R], axis=0)
                self._ham = np.append(self._ham, [useham], axis=0)

        elif mode.lower() == "reset":
            if np.any(np.all(self._hamR == ind_R, axis=1)):
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[[0]]
                self._ham[index] = (
                    self._ham[index]
                    + useham
                    - self._ham[index] * np.array(useham != 0, dtype=complex)
                )
            elif np.any(np.all(self._hamR == -ind_R, axis=1)):
                ind_R *= -1
                index = np.argwhere(np.all(self._hamR == ind_R, axis=1))[[0]]
                useham = useham.transpose().conjugate()
                self._ham[index] = (
                    self._ham[index]
                    + useham
                    - self._ham[index] * np.array(useham != 0, dtype=complex)
                )
            else:
                self._hamR = np.append(self._hamR, [ind_R], axis=0)
                self._ham = np.append(self._ham, [useham], axis=0)
        else:
            raise Exception("mode must be set, add or reset, not other")

    def set_onsite(
        self,
        onsite: Union[List[complex], complex],
        ind: Optional[int] = None,
        mode: str = "set",
    ) -> None:
        """
        Set onsite energy term(s).

        Args:
            onsite: Onsite energy value(s).
            ind: Orbital index (if None, set all orbitals).
            mode: 'set', 'add', or 'reset'.

        Raises:
            Exception: For various input validation errors.
        """
        if ind is None:
            if len(onsite) != self._norb:
                raise Exception("\n\nWrong number of site energies")
        if ind is not None:
            if ind < 0 or ind > self._norb:
                raise Exception("\n\nIndex ind out of scope.")

        if ind is None:
            if self._dim_r != 0:
                ind_R = np.zeros(self._dim_r, dtype=int)
                for i in range(len(onsite)):
                    self.set_hop(onsite[i], [i, i], ind_R, mode=mode)
            else:
                for i in range(len(onsite)):
                    self.set_hop(onsite[i], [i, i], mode=mode)
        else:
            if self._dim_r != 0:
                ind_R = np.zeros(self._dim_r, dtype=int)
                self.set_hop(onsite[ind], [ind, ind], ind_R, mode=mode)
            else:
                self.set_hop(onsite[ind], [ind, ind], mode=mode)

    def k_path(
        self,
        kpts: Union[str, np.ndarray],
        nk: int,
        knode_index: bool = False,
    ) -> Union[Tuple[np.ndarray, np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """
        Generate k-point path for band structure calculation.

        Args:
            kpts: String identifier or array of k-points.
            nk: Number of k-points along the path.
            knode_index: Whether to return node indices.

        Returns:
            Tuple containing:
                k_vec: k-point vectors along the path.
                k_dist: Distances along the path.
                k_node: Distances to high-symmetry points.
                (Optional) node_index: Indices of high-symmetry points.

        Raises:
            Exception: For various input validation errors.
        """
        if self._dim_k == 0:
            raise Exception("the model's k dimension is zero, do not use k")
        elif self._dim_k == 1:
            if kpts == "full":
                k_list = np.array([[0.0], [0.5], [1.0]])
            elif kpts == "fullc":
                k_list = np.array([[-0.5], [0.0], [0.5]])
            elif kpts == "half":
                k_list = np.array([[0.0], [0.5]])
            else:
                k_list = np.array(kpts)
        else:
            k_list = np.array(kpts)

        if k_list.shape[1] != self._dim_k:
            raise Exception("\n\n k-space dimension do not match")
        if nk < k_list.shape[0]:
            raise Exception(
                "\n\n please set more n_k, at least more than the number of k_list"
            )

        n_nodes = k_list.shape[0]
        lat_per = np.copy(self._lat)[self._per]
        k_metric = np.linalg.inv(np.dot(lat_per, lat_per.T))

        # Calculate distances along the path
        k_node = np.zeros(n_nodes, dtype=float)
        for n in range(1, n_nodes):
            dk = k_list[n] - k_list[n - 1]
            dklen = np.sqrt(np.dot(dk, np.dot(k_metric, dk)))
            k_node[n] = k_node[n - 1] + dklen

        # Find indices of high-symmetry points
        node_index = [0]
        for n in range(1, n_nodes - 1):
            frac = k_node[n] / k_node[-1]
            node_index.append(int(round(frac * (nk - 1))))
        node_index.append(nk - 1)

        # Generate k-points along the path
        k_dist = np.zeros(nk, dtype=float)
        k_vec = np.zeros((nk, self._dim_k), dtype=float)
        k_vec[0] = k_list[0]

        for n in range(1, n_nodes):
            n_i = node_index[n - 1]
            n_f = node_index[n]
            kd_i = k_node[n - 1]
            kd_f = k_node[n]
            k_i = k_list[n - 1]
            k_f = k_list[n]
            for j in range(n_i, n_f + 1):
                frac = float(j - n_i) / float(n_f - n_i)
                k_dist[j] = kd_i + frac * (kd_f - kd_i)
                k_vec[j] = k_i + frac * (k_f - k_i)

        if knode_index is False:
            return k_vec, k_dist, k_node
        else:
            node_index = np.array(node_index, dtype=int)
            return k_vec, k_dist, k_node, node_index

    def gen_ham(
        self, k_point: Optional[np.ndarray] = None, gauge: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate Hamiltonian matrix at given k-point(s).

        Args:
            k_point: k-point(s) at which to compute Hamiltonian.
            gauge: Whether to apply phase factors (gauge transformation).

        Returns:
            Hamiltonian matrix (or list of matrices for multiple k-points).

        Raises:
            Exception: For various input validation errors.
        """
        if k_point is None:
            if self._dim_k == 0:
                return self._ham[0]
            else:
                raise Exception(
                    "\n\n Wrong,the dim_k isn't 0, please input k_point"
                )
        else:
            k_point = np.array(k_point)
            if len(k_point.shape) == 2:
                lists = True
                if k_point.shape[1] != self._dim_k:
                    raise Exception(
                        "Wrong, the shape of k_point must equal to dim_k"
                    )
            else:
                lists = False
                if k_point.shape[0] != self._dim_k:
                    raise Exception(
                        "Wrong, the shape of k_point must equal to dim_k"
                    )

        orb = np.array(self._orb)[:, self._per]

        # Ensure R=0 term is first
        if np.any(self._hamR[0] != 0):
            a11 = np.all(self._hamR == 0, axis=1)
            index = np.argwhere(a11)  # [0, 0]
            if index.shape[0] == 0:
                self._ham = np.append(
                    self._ham,
                    np.zeros((self._nsta, self._nsta), dtype=complex),
                    axis=0,
                )
                self._hamR = np.append(
                    self._hamR, np.zeros(self._dim_r, dtype=int), axis=0
                )
                index = self._hamR.shape[0]
            ins = np.copy(self._ham[index])
            ind = np.copy(self._hamR[0])
            self._ham[index] = np.copy(self._ham[0])
            self._hamR[index] = ind
            self._ham[0] = ins
            self._hamR[0] *= 0

        ind_R = self._hamR[:, self._per]
        useham = self._ham

        if gauge:
            if lists:
                ham = np.zeros(
                    (len(k_point), self._nsta, self._nsta), dtype=complex
                )
                for i, k in enumerate(k_point):
                    ham[i] = np.sum(
                        np.exp(2.0j * np.pi * np.dot(ind_R, k))[:, None, None]
                        * useham,
                        axis=0,
                    )
                    U = np.diag(np.exp(2.0j * np.pi * np.dot(orb, k)))
                    if self._nspin == 2:
                        U = np.kron([[1, 0], [0, 1]], U)
                    ham[i] = np.dot(ham[i], U)
                    ham[i] = np.dot(U.T.conjugate(), ham[i])
            else:
                ham = np.sum(
                    np.exp(2.0j * np.pi * np.dot(ind_R, k_point))[
                        :, None, None
                    ]
                    * useham,
                    axis=0,
                )
                U = np.diag(np.exp(2.0j * np.pi * np.dot(orb, k_point)))
                if self._nspin == 2:
                    U = np.kron([[1, 0], [0, 1]], U)
                ham = np.dot(ham, U)
                ham = np.dot(U.T.conjugate(), ham)
        else:
            if lists:
                ham = np.zeros(
                    (len(k_point), self._nsta, self._nsta), dtype=complex
                )
                for i, k in enumerate(k_point):
                    ham[i] = np.sum(
                        np.exp(2.0j * np.pi * np.dot(ind_R, k))[
                            :, None, None
                        ]
                        * useham,
                        axis=0,
                    )
            else:
                ham = np.sum(
                    np.exp(2.0j * np.pi * np.dot(ind_R, k_point))[
                        :, None, None
                    ]
                    * useham,
                    axis=0,
                )
        return ham

    def solve_one(
        self,
        k_point: Optional[np.ndarray] = None,
        eig_vectors: bool = False,
        gauge: bool = True,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Solve eigenvalue problem at a single k-point.

        Args:
            k_point: k-point vector.
            eig_vectors: Whether to return eigenvectors.
            gauge: Whether to apply gauge transformation.

        Returns:
            Eigenvalues (and eigenvectors if eig_vectors=True).

        Raises:
            Exception: For various input validation errors.
        """
        if self._dim_k == 0 and k_point is not None:
            raise Exception(
                "Wrong, the dimension of k is zero,please don't set k_point"
            )
        elif k_point is None and self._dim_k != 0:
            raise Exception(
                "Wrong, the dimension of k is not zero, please set k_point"
            )

        if k_point is not None:
            k_point = np.array(k_point)
            if len(k_point.shape) != 1:
                raise Exception(
                    "Wrong, the shape of k_point must be (dim_k,), or please use solve_all"
                )
            if len(k_point) != self._dim_k:
                raise Exception(
                    "Wrong, the shape of k_point must equal to dim_k"
                )
            useham = self.gen_ham(k_point, gauge=gauge)
        else:
            useham = self.gen_ham(gauge=gauge)

        if eig_vectors:
            (evals, evec) = np.linalg.eigh(useham)
            index = np.argsort(evals)
            evals = evals[index]
            evec = evec[:, index]
            evec = evec.T
            return (evals, evec)
        else:
            evals = np.linalg.eigvalsh(useham)
            index = np.argsort(evals)
            evals = evals[index]
            return evals

    def solve_all(
        self,
        k_point: Optional[np.ndarray] = None,
        eig: bool = False,
        gauge: bool = True,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Solve eigenvalue problem at multiple k-points.

        Args:
            k_point: Array of k-points.
            eig: Whether to return eigenvectors.
            gauge: Whether to apply gauge transformation.

        Returns:
            Eigenvalues (and eigenvectors if eig=True).

        Raises:
            Exception: For various input validation errors.
        """
        if self._dim_k == 0 and k_point is not None:
            raise Exception(
                "Wrong, the dimension of k is zero,please don't set k_point"
            )
        elif k_point is None and self._dim_k != 0:
            raise Exception(
                "Wrong, the dimension of k is not zero, please set k_point"
            )

        if k_point is not None:
            k_point = np.array(k_point)
            if len(k_point.shape) != 2:
                raise Exception(
                    "Wrong, the shape of k_point must be (dim_k,), or please use solve_one"
                )
            if k_point.shape[1] != self._dim_k:
                raise Exception(
                    "Wrong, the shape of k_point must equal to dim_k"
                )
            useham = self.gen_ham(k_point, gauge=gauge)
        else:
            useham = self.gen_ham(gauge=gauge)

        if eig:
            (evals, evec) = np.linalg.eigh(useham)
            return (evals, evec)
        else:
            evals = np.linalg.eigvalsh(useham)
            return evals

    def solve_all_parallel(
        self,
        k_point: Optional[np.ndarray] = None,
        eig: bool = False,
        gauge: bool = True,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Solve eigenvalue problem at multiple k-points in parallel.

        Args:
            k_point: Array of k-points.
            eig: Whether to return eigenvectors.
            gauge: Whether to apply gauge transformation.

        Returns:
            Eigenvalues (and eigenvectors if eig=True).

        Raises:
            Exception: For various input validation errors.
        """
        if self._dim_k == 0 and k_point is not None:
            raise Exception(
                "Wrong, the dimension of k is zero,please don't set k_point"
            )
        elif k_point is None and self._dim_k != 0:
            raise Exception(
                "Wrong, the dimension of k is not zero, please set k_point"
            )

        if k_point is not None:
            k_point = np.array(k_point)
            if len(k_point.shape) != 2:
                raise Exception(
                    "Wrong, the shape of k_point must be (dim_k,), or please use solve_one"
                )
            if k_point.shape[1] != self._dim_k:
                raise Exception(
                    "Wrong, the shape of k_point must equal to dim_k"
                )

            genham = functools.partial(self.gen_ham, gauge=gauge)
            pool = Pool()
            useham = pool.map(self.gen_ham, k_point)
            pool.close()
            pool.join()

            nk = k_point.shape[0]
            if eig:
                pool = Pool()
                results = pool.map(np.linalg.eigh, useham)
                pool.close()
                pool.join()

                evals = np.zeros((nk, self._nsta), dtype=float)
                evec = np.zeros((nk, self._nsta, self._nsta), dtype=complex)
                for i in range(nk):
                    evals[i] = results[i][0]
                    evec[i] = results[i][1]
                evec = evec.transpose((0, 2, 1))
                return (evals, evec)
            else:
                pool = Pool()
                evals = pool.map(np.linalg.eigvalsh, useham)
                pool.close()
                pool.join()
                evals = np.array(evals, dtype=float)
                return evals
        else:
            useham = self.gen_ham()
            if eig:
                (evals, evec) = np.linalg.eigh(useham)
                evec = evec.transpose((0, 2, 1))
                return (evals, evec)
            else:
                evals = np.linalg.eigvalsh(useham)
            return evals

    def remove_dim(self, remove_k: int, value_k: float = 0) -> None:
        """
        Reduce dimensionality by removing one periodic direction.

        Args:
            remove_k: Index of direction to remove.
            value_k: Fixed value for the removed direction.

        Raises:
            Exception: If already 0D or wrong dimension specified.
        """
        if self._dim_k == 0:
            raise Exception("\n\n Can not reduce dimensionality even further!")
        self._per.remove(remove_k)
        dim_k = len(self._per)
        if dim_k != self._dim_k - 1:
            raise Exception("\n\n Specified wrong dimension to reduce!")
        self._dim_k = dim_k

        rv = self._orb[:, remove_k]
        if value_k != 0:
            U = np.diag(np.exp(2.0j * np.pi * rv * value_k))
            if self._nspin == 2:
                U = np.kron([[1, 0], [0, 1]], U)
            for i in range(self._ham.shape[0]):
                self._ham[i] = np.dot(self._ham[i], U)
                self._ham[i] = np.dot(U.T.conjugate(), self._ham[i])
                self._hamR[i, remove_k] = 0

    def shift_to_home(self) -> None:
        """
        Shift orbitals and Hamiltonian to home cell (fractional coordinates in [0,1)).
        """
        new_ham = np.copy(self._ham)
        new_hamR = np.copy(self._hamR)
        self._atom_position = shift_to_zero(self._atom_position) % 1.0

        for i in range(self._norb):
            cur_orb = self._orb[i]
            round_orb = shift_to_zero(np.array(cur_orb)) % 1.0
            dis_vec = np.array(np.round(cur_orb - round_orb), dtype=int)

            if np.any(dis_vec != 0):
                self._orb[i] -= np.array(dis_vec, dtype=float)

                for i0 in self._hamR - dis_vec:
                    if np.any(np.all(self._hamR == i0, axis=1)):
                        index_i = np.argwhere(np.all(self._hamR == i0, axis=1))
                        if np.any(np.all(new_hamR == i0, axis=1)):
                            index = np.all(new_hamR == i0, axis=1)
                            new_ham[index, i, :] = self._ham[index_i, i, :]
                            if self._nspin == 2:
                                new_ham[index, i + self._norb, :] = self._ham[
                                    index_i, i + self._norb, :
                                ]
                        elif np.any(np.all(new_hamR == -i0, axis=1)):
                            index = np.all(new_hamR == -i0, axis=1)
                            new_ham[index, :, i] = self._ham[
                                index_i, i, :
                            ].T.conjugate()
                            if self._nspin == 2:
                                new_ham[index, i + self._norb, :] = self._ham[
                                    index_i, :, i + self._norb
                                ].T.conjugate()
                        else:
                            new_hamR = np.append(new_hamR, [i0], axis=0)
                            ham0 = np.zeros(
                                (self._nsta, self._nsta), dtype=complex
                            )
                            ham0[i, :] = self._ham[index_i, i, :]
                            if self._nspin == 2:
                                ham0[i + self._norb, :] = self._ham[
                                    index_i, i + self._norb, :
                                ]
                            new_ham = np.append(new_ham, [ham0], axis=0)

                    elif np.any(np.all(self._hamR == -i0, axis=1)):
                        index_i = np.argwhere(np.all(self._hamR == -i0, axis=1))
                        if np.any(np.all(new_hamR == i0, axis=1)):
                            index = np.all(new_hamR == i0, axis=1)
                            new_ham[index, i, :] = self._ham[
                                index_i, :, i
                            ].T.conjugate()
                            if self._nspin == 2:
                                new_ham[index, i + self._norb, :] = self._ham[
                                    index_i, :, i + self._norb
                                ].T.conjugate
                        elif np.any(np.all(new_hamR == -i0, axis=1)):
                            index = np.all(new_hamR == -i0, axis=1)
                            new_ham[index, :, i] = self._ham[index_i, :, i]
                            if self._nspin == 2:
                                new_ham[index, :, i + self._norb] = self._ham[
                                    index_i, :, i + self._norb
                                ]
                        else:
                            new_hamR = np.append(new_hamR, [-i0], axis=0)
                            ham0 = np.zeros(
                                (self._nsta, self._nsta), dtype=complex
                            )
                            ham0[i, :] = self._ham[index_i, :, i].T.conjugate()
                            if self._nspin == 2:
                                ham0[i + self._norb, :] = self._ham[
                                    index_i, :, i + self._norb
                                ].conjugate().T
                            new_ham = np.append(new_ham, [ham0], axis=0)

                for j0 in self._hamR + dis_vec:
                    if np.any(np.all(self._hamR == j0, axis=1)):
                        index_j = np.argwhere(np.all(self._hamR == j0, axis=1))
                        if np.any(np.all(new_hamR == j0, axis=1)):
                            index = np.all(new_hamR == j0, axis=1)
                            new_ham[index, :, i] = self._ham[index_j, :, i]
                            if self._nspin == 2:
                                new_ham[index, :, i + self._norb] = self._ham[
                                    index_j, :, i + self._norb
                                ]
                        elif np.any(np.all(new_hamR == -j0, axis=1)):
                            index = np.all(new_hamR == -j0, axis=1)
                            new_ham[index, i, :] = self._ham[
                                index_j, :, i
                            ].conjugate().T
                            if self._nspin == 2:
                                new_ham[index, i + self._norb, :] = self._ham[
                                    index_j, :, i + self._norb
                                ].conjugate().T
                        else:
                            new_hamR = np.append(new_hamR, [j0], axis=0)
                            ham0 = np.zeros(
                                (self._nsta, self._nsta), dtype=complex
                            )
                            ham0[i, :] = self._ham[index_j, :, i]
                            if self._nspin == 2:
                                ham0[i + self._norb, :] = self._ham[
                                    index_j, :, i + self._norb
                                ]
                            new_ham = np.append(new_ham, [ham0], axis=0)

                    elif np.any(np.all(self._hamR == -j0, axis=1)):
                        index_j = np.argwhere(np.all(self._hamR == -j0, axis=1))
                        if np.any(np.all(new_hamR == j0, axis=1)):
                            index = np.all(new_hamR == j0, axis=1)
                            new_ham[index, :, i] = self._ham[
                                index_j, i, :
                            ].conjugate().T
                            if self._nspin == 2:
                                new_ham[index, :, i + self._norb] = self._ham[
                                    index_j, i + self._norb, :
                                ].conjugate().T
                        elif np.any(np.all(new_hamR == -j0, axis=1)):
                            index = np.all(new_hamR == -j0, axis=1)
                            new_ham[index, i, :] = self._ham[index_j, :, i]
                            if self._nspin == 2:
                                new_ham[index, i + self._norb, :] = self._ham[
                                    index_j, :, i + self._norb
                                ]
                        else:
                            new_hamR = np.append(new_hamR, [-j0], axis=0)
                            ham0 = np.zeros(
                                (self._nsta, self._nsta), dtype=complex
                            )
                            ham0[i, :] = self._ham[index_j, :, i]
                            if self._nspin == 2:
                                ham0[i + self._norb, :] = self._ham[
                                    index_j, i + self._norb, :
                                ].conjugate().T
                            new_ham = np.append(new_ham, [ham0], axis=0)

        self._ham = new_ham

    def output(self, path: str = ".", prefix: str = "wannier90") -> None:
        """
        Output model to Wannier90 format files.

        Args:
            path: Output directory.
            prefix: File prefix.
        """
        self.check_if_modified()
        if self._if_modified:
            R0 = self._hamR
            ham = self._ham
        else:
            R0 = np.append(self._hamR, -self._hamR[1:], axis=0)
            ham = np.append(
                self._ham, self._ham[1:].transpose(0, 2, 1).conjugate(), axis=0
            )

        n_R = len(R0)
        if self._dim_r == 2:
            R = np.append(R0, np.array([np.zeros(n_R, dtype=int)]).T, axis=1)
        elif self._dim_r == 1:
            R = np.append(R0, np.zeros((n_R, 2), dtype=int), axis=1)
        else:
            R = R0

        # Sort R-vectors
        arg = np.argsort(np.dot(R, [100, 10, 1]), axis=0)
        R = R[arg]
        ham = ham[arg]

        # Write _hr.dat file
        n_line = int(n_R / 15)
        n0 = int(n_R % 15)
        f = open(path + "/" + prefix + "_hr.dat", "w")
        f.write("writen by MoireStudio\n")
        f.write("         " + str(int(self._nsta)) + "\n")
        f.write("         " + str(int(n_R)) + "\n")

        for i in range(n_line):
            f.write(
                "    1    1    1    1    1    1    1    1    1    1    1    1    1    1    1\n"
            )
        for i in range(n0):
            f.write("    1")
        f.write("\n")

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
                    if "-" in "%.6f" % ham[i, j, k].real:
                        f.write("   %.6f" % ham[i, j, k].real)
                    else:
                        f.write("    %.6f" % ham[i, j, k].real)
                    if "-" in "%.6f" % ham[i, j, k].imag:
                        f.write("   %.6f\n" % ham[i, j, k].imag)
                    else:
                        f.write("    %.6f\n" % ham[i, j, k].imag)

        f.close()

        # Write _centres.xyz file
        n0 = int(self._norb + self._natom)
        f = open(path + "/" + prefix + "_centres.xyz", "w")
        f.write("    " + str(n0) + " \n")
        f.write("writen by MoireStudio\n")

        if self._dim_r != 3:
            orb = np.append(
                self._orb, np.zeros((self._norb, 3 - self._dim_r)), axis=1
            )
            atom_position = np.append(
                self._atom_position,
                np.zeros((self._natom, 3 - self._dim_r)),
                axis=1,
            )
        else:
            orb = self._orb
            atom_position = self._atom_position

        orb = np.dot(orb, self._lat)
        atom_position = np.dot(atom_position, self._lat)

        for i in range(self._norb):
            f.write("X")
            for j in range(3):
                f.write("         ")
                if "-" in "%.6f" % orb[i, j]:
                    f.write("%.6f" % orb[i, j])
                else:
                    f.write(" %.6f" % orb[i, j])
            f.write("\n")

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
        f.close()

        # Write .win file
        f = open(path + "/" + prefix + ".win", "w")
        f.write("begin unit_cell_cart\n")

        for i in range(3):
            for j in range(3):
                f.write("%.6f    " % self._lat[i, j])
            f.write("\n")
        f.write("end unit_cell_cart\n")

        f.write("begin atoms_cart\n")
        for i in range(self._natom):
            atom0 = np.dot(self._atom_position, self._lat)[i]
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
        f.close()

    def k_path_unfold(self, U: np.ndarray, kvec: np.ndarray) -> np.ndarray:
        """
        Fold k-path from primitive cell to supercell reciprocal space.

        Args:
            U: Transformation matrix from primitive to supercell.
            kvec: k-points in primitive cell fractional coordinates.

        Returns:
            k-points in supercell fractional coordinates.
        """
        inv_U = np.linalg.inv(U)
        lat = self._lat
        u_lat = np.dot(inv_U, lat)  # unfold unit cell latters

        if self._dim_r == 3:
            V = np.linalg.det(lat)  # supercell volume
            u_V = np.linalg.det(u_lat)  # primitive cell volume
            # supercell reciprocal vectors
            K = (
                np.array(
                    [
                        np.cross(lat[1], lat[2]),
                        np.cross(lat[2], lat[0]),
                        np.cross(lat[0], lat[1]),
                    ]
                )
                / V
                * (np.pi * 2)
            )
            # primitive cell reciprocal vectors
            u_K = (
                np.array(
                    [
                        np.cross(u_lat[1], u_lat[2]),
                        np.cross(u_lat[2], u_lat[0]),
                        np.cross(u_lat[0], u_lat[1]),
                    ]
                )
                / u_V
                * (np.pi * 2)
            )
        elif self._dim_r == 2:
            V = np.linalg.det(lat)
            u_V = np.linalg.det(u_lat)
            # supercell reciprocal vectors in 2D
            K = (
                np.array([[lat[1, 1], -lat[1, 0]], [-lat[0, 1], lat[0, 0]]])
                / V
                * np.pi
                * 2
            )
            # primitive cell reciprocal vectors in 2D
            u_K = (
                np.array(
                    [
                        [u_lat[1, 1], -u_lat[1, 0]],
                        [-u_lat[0, 1], u_lat[0, 0]],
                    ]
                )
                / u_V
                * np.pi
                * 2
            )

        # Transform k-points
        kvec0 = np.dot(kvec, u_K)  # fractional × primitive recip = cartesian
        kvec0 = np.dot(kvec0, np.linalg.inv(K))  # cartesian ÷ supercell recip = fractional
        kvec0 -= np.floor(kvec0)  # move to [0,1] interval
        # kvec0 -= 0.5  # move to [-0.5,0.5] interval
        return kvec0

    def gen_orb_math(
        self, U: np.ndarray, judge: float
    ) -> Tuple[np.ndarray, int]:
        """
        Generate mapping between supercell and primitive cell orbitals.

        Args:
            U: Transformation matrix from primitive to supercell.
            judge: Tolerance for position comparison.

        Returns:
            Tuple containing:
                orb_arg: Mapping from supercell to primitive orbital indices.
                norb_unfold: Number of orbitals in primitive cell.
        """
        inv_U = np.linalg.inv(U)
        U_det = int(np.linalg.det(U))
        lat = np.dot(inv_U, self._lat)  # primitive cell lattice vectors
        orb = shift_to_zero(np.dot(self._orb, U)[:, self._per])  # primitive cell orbital positions
        orb0 = shift_to_zero(orb % 1)  # normalize to [0,1)
        orb_R = np.floor(orb)  # which primitive cell each orbital belongs to

        orb_arg = np.arange(self._norb, dtype=int)  # mapping from supercell to primitive orbitals
        atom_arg = np.arange(self._natom, dtype=int)

        # Process atom positions
        super_atom_position = np.copy(self._atom_position)  # supercell atom positions
        atom_position = shift_to_zero(np.dot(super_atom_position, U)) % 1  # primitive cell atom positions

        # Remove duplicate atoms in primitive cell
        index = np.ones(self._natom, dtype=bool)
        for i in range(self._natom - 1):
            if index[i]:
                for j in range(i + 1, self._natom):
                    if (
                        np.linalg.norm(atom_position[i] - atom_position[j]) < judge
                        and index[j]
                    ):
                        index[j] = False

        unit_atom_position = atom_position[index]  # unique primitive cell atoms
        unit_atom = self._atom[index]  # orbitals per unique atom
        unit_natom = len(unit_atom)

        # Create atom mapping
        for i in range(unit_natom):
            for j in range(self._natom):
                if np.linalg.norm(unit_atom_position[i] - atom_position[j]) < judge:
                    atom_arg[j] = i

        # Calculate orbital indices for atoms
        unit_orb_list = np.zeros(unit_natom, dtype=int)  # first orbital index for each primitive atom
        super_orb_list = np.zeros(self._natom, dtype=int)  # first orbital index for each supercell atom

        a = 0
        for i in range(unit_natom):
            unit_orb_list[i] = a
            for j in range(unit_atom[i]):
                a += 1

        a = 0
        for i in range(self._natom):
            super_orb_list[i] = a
            for j in range(self._atom[i]):
                a += 1

        # Create orbital mapping
        for i in range(self._natom):
            for j in range(self._atom[i]):
                orb_arg[super_orb_list[i] + j] = unit_orb_list[atom_arg[i]] + j

        norb_unfold = len(orb_arg)
        return (orb_arg, norb_unfold)

    def shift_to_atom(self) -> None:
        """Shift orbital positions to their corresponding atom positions."""
        orb = 0
        for i in range(self._natom):
            for j in range(self._atom[i]):
                self._orb[orb] = self._atom_position[i]
                orb += 1

    def check_if_modified(self) -> None:
        """
        Check if Hamiltonian has been modified (has both R and -R terms).

        Raises:
            Exception: If Hamiltonian has duplicate R-vectors or missing pairs.
        """
        _, counts = np.unique(self._hamR, axis=0, return_counts=True)
        if np.any(counts > 1):
            raise Exception("Error, modified ham twice")

        new_hamR = []
        for i in range(len(self._hamR)):
            if np.any(self._hamR[i]):
                new_hamR.append(self._hamR[i])
        new_hamR = np.array(new_hamR)
        neg_new_hamR = -new_hamR

        def to_row_view(arr):
            return np.ascontiguousarray(arr).view(
                np.dtype((np.void, arr.dtype.itemsize * arr.shape[1]))
            )

        use_list = np.in1d(to_row_view(new_hamR), to_row_view(neg_new_hamR))
        if np.any(use_list) != np.all(use_list):
            raise Exception("ham error")
        else:
            self._if_modified = np.all(use_list)

    def modify_ham(self) -> None:
        """
        Modify Hamiltonian to include both R and -R terms.
        """
        self.check_if_modified()
        if not self._if_modified:
            self._hamR = np.append(
                np.array(self._hamR), np.array(-self._hamR[1:]), axis=0
            )[:, self._per]
            self._ham = np.append(
                self._ham,
                self._ham[1:].transpose((0, 2, 1)).conjugate(),
                axis=0,
            )

    def layer_index_arrange(self) -> None:
        """
        Arrange atoms and orbitals by layer (top/bottom).
        """
        mid_pos = (np.max(self._orb[:, 2]) + np.min(self._orb[:, 2])) / 2
        self._atom_pos_layer_index = np.zeros((len(self._atom_position),), dtype=int)
        self._orb_layer_index = np.zeros((len(self._orb),), dtype=int)

        up_atom_pos = []
        dw_atom_pos = []
        up_orb = []
        dw_orb = []

        # Classify atoms by layer
        for i in range(len(self._atom_position)):
            if self._atom_position[i, 2] > mid_pos:
                self._atom_pos_layer_index[i] = 1
                up_atom_pos.append(self._atom_position[i])
            else:
                self._atom_pos_layer_index[i] = -1
                dw_atom_pos.append(self._atom_position[i])

        # Classify orbitals and create new ordering
        new_orb_index = []
        for i in range(len(self._orb)):
            if self._orb[i, 2] > mid_pos:
                self._orb_layer_index[i] = 1
                up_orb.append(self._orb[i])
                new_orb_index.append(len(up_orb) - 1)
            else:
                self._orb_layer_index[i] = -1
                dw_orb.append(self._orb[i])
                new_orb_index.append(len(dw_orb) + len(self._orb) // 2 - 1)

        # Combine layers
        up_atom_pos = np.array(up_atom_pos)
        dw_atom_pos = np.array(dw_atom_pos)
        up_orb = np.array(up_orb)
        dw_orb = np.array(dw_orb)
        atom_pos_use = np.concatenate((up_atom_pos, dw_atom_pos), axis=0)
        orb_use = np.concatenate((up_orb, dw_orb), axis=0)
        new_orb_index = np.array(new_orb_index)

        # Reorder Hamiltonian
        new_ham = np.zeros(
            (self._ham.shape[0], self._ham.shape[1], self._ham.shape[2]),
            dtype=complex,
        )
        for k_R in range(len(self._hamR)):
            for i in range(len(self._orb)):
                for j in range(len(self._orb)):
                    new_ham[k_R, new_orb_index[i], new_orb_index[j]] = self._ham[
                        k_R, i, j
                    ]

        self._ham = new_ham
        self._orb = orb_use
        self._atom_position = atom_pos_use

    def orb_deal_atom(self) -> None:
        """
        Assign orbital positions to their corresponding atom positions.
        """
        cc = 0
        for i in range(len(self._atom_position)):
            for j in range(self._atom_list[i]):
                self._orb[cc] = self._atom_position[i]
                cc = cc + 1

    def solve_dos(
        self,
        mesh_arr: List[int],
        energy_range: Tuple[float, float],
        n_e: int,
        method: str = "Gaussian",
        sigma: float = 0.01,
    ) -> np.ndarray:
        """
        Calculate density of states.

        Args:
            mesh_arr: k-mesh dimensions.
            energy_range: Energy range for DOS calculation.
            n_e: Number of energy points.
            method: Broadening method (only Gaussian implemented).
            sigma: Broadening width.

        Returns:
            Density of states array.
        """
        start_k = np.zeros(self._dim_k, dtype=float)
        k_points = gen_k_mesh(mesh_arr[0])  # gen_mesh_arr(mesh_arr, self._dim_k, start_k)
        evals = self.solve_all(k_points)
        E0 = np.linspace(energy_range[0], energy_range[1], n_e)
        center = evals.ravel()
        dos = np.zeros(n_e, dtype=float)
        dos = Gauss(E0, dos, center, sigma)
        return dos

    def change_range(self, atom_range_list: np.ndarray) -> None:
        """
        Change the ordering of atoms and orbitals.

        Args:
            atom_range_list: New ordering of atoms.
        """
        orb_use = np.copy(self._orb)
        atom_pos_use = np.copy(self._atom_position)
        atom_name_use = np.copy(self._atom_name)

        old_atom_list = np.copy(self._atom_list)
        new_atom_list = np.zeros((len(old_atom_list)), dtype=int)
        for i in range(len(old_atom_list)):
            new_atom_list[atom_range_list[i]] = old_atom_list[i]

        old_atom_sum = np.zeros((len(old_atom_list)), dtype=int)
        new_atom_sum = np.zeros((len(old_atom_list)), dtype=int)
        c_old = 0
        c_new = 0
        for i in range(len(old_atom_list)):
            old_atom_sum[i] = c_old
            new_atom_sum[i] = c_new
            c_old = c_old + old_atom_list[i]
            c_new = c_new + new_atom_list[i]

        def change_ham_range(ham_use):
            """Reorder Hamiltonian matrix according to new atom ordering."""
            ham_new = np.zeros(
                (ham_use.shape[0], ham_use.shape[1], ham_use.shape[2]),
                dtype=complex,
            )
            ham_new_2 = np.zeros(
                (ham_use.shape[0], ham_use.shape[1], ham_use.shape[2]),
                dtype=complex,
            )
            for k in range(ham_use.shape[0]):
                for i_old, i_new in enumerate(atom_range_list):
                    ham_new[
                        k,
                        new_atom_sum[i_new] : new_atom_sum[i_new] + new_atom_list[i_new],
                        :,
                    ] = ham_use[
                        k,
                        old_atom_sum[i_old] : old_atom_sum[i_old] + old_atom_list[i_old],
                        :,
                    ]
                for j_old, j_new in enumerate(atom_range_list):
                    ham_new_2[
                        k,
                        :,
                        new_atom_sum[j_new] : new_atom_sum[j_new] + new_atom_list[j_new],
                    ] = ham_new[
                        k,
                        :,
                        old_atom_sum[j_old] : old_atom_sum[j_old] + old_atom_list[j_old],
                    ]
            return ham_new_2

        if self._nspin == 2:
            ham_out = np.zeros(
                (self._ham.shape[0], self._ham.shape[1], self._ham.shape[2]),
                dtype=complex,
            )
            ham_out[:, : self._norb, : self._norb] = change_ham_range(
                self._ham[:, : self._norb, : self._norb]
            )
            ham_out[:, : self._norb, self._norb :] = change_ham_range(
                self._ham[:, : self._norb, self._norb :]
            )
            ham_out[:, self._norb :, : self._norb] = change_ham_range(
                self._ham[:, self._norb :, : self._norb]
            )
            ham_out[:, self._norb :, self._norb :] = change_ham_range(
                self._ham[:, self._norb :, self._norb :]
            )
        else:
            ham_out = change_ham_range(self._ham)

        # Reorder orbitals and atoms
        orb_new = np.zeros((orb_use.shape[0], orb_use.shape[1]), dtype=float)
        atom_pos_new = np.zeros((atom_pos_use.shape[0], atom_pos_use.shape[1]), dtype=float)
        atom_name_new = np.copy(atom_name_use)

        for i_old, i_new in enumerate(atom_range_list):
            atom_pos_new[i_new] = atom_pos_use[i_old]
            atom_name_new[i_new] = atom_name_use[i_old]
            orb_new[
                new_atom_sum[i_new] : new_atom_sum[i_new] + new_atom_list[i_new], :
            ] = orb_use[
                old_atom_sum[i_old] : old_atom_sum[i_old] + old_atom_list[i_old], :
            ]

        self._ham = ham_out
        self._orb = orb_new
        self._atom_position = atom_pos_new
        self._atom_list = new_atom_list
        self._atom = new_atom_list
        self._atom_name = atom_name_new

    def spin_to_orb(self) -> None:
        """
        Convert spinor basis to orbital basis (expand spin dimension).
        """
        self._nsta = 1
        self._atom_list = self._atom_list * 2
        self._atom = self._atom * 2

        half_orb = np.copy(self._orb)
        self._orb = np.zeros((len(half_orb) * 2, 3), dtype=float)
        num_orb = len(half_orb)
        iii = 0

        # Duplicate orbitals for spin up and down
        for i in range(len(half_orb)):
            self._orb[iii] = half_orb[i]
            iii = iii + 1
            self._orb[iii] = half_orb[i]
            iii = iii + 1

        # Expand Hamiltonian
        for i in range(len(self._hamR)):
            ham_use = np.copy(self._ham[i])
            for j in range(len(half_orb)):
                self._ham[i, 2 * j] = ham_use[j]
                self._ham[i, 2 * j + 1] = ham_use[j + num_orb]

            ham_use = np.copy(self._ham[i])
            for j in range(len(half_orb)):
                self._ham[i, :, 2 * j] = ham_use[:, j]
                self._ham[i, :, 2 * j + 1] = ham_use[:, j + num_orb]


def shift_to_zero(a: np.ndarray) -> np.ndarray:
    """
    Shift fractional coordinates to zero by rounding near integers.

    Args:
        a: Array of fractional coordinates.

    Returns:
        Shifted coordinates.
    """
    a = np.array(a)
    if np.any(np.abs(a - np.floor(a)) < 1e-5):
        index = np.abs(a - np.floor(a)) < 1e-5
        a[index] = np.round(a[index])
    if np.any(np.abs(a - np.ceil(a)) < 1e-5):
        index = np.abs(a - np.ceil(a)) < 1e-5
        a[index] = np.round(a[index])
    return a


def gen_k_mesh(n: int, if_edge: bool = False) -> np.ndarray:
    """
    Generate a uniform k-mesh in 2D.

    Args:
        n: Number of k-points along each direction.
        if_edge: Whether to include edge points.

    Returns:
        k-mesh array of shape (n*n, 3).
    """
    k_mesh = np.zeros((n * n, 3), dtype=float)
    iii = 0
    use_list = np.linspace(0, 1, n + (not if_edge))
    for i in range(n):
        for j in range(n):
            k_mesh[iii, 0] = use_list[i]
            k_mesh[iii, 1] = use_list[j]
            iii = iii + 1
    return k_mesh


def Gauss(x: np.ndarray, y: np.ndarray, center: np.ndarray, sigma: float) -> np.ndarray:
    """
    Apply Gaussian broadening to a set of delta functions.

    Args:
        x: Energy grid points.
        y: Output array (will be modified).
        center: Centers of delta functions.
        sigma: Gaussian width.

    Returns:
        Broadened function.
    """
    for i in range(center.shape[0]):
        y += (
            1
            / np.sqrt(2 * np.pi)
            / sigma
            * np.exp(-((x - center[i]) ** 2) / (2 * sigma**2))
        )
    y *= 1 / center.shape[0]
    return y