"""
Module for reading tight-binding model data from various file formats.

This module provides functions to read tight-binding parameters from:
1. Wannier90 output files (*_hr.dat, *.win, *_centres.xyz)
2. VASP POSCAR files
3. Custom formats for bilayer structures
"""

import re
import os
from typing import Tuple, Optional, List, Dict, Any
import numpy as np

from .tb_model import tb_model


def read_mono(file_position: str, file_name: str, fermi_energy: float) -> tb_model:
    """
    Read a monolayer tight-binding model from Wannier90 files.

    Args:
        file_position: Directory path containing the Wannier90 files.
        file_name: Base name of the Wannier90 files (without extension).
        fermi_energy: Fermi energy to use as the zero-energy reference.

    Returns:
        Tight-binding model object for the monolayer.
    """
    silicon = w90(file_position, file_name)
    mono_zero_energy = fermi_energy
    mono_model = silicon.model(zero_energy=mono_zero_energy)
    mono_model.modify_ham()
    mono_model.orb_deal_atom()
    return mono_model


def read_fermi_energy(file_route: str) -> float:
    """
    Read Fermi energy from a file.

    Args:
        file_route: Path to the file containing Fermi energy.

    Returns:
        Fermi energy value.
    """
    fermi_data = np.loadtxt(file_route, comments="#")
    fermi_data = np.array([fermi_data])
    return fermi_data[0]


def read_POSCAR(
    file_position: str, file_name: str, ifmodel: bool = False
) -> Tuple[tb_model, Tuple[np.ndarray, np.ndarray, List[str]]]:
    """
    Read structure information from a POSCAR file.

    Args:
        file_position: Directory path containing the POSCAR file.
        file_name: Name of the POSCAR file.
        ifmodel: If True, return a tb_model object; otherwise return raw data.

    Returns:
        If ifmodel is True: tb_model object.
        Otherwise: Tuple of (lattice vectors, atomic positions, atomic names).
    """
    file_route = file_position + "/" + file_name
    lat = np.zeros((3, 3), dtype=float)
    with open(file_route, "r") as file_data:
        for i, line in enumerate(file_data):
            if i < 2:
                continue
            elif (i >= 2) and (i <= 4):
                values = line.split()
                lat[i - 2] = np.array(
                    [float(values[0]), float(values[1]), float(values[2])]
                )
            elif i == 5:
                values = line.split()
                atom_kind = []
                for kind_i in range(len(values)):
                    atom_kind.append(values[kind_i])
            elif i == 6:
                values = line.split()
                atom_number = np.sum(np.array(values, dtype=int))
                atom_number_per_kind = np.array(values, int)
                atom_position = np.zeros((atom_number, 3), dtype=float)
            elif i == 7:
                if line == "Cartesian\n":
                    car = 1
                else:
                    car = 0
            else:
                values = line.split()
                if values == []:
                    continue
                atom_position[i - 8] = np.array(
                    [float(values[0]), float(values[1]), float(values[2])]
                )
    if car:
        atom_position = np.dot(atom_position, np.linalg.inv(lat))
    atom_name = []
    for i in range(len(atom_number_per_kind)):
        for j in range(atom_number_per_kind[i]):
            atom_name.append(atom_kind[i])
    if ifmodel:
        atom_list = np.zeros((len(atom_position),), dtype=int) + 1
        use_model = tb_model(
            3,
            3,
            lat=lat,
            orb=atom_position,
            atom_list=atom_list,
            atom_position=atom_position,
            atom_name=atom_name,
        )
        return use_model
    else:
        return lat, atom_position, atom_name


class w90:
    """
    Class for reading and processing Wannier90 tight-binding models.

    This class reads Wannier90 output files (*_hr.dat, *.win, *_centres.xyz)
    and constructs a tight-binding model.
    """

    def __init__(self, path: str, prefix: str, mode: int = 0) -> None:
        """
        Initialize the Wannier90 reader.

        Args:
            path: Directory containing Wannier90 files.
            prefix: Base name of Wannier90 files.
            mode: Processing mode (0 for normal, 1 for spinor reordering).
        """
        self._path = path
        self._prefix = prefix
        f = open(self._path + "/" + self._prefix + ".win", "r")
        self._win = f.read()
        f.close()
        lat = re.findall(
            "begin unit_cell_cart[\-\. 0-9\n]*end unit_cell_cart", self._win
        )
        lat = re.findall("[\-\. 0-9]*[0-9]", lat[0])
        spin = re.findall("spinors[\ ]*=[a-z A-Z\.]*", self._win)
        atom = re.findall(
            "begin atoms_cart[A-Za-z\-\. 0-9\n]*end atoms_cart", self._win
        )
        atom = re.findall("[A-Z][a-z]*", atom[0])
        atom_pos = re.findall(
            "begin atoms_cart[A-Za-z\-\. 0-9\n]*end atoms_cart", self._win
        )
        atom_pos = re.findall("[\-\. 0-9]*[0-9]", atom_pos[0])
        # self._atom_name = np.copy(atom)
        proj = re.findall(
            "begin projections[A-Za-z0-9;:, \n]*end projections", self._win
        )
        proj_content = proj[0].replace(" ", "")
        proj = re.findall("[A-Z][a-z]*:[a-z0-9,;]*", proj_content)
        self._atom = []
        proj_name = []
        proj_num = []
        proj_orb_name = []
        for i in range(len(proj)):
            proj_name.append(re.findall("[A-Z][a-z]*", proj[i])[0])
            projection = re.findall(":[a-z0-9,;]*", proj[i])
            projection = re.findall("[a-z0-9][a-z0-9]*", projection[0])
            proj_num.append(0)
            one_orb_name = []
            for j in range(len(projection)):
                one_orb_name.append(projection[j])
                if "s" == projection[j]:
                    proj_num[i] += 1
                elif "px" == projection[j]:
                    proj_num[i] += 1
                elif "py" == projection[j]:
                    proj_num[i] += 1
                elif "pz" == projection[j]:
                    proj_num[i] += 1
                elif "p" == projection[j]:
                    proj_num[i] += 3
                elif "sp2" == projection[j]:
                    proj_num[i] += 3
                elif "sp3" == projection[j]:
                    proj_num[i] += 4
                elif "d" == projection[j]:
                    proj_num[i] += 5
                elif "f" == projection[j]:
                    proj_num[i] += 5
                elif "dz2" == projection[j]:
                    proj_num[i] += 1
                elif "dxy" == projection[j]:
                    proj_num[i] += 1
                elif "dx2y2" == projection[j]:
                    proj_num[i] += 1
                elif "dyz" == projection[j]:
                    proj_num[i] += 1
                else:
                    raise Exception(
                        "cant recognize the projections, the procedure only can recognize s,px,py,pz,p,d,f,sp2,sp3"
                    )
            proj_orb_name.append(one_orb_name)
        for a, i in enumerate(proj_name):
            for j in atom:
                if j == i:
                    self._atom.append(proj_num[a])
        self._orb_name = dict(zip(proj_name, proj_orb_name))
        self._atom = np.array(self._atom, dtype=int)
        self._natom = int(len(self._atom))
        if len(spin) == 0:
            self._nspin = 1
        else:
            if re.findall("[tT]", spin[0]) is not None:
                self._nspin = 2
            else:
                self._nspin = 1
        self._lat = []
        for i in lat:
            lats = re.findall("[\-\.0-9]*[0-9]", i)
            latss = []
            for j in lats:
                latss.append(float(j))
            self._lat.append(latss)
        self._lat = np.array(self._lat, dtype=float)

        f = open(self._path + "/" + prefix + "_hr.dat")
        f.readline()
        n_orb = int(f.readline())
        self._norb = int(n_orb / self._nspin)
        self._nsta = n_orb
        n_R = int(f.readline())
        n_cal = 0
        weight = []
        n_raw = 3
        while n_cal < n_R:
            weight = np.append(
                weight, np.array(re.findall("[0-9]", f.readline()), dtype=int)
            )
            n_cal = len(weight)
            n_raw += 1
        n_line = n_R * n_orb**2
        tmp_data = np.zeros((n_line, 2), dtype=float)
        ind_R_data = np.zeros((n_line, 3), dtype=int)
        ind_ij = np.zeros((n_line, 2), dtype=int)
        gen_data = np.loadtxt(
            self._path + "/" + prefix + "_hr.dat", dtype=float, skiprows=n_raw
        )
        tmp = gen_data[:, 5] + 1.0j * gen_data[:, 6]
        ind_R_data = np.array(gen_data[:, :3], dtype=int)
        ind_ij = np.array(gen_data[:, 3:5], dtype=int)
        del gen_data
        ham = np.zeros((n_R, n_orb, n_orb), dtype=complex)
        R_ham = np.zeros((n_R, 3), dtype=int)
        R_ham = ind_R_data[:: n_orb**2]
        ham = gen_w90_ham(n_R, n_orb, tmp, weight, ham)
        new_ham = np.copy(ham)
        if mode == 1:
            new_ham[:, : self._norb, : self._norb] = ham[:, ::2, ::2]
            new_ham[:, self._norb :, self._norb :] = ham[:, 1::2, 1::2]
            new_ham[:, : self._norb, self._norb :] = ham[:, ::2, 1::2]
            new_ham[:, self._norb :, : self._norb] = ham[:, 1::2, ::2]
        ham = new_ham
        self._ham = ham
        self._hamR = R_ham

        file_xyz = self._path + "/" + prefix + "_centres.xyz"
        if os.path.isfile(file_xyz):
            f = open(self._path + "/" + prefix + "_centres.xyz", "r")
            f.readline()
            f.readline()
            self._orb = []
            self._atom_position = np.zeros((self._natom, 3), dtype=float)
            self._atom_name = []

            for i in range(self._norb):
                lat = np.array(
                    re.findall("[\-\.0-9]*[0-9]", f.readline()), dtype=float
                )
                self._orb.append(lat)
            if self._nspin == 2:
                for i in range(self._norb):
                    f.readline()
            for i in range(self._natom):
                aa = f.readline()
                # print(aa)
                lat = np.array(re.findall("[\-\.0-9]*[0-9]", aa), dtype=float)
                self._atom_position[i] = lat
                self._atom_name.append(re.findall("[A-Z][a-z]*", aa)[0])
        else:
            self._atom_position = []
            for i in atom_pos:
                aps = re.findall("[\-\.0-9]*[0-9]", i)
                apss = []
                for j in aps:
                    apss.append(float(j))
                self._atom_position.append(apss)
            self._atom_position = np.array(self._atom_position, dtype=float)

            orb_num = np.sum(self._atom)
            orb = np.zeros((orb_num, 3), dtype=float)
            iii = 0
            for i in range(len(self._atom)):
                for j in range(self._atom[i]):
                    orb[iii] = self._atom_position[i]
                    iii = iii + 1
            self._orb = orb

        self._atom_name = np.array(self._atom_name)
        self._atom_position = shift_to_zero(
            np.dot(self._atom_position, np.linalg.inv(self._lat))
        )
        self._orb = np.array(self._orb)
        self._orb = shift_to_zero(np.dot(self._orb, np.linalg.inv(self._lat)))
        self._ef = 0.0
        self._per = [0, 1, 2]
        self._dim_r = 3
        self._dim_k = 3
        self._natom = len(self._atom)

        # Sometimes the orbital positions from wannier_centres do not match
        # the atomic positions. For convenience, we adjust the atomic positions.
        # index = np.arange(self._natom)
        # for i, atom in enumerate(self._atom_position):
        #     index[i] = np.argmin(np.linalg.norm(atom - self._orb, axis=1))
        # index = np.argsort(index)
        # self._atom_position = self._atom_position[index]
        # self._atom = self._atom[index]

    def model(self, zero_energy: float = 0.0, min_hop: float = 0.0) -> tb_model:
        """
        Create a tight-binding model from the Wannier90 data.

        Args:
            zero_energy: Energy to set as zero reference.
            min_hop: Minimum hopping to include (not currently used).

        Returns:
            Tight-binding model object.
        """
        self._ef = zero_energy
        tb = tb_model(
            3,
            3,
            self._lat,
            self._orb,
            nspin=self._nspin,
            atom_list=self._atom,
            atom_position=self._atom_position,
            atom_name=self._atom_name,
            orb_name=self._orb_name,
        )
        if np.any(self._hamR[0] != 0):
            index = np.argwhere(np.all(self._hamR == 0, axis=1))[0, 0]
            ins = np.copy(self._ham[index])
            ind = np.copy(self._hamR[0])
            self._ham[index] = np.copy(self._ham[0])
            self._hamR[index] = ind
            self._ham[0] = ins
            self._hamR[0] *= 0
        diag = np.identity(tb._nsta, dtype=complex) * zero_energy
        tb_hamR = self._hamR
        tb_ham = self._ham
        # index=(tb_hamR[:,2]>0)+(tb_hamR[:,2]==0)*(tb_hamR[:,1]>0)+(tb_hamR[:,2]==0)*(tb_hamR[:,1]==0)*(tb_hamR[:,0]>=0)
        index = (tb_hamR[:, 2] > 0) + (tb_hamR[:, 2] == 0) * (
            (tb_hamR[:, 1] > 0)
            + (tb_hamR[:, 1] == 0) * (tb_hamR[:, 0] >= 0)
        )
        tb._ham = self._ham[index]
        tb._hamR = self._hamR[index]
        tb._ham[0] -= diag
        self._ham[0] -= diag
        return tb

    def read_band(
        self,
    ) -> Tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Read band structure data from Wannier90 band files.

        Returns:
            Tuple containing:
                n_k: Number of k-points.
                band: Band energies (n_k × n_bands).
                k_vec: k-point vectors.
                k_dis: k-point distances along the path.
                k_node: High-symmetry point positions.
        """
        f = open(self._path + "/" + self._prefix + "_band.kpt")
        n_k = int(f.readline())
        f.close()
        band_data = np.loadtxt(self._path + "/" + self._prefix + "_band.dat")
        k_vec = np.loadtxt(
            self._path + "/" + self._prefix + "_band.kpt",
            skiprows=1,
            usecols=[0, 1, 2],
        )
        n_line = len(band_data)
        nn = int(n_line / n_k)
        band = np.zeros((n_k, nn), dtype=float)
        k_dis = band_data[:n_k, 0]
        k_node = np.loadtxt(
            self._path + "/" + self._prefix + "_band.labelinfo.dat",
            usecols=[2],
        )
        for n in range(nn):
            band[:, n] = band_data[n * n_k : (n + 1) * n_k, 1] - self._ef
        return (n_k, band, k_vec, k_dis, k_node)

    def gen_ham(
        self, k_point: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Generate Hamiltonian matrix at given k-point(s).

        Args:
            k_point: k-point(s) at which to compute the Hamiltonian.
                    If None, returns the on-site Hamiltonian.

        Returns:
            Hamiltonian matrix (or list of matrices for multiple k-points).

        Raises:
            Exception: If k_point dimension doesn't match model dimension.
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
        ind_R = self._hamR[:, self._per]
        useham = self._ham
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
        return ham

    def remove_dim(self, remove_k: int, value_k: float = 0) -> None:
        """
        Reduce the dimensionality of the model by removing one k-direction.

        Args:
            remove_k: Index of the dimension to remove (0, 1, or 2).
            value_k: Fixed value for the removed dimension.

        Raises:
            Exception: If the model is already 0D or wrong dimension specified.
        """
        if self._dim_k == 0:
            raise Exception(
                "\n\n Can not reduce dimensionality even further!"
            )
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


def shift_to_zero(a: np.ndarray) -> np.ndarray:
    """
    Shift fractional coordinates to be within [0, 1).

    Args:
        a: Array of fractional coordinates.

    Returns:
        Coordinates shifted to the [0, 1) range.
    """
    a = np.array(a)
    if np.any(np.abs(a - np.floor(a)) < 1e-5):
        index = np.abs(a - np.floor(a)) < 1e-5
        a[index] = np.round(a[index])
    if np.any(np.abs(a - np.ceil(a)) < 1e-5):
        index = np.abs(a - np.ceil(a)) < 1e-5
        a[index] = np.round(a[index])
    return a


def gen_w90_ham(
    n_R: int, n_orb: int, tmp: np.ndarray, weight: np.ndarray, ham: np.ndarray
) -> np.ndarray:
    """
    Reorganize Wannier90 hopping matrices.

    Args:
        n_R: Number of R-vectors.
        n_orb: Number of orbitals.
        tmp: Flattened hopping matrix data.
        weight: Weight factors for each R-vector.
        ham: Pre-allocated Hamiltonian array.

    Returns:
        Reorganized Hamiltonian array.
    """
    for r in range(n_R):
        for i in range(n_orb):
            for j in range(n_orb):
                ham[r, j, i] = tmp[r * n_orb**2 + i * n_orb + j] / weight[r]
    return ham


def devide2mono(
    bilayer_model: tb_model,
) -> Tuple[tb_model, tb_model, np.ndarray, np.ndarray]:
    """
    Split a bilayer tight-binding model into two monolayer models.

    Args:
        bilayer_model: Input bilayer tight-binding model.

    Returns:
        Tuple containing:
            mono_t_model: Top monolayer model.
            mono_b_model: Bottom monolayer model.
            h0: Inter-layer coupling matrix.
            d0: Inter-layer distance matrix.
    """
    mono_atom_num = len(bilayer_model._atom) // 2
    mono_orb_num = len(bilayer_model._orb) // 2
    mono_t_model = tb_model(
        k_dim=3,
        r_dim=3,
        lat=bilayer_model._lat,
        orb=bilayer_model._orb[:mono_orb_num],
        atom_position=bilayer_model._atom_position[:mono_atom_num],
        per=[0, 1, 2],
        atom_list=bilayer_model._atom_list[:mono_atom_num],
        atom_name=bilayer_model._atom_name[:mono_atom_num],
    )
    mono_b_model = tb_model(
        k_dim=3,
        r_dim=3,
        lat=bilayer_model._lat,
        orb=bilayer_model._orb[mono_orb_num:],
        atom_position=bilayer_model._atom_position[mono_atom_num:],
        per=[0, 1, 2],
        atom_list=bilayer_model._atom_list[mono_atom_num:],
        atom_name=bilayer_model._atom_name[mono_atom_num:],
    )

    mono_t_model._nspin = bilayer_model._nspin
    mono_b_model._nspin = bilayer_model._nspin
    mono_t_model._nsta = bilayer_model._nsta // 2
    mono_b_model._nsta = bilayer_model._nsta // 2

    mono_t_model._atom = bilayer_model._atom[:mono_atom_num]
    mono_b_model._atom = bilayer_model._atom[mono_atom_num:]

    n_o_t = mono_t_model._norb
    n_o_b = mono_b_model._norb
    n_s_t = mono_t_model._nsta
    n_s_b = mono_b_model._nsta
    tol_no = n_o_t + n_o_b
    if bilayer_model._nspin == 2:
        ham_t = np.zeros(
            (len(bilayer_model._hamR), n_s_t, n_s_t), dtype=complex
        )
        ham_b = np.zeros(
            (len(bilayer_model._hamR), n_s_b, n_s_b), dtype=complex
        )
        h0 = np.zeros((n_s_t, n_s_b), dtype=complex)

        ham_t[:, :n_o_t, :n_o_t] = bilayer_model._ham[:, :n_o_t, :n_o_t]
        ham_t[:, :n_o_t, n_o_t:] = bilayer_model._ham[
            :, :n_o_t, tol_no : tol_no + n_o_t
        ]
        ham_t[:, n_o_t:, :n_o_t] = bilayer_model._ham[
            :, tol_no : tol_no + n_o_t, :n_o_t
        ]
        ham_t[:, n_o_t:, n_o_t:] = bilayer_model._ham[
            :, tol_no : tol_no + n_o_t, tol_no : tol_no + n_o_t
        ]

        ham_b[:, :n_o_b, :n_o_b] = bilayer_model._ham[
            :, n_o_t:tol_no, n_o_t:tol_no
        ]
        ham_b[:, :n_o_b, n_o_b:] = bilayer_model._ham[
            :, n_o_t:tol_no, tol_no + n_o_t :
        ]
        ham_b[:, n_o_b:, :n_o_b] = bilayer_model._ham[
            :, tol_no + n_o_t :, n_o_t:tol_no
        ]
        ham_b[:, n_o_b:, n_o_b:] = bilayer_model._ham[
            :, tol_no + n_o_t :, tol_no + n_o_t :
        ]

        h0[:n_o_t, :n_o_t] = bilayer_model._ham[0, :n_o_t, n_o_t:tol_no]
        h0[:n_o_t, n_o_t:] = bilayer_model._ham[
            0, :n_o_t, tol_no + n_o_t :
        ]
        h0[n_o_t:, :n_o_t] = bilayer_model._ham[
            0, tol_no : tol_no + n_o_t, n_o_t:tol_no
        ]
        h0[n_o_t:, n_o_t:] = bilayer_model._ham[
            0, tol_no : tol_no + n_o_t, tol_no + n_o_t :
        ]

    else:
        ham_t = bilayer_model._ham[:, :n_o_t, :n_o_t]
        ham_b = bilayer_model._ham[:, n_o_t:, n_o_t:]
        h0 = bilayer_model._ham[0, :n_o_t, n_o_t:]

    mono_t_model._ham = ham_t
    mono_b_model._ham = ham_b
    mono_t_model._hamR = bilayer_model._hamR
    mono_b_model._hamR = bilayer_model._hamR

    mono_t_model._orb_name = bilayer_model._orb_name
    mono_b_model._orb_name = bilayer_model._orb_name

    if bilayer_model._orb[0, 2] > bilayer_model._orb[n_o_t, 2]:
        d0 = (
            np.zeros((n_s_t, n_s_b), dtype=float)
            + (
                np.min(bilayer_model._orb[:n_o_t, 2])
                - np.max(bilayer_model._orb[n_o_t:, 2])
            )
            * bilayer_model._lat[2, 2]
        )
        return mono_t_model, mono_b_model, h0, d0
    else:
        d0 = (
            np.zeros((n_s_t, n_s_b), dtype=float)
            + (
                np.min(bilayer_model._orb[n_o_t:, 2])
                - np.max(bilayer_model._orb[:n_o_t, 2])
            )
            * bilayer_model._lat[2, 2]
        )
        return mono_b_model, mono_t_model, h0, d0


def gen_atom_range_list(
    bilayer_model: tb_model, layer_inerchange: bool = False
) -> np.ndarray:
    """
    Generate an index list mapping atoms to layers.

    Args:
        bilayer_model: Input bilayer model.
        layer_inerchange: If True, invert the layer assignment.

    Returns:
        Array mapping original atom indices to layer-ordered indices.
    """
    atom_pos = bilayer_model._atom_position
    atom_pos_list = atom_pos.tolist()
    centra_z = (np.max(atom_pos[:, 2]) + np.min(atom_pos[:, 2])) / 2
    atom_pos_t = []
    atom_pos_b = []
    for i in range(len(atom_pos)):
        if layer_inerchange:
            if atom_pos[i, 2] < centra_z:
                atom_pos_t.append(atom_pos[i].tolist())
            else:
                atom_pos_b.append(atom_pos[i].tolist())
        else:
            if atom_pos[i, 2] > centra_z:
                atom_pos_t.append(atom_pos[i].tolist())
            else:
                atom_pos_b.append(atom_pos[i].tolist())

    atom_range_list = np.zeros((len(atom_pos),), dtype=int)
    for i in range(len(atom_pos_t)):
        ori_i = atom_pos_list.index(atom_pos_t[i])
        atom_range_list[ori_i] = i
    for i in range(len(atom_pos_b)):
        ori_i = atom_pos_list.index(atom_pos_b[i])
        atom_range_list[ori_i] = i + len(atom_pos_t)
    return atom_range_list