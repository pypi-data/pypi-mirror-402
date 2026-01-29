"""
Twisted bilayer geometry generation and moiré pattern analysis.

This module provides the TwistGeometry class for generating twisted bilayer
structures, calculating moiré patterns, and analyzing commensurate angles.
"""

import numpy as np
import matplotlib.pyplot as plt
from .simple_func import R_theta, reciprocal_base, get_perpendicular_unit_vector, linearly_dependent


class TwistGeometry:
    """
    Geometry generator for twisted bilayer systems.

    This class handles the generation of moiré superlattices, identification
    of commensurate angles, and construction of twisted bilayer atomic positions.

    Attributes
    ----------
    _theta_pi : float
        Twist angle in radians.
    _theta_360 : float
        Twist angle in degrees.
    _mono_lat_t : numpy.ndarray
        2D lattice vectors of top monolayer (2x2 matrix).
    _mono_lat_b : numpy.ndarray
        2D lattice vectors of bottom monolayer (2x2 matrix).
    _mono_atom_pos_t : numpy.ndarray
        Atomic positions of top monolayer in Cartesian coordinates (Nx3).
    _mono_atom_pos_b : numpy.ndarray
        Atomic positions of bottom monolayer in Cartesian coordinates (Mx3).
    _atom_name_t : list
        Element names for top monolayer atoms.
    _atom_name_b : list
        Element names for bottom monolayer atoms.
    _atom_num_per_area_t : float
        Atomic density (atoms per area) of top monolayer.
    _atom_num_per_area_b : float
        Atomic density (atoms per area) of bottom monolayer.
    _d_AA : float
        Interlayer distance at AA stacking regions.
    _d_AB : float
        Interlayer distance at AB stacking regions.
    _Lm : numpy.ndarray
        Moiré superlattice vectors (3x3 matrix including z-direction).
    _moire_points : numpy.ndarray
        Atomic positions in moiré superlattice.
    _atom_index : numpy.ndarray
        Indices mapping moiré atoms to original monolayer atoms.
    _atom_name : list
        Element names for all atoms in moiré superlattice.
    _t_num : int
        Number of atoms in top layer of moiré cell.
    _b_num : int
        Number of atoms in bottom layer of moiré cell.
    _lat_kind : int
        Lattice type identifier (2, 4, or 6 for oblique, rectangular, or hexagonal).
    _if_plot : bool
        Flag for plotting intermediate results.
    _d_0 : float
        Average interlayer distance parameter.
    _d_1 : float
        Interlayer distance modulation amplitude.
    """

    def __init__(self, theta_360, mono_t_model, mono_b_model, inter_ids):
        """
        Initialize TwistGeometry with monolayer models and twist angle.

        Parameters
        ----------
        theta_360 : float
            Twist angle in degrees.
        mono_t_model : TBModel
            Tight-binding model for top monolayer.
        mono_b_model : TBModel
            Tight-binding model for bottom monolayer.
        inter_ids : tuple of float
            Interlayer distances (d_AA, d_AB) for AA and AB stacking regions.
        """
        self._theta_pi = theta_360 * np.pi / 180
        self._theta_360 = theta_360

        # Extract 2D lattice vectors
        self._mono_lat_t = mono_t_model._lat[0:2, 0:2]
        self._mono_lat_b = mono_b_model._lat[0:2, 0:2]

        # Calculate atomic positions in Cartesian coordinates
        self._mono_atom_pos_t = np.dot(mono_t_model._atom_position, mono_t_model._lat)
        self._mono_atom_pos_b = np.dot(mono_b_model._atom_position, mono_b_model._lat)

        # Store atomic information
        self._atom_name_t = mono_t_model._atom_name
        self._atom_name_b = mono_b_model._atom_name

        # Calculate atomic densities
        self._atom_num_per_area_t = len(self._mono_atom_pos_t) / \
                                    np.linalg.norm(np.cross(mono_t_model._lat[0], mono_t_model._lat[1]))
        self._atom_num_per_area_b = len(self._mono_atom_pos_b) / \
                                    np.linalg.norm(np.cross(mono_b_model._lat[0], mono_b_model._lat[1]))

        # Store interlayer distances
        self._d_AA, self._d_AB = inter_ids

    def Expand_cell(self, layer_index=0):
        """
        Expand monolayer unit cell to create a supercell for moiré pattern analysis.

        Parameters
        ----------
        layer_index : int, optional
            0 for top layer, 1 for bottom layer (default: 0).

        Returns
        -------
        points : numpy.ndarray
            Expanded atomic positions (Nx2 array).
        index : numpy.ndarray
            Indices mapping expanded positions to original atoms.

        Notes
        -----
        Expands the unit cell by ±150 repetitions in both lattice directions,
        generating approximately 90,000 points per atom for dense sampling.
        """
        # Select layer-specific parameters
        if layer_index:
            L1 = self._mono_lat_b[0]
            L2 = self._mono_lat_b[1]
            atom_pos = self._mono_atom_pos_b[:, 0:2]
        else:
            L1 = self._mono_lat_t[0]
            L2 = self._mono_lat_t[1]
            atom_pos = self._mono_atom_pos_t[:, 0:2]

        # Expansion parameters
        N = 150
        atom_number = np.shape(atom_pos)[0]

        # Initialize arrays
        points = np.zeros((atom_number, (N * 2) ** 2, 2))
        index = np.zeros((atom_number, (N * 2) ** 2, 2), dtype=int)

        # Generate expanded positions
        for a_n in range(atom_number):
            iii = 0
            for i in range(-N, N):
                for j in range(-N, N):
                    point = i * L1 + j * L2
                    points[a_n, iii, 0:2] = point + atom_pos[a_n, :]
                    index[a_n, iii, 0] = a_n
                    iii += 1

        # Reshape arrays
        points = np.reshape(points, (-1, 2))
        index = np.reshape(index, (-1, 2))
        index = index[:, 0]

        return points, index

    def cut_moire(self, points, index, Lm):
        """
        Filter points to those within the moiré unit cell.

        Parameters
        ----------
        points : numpy.ndarray
            Atomic positions to filter (Nx2 array).
        index : numpy.ndarray
            Corresponding atomic indices.
        Lm : numpy.ndarray
            Moiré lattice vectors (2x2 matrix).

        Returns
        -------
        filtered_points : numpy.ndarray
            Points within the moiré unit cell.
        filtered_index : numpy.ndarray
            Indices of filtered points.

        Notes
        -----
        Transforms points to moiré lattice coordinates and selects those
        within the unit cell [0,1) x [0,1).
        """
        # Transform to moiré lattice coordinates
        points_base = np.dot(points, np.linalg.inv(Lm))

        # Select points within unit cell
        mask = (points_base[:, 0] >= 0) & (points_base[:, 0] < 1) & \
               (points_base[:, 1] >= 0) & (points_base[:, 1] < 1)

        filtered_points = points[mask]
        filtered_index = index[mask]

        return filtered_points, filtered_index

    def standardizing(self, Lm):
        """
        Standardize moiré lattice vectors to align with monolayer coordinate system.

        Parameters
        ----------
        Lm : numpy.ndarray
            Initial moiré lattice vectors (2x2 matrix).

        Returns
        -------
        new_Lm : numpy.ndarray
            Standardized moiré lattice vectors (2x2 matrix).

        Notes
        -----
        Rotates moiré lattice by -θ/2, expresses in monolayer basis,
        rounds to integer combinations, and rotates back.
        """
        # Initialize arrays
        rota_Lm = np.zeros((2, 2), dtype=float)
        rota_base = np.zeros((2, 2), dtype=float)
        new_rota_Lm = np.zeros((2, 2), dtype=float)
        new_Lm = np.zeros((2, 2), dtype=float)

        # Rotate moiré lattice
        rota_Lm[0] = np.dot(R_theta(-self._theta_pi / 2), Lm[0])
        rota_Lm[1] = np.dot(R_theta(-self._theta_pi / 2), Lm[1])

        # Express in monolayer basis and round to integers
        rota_base[0] = np.dot(rota_Lm[0], np.linalg.inv(self._mono_lat_t))
        rota_base[1] = np.dot(rota_Lm[1], np.linalg.inv(self._mono_lat_t))
        rota_base = np.round(rota_base)

        # Convert back to Cartesian coordinates
        new_rota_Lm[0] = np.dot(rota_base[0], self._mono_lat_t)
        new_rota_Lm[1] = np.dot(rota_base[1], self._mono_lat_t)

        # Rotate back to original orientation
        new_Lm[0] = np.dot(R_theta(self._theta_pi / 2), new_rota_Lm[0])
        new_Lm[1] = np.dot(R_theta(self._theta_pi / 2), new_rota_Lm[1])

        return new_Lm

    def coincide_lat(self, up_points_use_1, dw_points_use_1, search_max,
                     accuracy=0.01, write_by_hand=None):
        """
        Identify coincident lattice points between rotated monolayers.

        Parameters
        ----------
        up_points_use_1 : numpy.ndarray
            Rotated top layer points (Nx2 array).
        dw_points_use_1 : numpy.ndarray
            Rotated bottom layer points (Mx2 array).
        search_max : float
            Search radius for coincident points.
        accuracy : float, optional
            Tolerance for point coincidence (default: 0.01 Å).
        write_by_hand : list of int, optional
            Manual selection of lattice vectors from coincident points.

        Returns
        -------
        Lm : numpy.ndarray
            Moiré lattice vectors derived from coincident points (2x2 matrix).

        Raises
        ------
        Exception
            If angle is incommensurable or insufficient coincident points.

        Notes
        -----
        Identifies points where rotated monolayers nearly coincide and uses
        these to determine primitive moiré lattice vectors.
        """
        # Plot if requested
        if self._if_plot:
            self.plot_up_down(up_points_use_1, dw_points_use_1, search_max)

        # Filter points within search radius
        mask_range_up_1 = (up_points_use_1[:, 0] > -search_max) & (up_points_use_1[:, 0] < search_max)
        up_points_use_1 = up_points_use_1[mask_range_up_1]
        mask_range_up_2 = (up_points_use_1[:, 1] > -search_max) & (up_points_use_1[:, 1] < search_max)
        up_points_use_1 = up_points_use_1[mask_range_up_2]

        mask_range_dw_1 = (dw_points_use_1[:, 0] > -search_max) & (dw_points_use_1[:, 0] < search_max)
        dw_points_use_1 = dw_points_use_1[mask_range_dw_1]
        mask_range_dw_2 = (dw_points_use_1[:, 1] > -search_max) & (dw_points_use_1[:, 1] < search_max)
        dw_points_use_1 = dw_points_use_1[mask_range_dw_2]

        # Find coincident points
        coin_points = []
        for i in range(len(up_points_use_1)):
            up_point = up_points_use_1[i]
            distance = np.linalg.norm(dw_points_use_1 - up_point, ord=2, axis=1, keepdims=True)
            distance = np.abs(distance)
            min_dis = np.min(distance)
            if min_dis < accuracy:
                coin_points.append(up_point)

        coin_points = np.array(coin_points)

        # Check for sufficient coincident points
        if len(coin_points) < 15:
            print("Warning: This angle is highly likely to be incommensurable")

        # Select moiré lattice vectors
        if write_by_hand is None:
            coin_points_use = np.copy(coin_points)

            # Remove origin point
            distance_coin = np.linalg.norm(coin_points_use, ord=2, axis=1, keepdims=True)
            coin_points_use = np.delete(coin_points_use, np.where(distance_coin < 0.01), axis=0)
            distance_coin = np.delete(distance_coin, np.where(distance_coin < 0.01), axis=0)
            distance_coin = np.around(distance_coin, 5)

            # Find shortest non-zero vectors
            Lm_min = np.min(distance_coin)
            mask_nearest = np.abs(distance_coin - Lm_min) < 1e-3
            nearest_indices = np.where(mask_nearest)[0]
            nearest_points = coin_points_use[nearest_indices]

            # Select appropriate vectors based on symmetry
            if (len(nearest_points) == 4) or (len(nearest_points) == 6):
                Lm_0 = nearest_points[len(nearest_points) - 1]
                Lm_1 = nearest_points[len(nearest_points) - 2]

                # Check for collinearity
                cos_alpha = np.dot(Lm_0, Lm_1) / (np.linalg.norm(Lm_0) * np.linalg.norm(Lm_1))
                if 1 - np.abs(cos_alpha) < 0.02:
                    Lm_1 = nearest_points[len(nearest_points) - 3]
            elif len(nearest_points) == 2:
                # For 2-fold symmetry
                point_A = coin_points_use[np.argmin(distance_coin)]
                min_distance = float('inf')
                point_B = None
                index_B = None
                dis_A = np.linalg.norm(point_A)

                for i in range(len(coin_points_use)):
                    point = coin_points_use[i]
                    point_dis = distance_coin[i]
                    cos_beta = np.dot(point, point_A) / (np.linalg.norm(point) * dis_A)

                    if np.abs(np.abs(cos_beta) - 1) > 0.05:
                        if point_dis < min_distance:
                            min_distance = point_dis
                            point_B = point
                            index_B = i

                Lm_0 = point_A
                Lm_1 = point_B

                # Remove selected point for further processing
                coin_points_use = np.delete(coin_points_use, index_B, axis=0)
                distance_coin = np.delete(distance_coin, index_B, axis=0)
            else:
                raise Exception("This angle is not commensurable")
        else:
            # Manual selection
            Lm_0 = coin_points[write_by_hand[0]]
            Lm_1 = coin_points[write_by_hand[1]]

        # Assemble lattice matrix
        Lm = np.zeros((2, 2), dtype=float)
        Lm[0] = Lm_0
        Lm[1] = Lm_1

        # Clean near-zero components
        for i in range(Lm.shape[0]):
            for j in range(Lm.shape[1]):
                if np.abs(Lm[i, j]) < 0.01:
                    Lm[i, j] = 0

        # Determine lattice type based on angle
        def vector_angle(v1, v2, degree=True):
            """Calculate angle between two 2D vectors."""
            # Compute dot product
            dot_product = v1[0] * v2[0] + v1[1] * v2[1]

            # Compute norms
            norm_v1 = np.hypot(v1[0], v1[1])
            norm_v2 = np.hypot(v2[0], v2[1])

            # Check for zero vectors
            if norm_v1 == 0 or norm_v2 == 0:
                raise ValueError("Vector cannot be zero!")

            # Compute cosine with numerical stability
            cos_theta = dot_product / (norm_v1 * norm_v2)
            cos_theta = max(min(cos_theta, 1.0), -1.0)

            # Compute angle
            angle_rad = np.arccos(cos_theta)

            return np.degrees(angle_rad) if degree else angle_rad

        # Classify lattice type
        if np.abs(vector_angle(Lm_1, Lm_0) - 60) < 1e-3:
            self._lat_kind = 6  # Hexagonal
        else:
            self._lat_kind = 2  # Oblique

        return Lm

    def right_hand(self, Lm):
        """
        Ensure moiré lattice vectors form a right-handed coordinate system.

        Parameters
        ----------
        Lm : numpy.ndarray
            Moiré lattice vectors (2x2 matrix).

        Returns
        -------
        Lm : numpy.ndarray
            Adjusted lattice vectors with positive z-component cross product.
        """
        # Create 3D version for cross product calculation
        Lm_use = np.zeros((3, 3), dtype=float)
        Lm_use[0:2, 0:2] = Lm[0:2, 0:2]

        # Calculate cross product in z-direction
        Lz = np.cross(Lm_use[0], Lm_use[1])

        # Flip second vector if left-handed
        if Lz[2] < 0:
            Lm[1] = -Lm[1]

        return Lm

    def gen_structure(self, zero_point, lim=20, search=0, accurate=0.01,
                      iLmfromG=False, if_gen_pos=False, write_by_hand=None,
                      if_plot=False):
        """
        Generate twisted bilayer atomic structure for a given twist angle.

        This is the main function that constructs the complete twisted bilayer
        structure by:
        1. Expanding monolayer unit cells
        2. Rotating layers by ±θ/2
        3. Identifying coincident points to determine moiré lattice
        4. Cutting atomic positions to moiré unit cell
        5. Applying out-of-plane relaxation
        6. Assembling final atomic positions

        Parameters
        ----------
        zero_point : int, list, or numpy.ndarray
            Reference point for alignment. Can be:
            - int: Index of atom to use as origin in each layer
            - list/tuple: [top_idx, bottom_idx] atom indices
            - numpy.ndarray: Direct coordinates [[top_x, top_y], [bottom_x, bottom_y]]
        lim : int, optional
            Limit for commensurate angle search in reciprocal space (default: 20).
        search : float, optional
            Search radius for coincident point method in real space (Å, default: 0).
        accurate : float, optional
            Tolerance for commensurability checks (default: 0.01).
        iLmfromG : bool, optional
            If True, generate moiré lattice from reciprocal space method (default: False).
        if_gen_pos : bool, optional
            If True, generate POSCAR file (default: False).
        write_by_hand : list of int, optional
            Manual selection of moiré lattice vectors (default: None).
        if_plot : bool, optional
            If True, plot intermediate results (default: False).

        Returns
        -------
        Lm : numpy.ndarray
            Moiré superlattice vectors (3x3 matrix including z-direction).
        moire_points : numpy.ndarray
            Atomic positions in moiré superlattice (Cartesian coordinates).
        atom_index : numpy.ndarray
            Indices mapping moiré atoms to original monolayer atoms.

        Notes
        -----
        The function supports two methods for moiré lattice determination:
        1. Real-space coincident point method (when search > 0)
        2. Reciprocal-space method (when iLmfromG = True)

        For heterostructures with different lattice constants, only the
        real-space method should be used.

        The out-of-plane relaxation uses a cosine modulation based on the
        moiré pattern to simulate structural corrugation.
        """
        # Set plotting flag
        self._if_plot = if_plot

        # Process zero_point input
        zero_point = np.array(zero_point)
        if len(zero_point.shape) < 2:
            # Input is atom indices
            atompos_t = np.dot(self._mono_atom_pos_t[:, 0:2], np.linalg.inv(self._mono_lat_t))
            zero_point_t = atompos_t[zero_point[0]]
            atompos_b = np.dot(self._mono_atom_pos_b[:, 0:2], np.linalg.inv(self._mono_lat_b))
            zero_point_b = atompos_b[zero_point[1]]
        else:
            # Input is direct coordinates
            zero_point_t = zero_point[0]
            zero_point_b = zero_point[1]

        # Rotate layers by ±θ/2
        theta = self._theta_pi

        # Expand monolayer unit cells
        points_t, index_t = self.Expand_cell(layer_index=0)
        points_b, index_b = self.Expand_cell(layer_index=1)

        # Shift to align zero points
        zero_point_xy_t = np.dot(zero_point_t, self._mono_lat_t)
        zero_point_xy_b = np.dot(zero_point_b, self._mono_lat_b)
        points_t = points_t - zero_point_xy_t
        points_b = points_b - zero_point_xy_b

        # Rotate layers
        up_points_use = np.dot(R_theta(theta / 2), points_t.T).T
        down_points_use = np.dot(R_theta(-theta / 2), points_b.T).T

        # Determine moiré lattice
        if search != 0:
            # Check if zero points exist in both layers
            mask_t = (points_t[:, 0] > -1e-2) & (points_t[:, 0] < 1e-2) & \
                     (points_t[:, 1] > -1e-2) & (points_t[:, 1] < 1e-2)
            mask_b = (points_b[:, 0] > -1e-2) & (points_b[:, 0] < 1e-2) & \
                     (points_b[:, 1] > -1e-2) & (points_b[:, 1] < 1e-2)

            if np.any(mask_t) & np.any(mask_b):
                # Use coincident point method
                index_zero_t = index_t[mask_t]
                index_zero_b = index_b[mask_b]

                mask_index_t = (index_t == index_zero_t[0])
                mask_index_b = (index_b == index_zero_b[0])
                up_points_use_1 = up_points_use[mask_index_t]
                dw_points_use_1 = down_points_use[mask_index_b]

                Lm = self.coincide_lat(up_points_use_1, dw_points_use_1,
                                       search, accuracy=accurate,
                                       write_by_hand=write_by_hand)
            else:
                # Fall back to reciprocal space method
                Lm = self.from_set_gen_Lm(lim=lim, accurate=accurate,
                                          iLmfromG=iLmfromG,
                                          write_by_hand=write_by_hand)
        else:
            # Use reciprocal space method
            Lm = self.from_set_gen_Lm(lim=lim, accurate=accurate,
                                      iLmfromG=iLmfromG,
                                      write_by_hand=write_by_hand)

        # Store moiré lattice
        self._Lm = np.copy(Lm)

        # Apply small shifts to avoid edge cases, cut to moiré cell
        if np.abs(np.linalg.norm(self._mono_lat_b[0]) -
                  np.linalg.norm(self._mono_lat_t[0])) < 1e-3:
            # For homostructures, try multiple shifts
            small_shift = np.array([[0.0, 0.0],
                                    [0.1, 0.0],
                                    [0.0, 0.1],
                                    [0.1, 0.1]])
        else:
            # For heterostructures, simpler approach
            small_shift = np.array([[0.1, 0.0]])

        # Try different shifts to get equal number of atoms in both layers
        for i in range(len(small_shift)):
            up_points_use_shifted = np.around(up_points_use, 5) + small_shift[i]
            down_points_use_shifted = np.around(down_points_use, 5) + small_shift[i]

            up_points_use2, index_up = self.cut_moire(up_points_use_shifted,
                                                      index_t, Lm)
            down_points_use2, index_down = self.cut_moire(down_points_use_shifted,
                                                          index_b, Lm)

            # Remove shift
            up_points_use2 = up_points_use2 - small_shift[i]
            down_points_use2 = down_points_use2 - small_shift[i]

            # Check atom count equality
            if len(index_up) == len(index_down):
                break

        # Apply out-of-plane relaxation
        points_dz_t = self.out_of_plane_relax(up_points_use2)
        points_dz_b = self.out_of_plane_relax(down_points_use2)

        # Prepare z-coordinates
        mono_dz_t = self._mono_atom_pos_t[:, 2]
        mono_dz_b = self._mono_atom_pos_b[:, 2]

        # Center z-coordinates and separate layers
        mono_dz_t = mono_dz_t - ((np.max(mono_dz_t) + np.min(mono_dz_t)) / 2) + 20
        mono_dz_b = mono_dz_b - ((np.max(mono_dz_b) + np.min(mono_dz_b)) / 2) + 20

        # Calculate layer thicknesses
        max_min_dz_t = np.max(mono_dz_t) - np.min(mono_dz_t)
        max_min_dz_b = np.max(mono_dz_b) - np.min(mono_dz_b)

        # Assemble final 3D positions
        up_points = np.zeros((up_points_use2.shape[0], 3))
        down_points = np.zeros((down_points_use2.shape[0], 3))

        for i in range(len(up_points_use2)):
            up_points[i, 0:2] = up_points_use2[i]
            up_points[i, 2] = mono_dz_t[index_up[i]] + max_min_dz_t / 2 + 0.5 * points_dz_t[i]

        for i in range(len(down_points_use2)):
            down_points[i, 0:2] = down_points_use2[i]
            down_points[i, 2] = mono_dz_b[index_down[i]] - max_min_dz_b / 2 - 0.5 * points_dz_b[i]

        # Store atom counts
        self._t_num = len(up_points)
        self._b_num = len(down_points)

        # Combine layers
        moire_points = np.vstack([up_points, down_points])
        atom_index = np.hstack([index_up, index_down])

        # Convert Lm to 3D with vacuum
        Lm_2d = np.vstack([Lm[0], Lm[1]])
        Lm_2d = np.hstack([Lm_2d, np.array([[0], [0]])])
        Lm = np.vstack([Lm_2d, np.array([[0, 0, 40]])])  # 40 Å vacuum

        # Clean edge atoms
        moire_points_temp = np.dot(moire_points, np.linalg.inv(Lm))
        for i in range(len(moire_points_temp)):
            for j in range(2):
                if np.abs(moire_points_temp[i, j]) < 0.001:
                    moire_points_temp[i, j] = 0
                elif np.abs(moire_points_temp[i, j] - 1) < 0.001:
                    moire_points_temp[i, j] = 0

        moire_points = np.dot(moire_points_temp, Lm)

        # Store atomic names
        self._atom_name = []
        for i in range(self._t_num):
            self._atom_name.append(self._atom_name_t[atom_index[i]])
        for i in range(self._t_num, len(moire_points)):
            self._atom_name.append(self._atom_name_b[atom_index[i]])

        # Store final results
        self._Lm = Lm
        self._moire_points = moire_points
        self._atom_index = atom_index

        # Generate POSCAR if requested
        if if_gen_pos:
            prefix = str(np.round(self._theta_360, 2))
            self.gen_POSCAR(moire_points, prefix)

        return Lm, moire_points, atom_index

    def gen_POSCAR(self, moire_points, prefix):
        """
        Generate VASP POSCAR file for the twisted bilayer structure.

        Parameters
        ----------
        moire_points : numpy.ndarray
            Atomic positions in Cartesian coordinates (Nx3 array).
        prefix : str
            Filename prefix (typically twist angle).
        """
        # Identify unique atom types
        atom_kind = np.unique(self._atom_name)
        atom_pos_list = []
        each_kind_num = []
        atom_name = np.array(self._atom_name)

        # Group atoms by element
        for i in range(len(atom_kind)):
            mask = (atom_name == atom_kind[i])
            one_kind_points = moire_points[mask]
            atom_pos_list.append(one_kind_points)
            each_kind_num.append(len(one_kind_points))

        # Combine all positions
        out_points = np.vstack(atom_pos_list)

        # Format atom type and count strings
        sert_use_atom = ' '
        sert_use_num = ' '
        for i in range(len(atom_kind)):
            sert_use_atom = sert_use_atom + '   ' + atom_kind[i]
        for i in range(len(atom_kind)):
            sert_use_num = sert_use_num + '   ' + str(int(each_kind_num[i]))

        # Combine lattice and positions
        POSCAR = np.vstack([self._Lm, out_points])

        # Write to file
        file_name = "POSCAR_" + prefix + ".vasp"
        np.savetxt(file_name, POSCAR, fmt='%15.10f')

        # Add VASP file headers
        with open(file_name, 'r') as fp:
            lines = list(fp)

        # Insert VASP headers
        lines.insert(0, "Generated by MoireStudio   " + "twist angle: " +
                     str(self._theta_360) + '\n' + str(1) + '\n')
        lines.insert(4, sert_use_atom + '\n' + sert_use_num + '\n' + 'Cartesian\n')

        # Write updated file
        with open(file_name, 'w') as fp:
            fp.write(''.join(lines))

    def out_of_plane_relax(self, tao):
        """
        Calculate out-of-plane relaxation based on moiré pattern.

        Parameters
        ----------
        tao : numpy.ndarray
            In-plane positions in moiré cell (Nx2 array).

        Returns
        -------
        d_use : numpy.ndarray
            Out-of-plane displacements (N array).

        Notes
        -----
        For hexagonal symmetry (lat_kind=6), uses 3 cosine terms.
        For rectangular symmetry (lat_kind=4), uses 2 cosine terms.
        The modulation amplitude depends on AA and AB stacking distances.
        """
        # Hexagonal symmetry
        if self._lat_kind == 6:
            self._d_0 = (self._d_AA + 2 * self._d_AB) / 3
            self._d_1 = (self._d_AA - self._d_AB) / 9

            d_use = np.zeros((len(tao),), dtype=float)
            b_base = reciprocal_base(self._Lm)

            for i in range(len(tao)):
                ll_1 = np.dot(tao[i], b_base[0])
                ll_2 = np.dot(tao[i], b_base[1])
                ll_3 = np.dot(tao[i], -b_base[0] - b_base[1])
                d_use[i] = self._d_0 + 2 * self._d_1 * (np.cos(ll_1) +
                                                        np.cos(ll_2) +
                                                        np.cos(ll_3))
        # Rectangular symmetry
        else:
            self._d_0 = (self._d_AA + self._d_AB) / 2
            self._d_1 = (self._d_AA - self._d_AB) / 8

            d_use = np.zeros((len(tao),), dtype=float)
            b_base = reciprocal_base(self._Lm)

            for i in range(len(tao)):
                ll_1 = np.dot(tao[i], b_base[0])
                ll_2 = np.dot(tao[i], b_base[1])
                d_use[i] = self._d_0 + self._d_1 * (np.cos(ll_1) + np.cos(ll_2))

        return d_use

    def plot_up_down(self, up_points_use, down_points_use, lim):
        """
        Plot rotated monolayer points for visualization.

        Parameters
        ----------
        up_points_use : numpy.ndarray
            Rotated top layer points (Nx2 array).
        down_points_use : numpy.ndarray
            Rotated bottom layer points (Mx2 array).
        lim : float
            Plotting limit in both x and y directions.
        """
        # Filter points within limits
        mask_up = (up_points_use[:, 0] >= -lim) & (up_points_use[:, 0] <= lim) & \
                  (up_points_use[:, 1] >= -lim) & (up_points_use[:, 1] <= lim)
        mask_dw = (down_points_use[:, 0] >= -lim) & (down_points_use[:, 0] <= lim) & \
                  (down_points_use[:, 1] >= -lim) & (down_points_use[:, 1] <= lim)

        up_plot = up_points_use[mask_up]
        dw_plot = down_points_use[mask_dw]

        # Create plot
        plt.figure(figsize=(6, 6))
        plt.scatter(dw_plot[:, 0], dw_plot[:, 1], c="b", label="Bottom")
        plt.scatter(up_plot[:, 0], up_plot[:, 1], s=60, c="r", alpha=0.5, label="Top")
        plt.xlabel("x (Å)")
        plt.ylabel("y (Å)")
        plt.title("Rotated Monolayer Points")
        plt.legend()
        plt.axis('equal')
        plt.show()

    def from_set_gen_Lm(self, lim=10, accurate=0.001, iLmfromG=False,
                        write_by_hand=None):
        """
        Generate moiré lattice vectors from commensurate angle solutions.

        Parameters
        ----------
        lim : int, optional
            Search limit for integer combinations (default: 10).
        accurate : float, optional
            Tolerance for commensurability (default: 0.001).
        iLmfromG : bool, optional
            Use reciprocal space method (default: False).
        write_by_hand : list of int, optional
            Manual selection of vectors from solution set.

        Returns
        -------
        Lm : numpy.ndarray
            Moiré lattice vectors (2x2 matrix).

        Raises
        ------
        Exception
            If angle is incommensurate or insufficient solutions.

        Notes
        -----
        For heterostructures with different lattice constants, iLmfromG
        should be set to False.
        """
        # Get commensurate solutions
        com_set = self.commensurance_list(self._theta_360, lim=lim,
                                          accurate=accurate)
        com_set = np.array(com_set, dtype=float)

        if com_set.size == 0:
            raise Exception("This angle is not commensurate")

        # Convert to Cartesian coordinates and rotate to moiré frame
        vec_cart = np.dot(com_set, self._mono_lat_b)  # (N,2)
        vec_moire = np.dot(R_theta(-self._theta_pi / 2), vec_cart.T).T  # (N,2)

        # Plot if requested
        if hasattr(self, "_if_plot") and self._if_plot:
            com_set_xy = np.dot(vec_cart, R_theta(self._theta_pi / 2))
            self.plot_up_down(com_set_xy, com_set_xy, lim * 4)

        # Remove trivial (near-zero) solutions
        norms = np.linalg.norm(vec_moire, axis=1)
        mask = norms > 1e-3
        vec_moire = vec_moire[mask]
        com_set = com_set[mask]
        norms = norms[mask]

        if vec_moire.shape[0] == 0:
            raise Exception("No non-trivial moiré translations found; "
                            "this angle is likely incommensurate")

        # Helper functions
        def _infer_lat_kind(v1, v2, rel_len_tol=0.10, cos_hex_tol=0.15,
                            cos_rect_tol=0.15):
            """Classify lattice type from two basis vectors."""
            a = np.linalg.norm(v1)
            b = np.linalg.norm(v2)
            if a < 1e-8 or b < 1e-8:
                return 2

            cosang = np.dot(v1, v2) / (a * b)
            cosang = np.clip(cosang, -1.0, 1.0)

            # Hexagonal (60° or 120°)
            if abs(a - b) / max(a, b) < rel_len_tol and \
                    abs(abs(cosang) - 0.5) < cos_hex_tol:
                return 6

            # Rectangular (90°)
            if abs(cosang) < cos_rect_tol:
                return 4

            # Oblique
            return 2

        def _are_collinear(v1, v2, tol=1e-8):
            """Check if two 2D vectors are nearly collinear."""
            if v1 is None or v2 is None:
                return True

            v1 = np.asarray(v1, dtype=float).ravel()
            v2 = np.asarray(v2, dtype=float).ravel()

            if v1.shape != (2,) or v2.shape != (2,):
                return True

            cross = v1[0] * v2[1] - v1[1] * v2[0]
            return abs(cross) < tol

        def _pair_area(v1, v2):
            """Calculate area of parallelogram spanned by two vectors."""
            return abs(v1[0] * v2[1] - v1[1] * v2[0])

        def _find_min_primitive_area(vec_pool, area_tol=1e-8):
            """Find minimum non-zero area from vector pairs."""
            vec_pool = np.asarray(vec_pool, dtype=float)
            m = vec_pool.shape[0]

            if m < 2:
                return None

            min_area = None
            for i in range(m):
                v1 = vec_pool[i]
                for j in range(i + 1, m):
                    v2 = vec_pool[j]
                    area = _pair_area(v1, v2)

                    if area <= area_tol:
                        continue

                    if (min_area is None) or (area < min_area):
                        min_area = area

            return min_area

        def _select_basis(vec_pool, target_area=None, max_candidates=32,
                          area_tol=1e-8, area_rel_window=0.05,
                          prefer_symmetric=True):
            """Select optimal basis vectors from candidate pool."""
            vec_pool = np.asarray(vec_pool, dtype=float)

            if vec_pool.ndim != 2 or vec_pool.shape[0] < 2 or vec_pool.shape[1] != 2:
                return None, None, None

            m = min(max_candidates, vec_pool.shape[0])
            sub = vec_pool[:m]
            lengths = np.linalg.norm(sub, axis=1)

            best_score = 0.0
            best_pair = None
            best_kind = 2

            # Set area selection window
            if target_area is not None:
                area_window = max(area_rel_window * target_area, area_tol)
            else:
                area_window = None

            # Evaluate all pairs
            for i in range(m):
                v1 = sub[i]
                for j in range(i + 1, m):
                    v2 = sub[j]
                    area = _pair_area(v1, v2)

                    if area <= area_tol:
                        continue

                    # Filter by target area
                    if target_area is not None and \
                            abs(area - target_area) > area_window:
                        continue

                    # Classify lattice type
                    kind = _infer_lat_kind(v1, v2)
                    score = area

                    # Penalize very different lengths
                    L1 = lengths[i]
                    L2 = lengths[j]
                    Lmax = max(L1, L2)

                    if Lmax > 0:
                        ratio = min(L1, L2) / Lmax
                        if ratio < 0.5:
                            score *= 0.8

                    # Slight preference for equal lengths
                    if np.abs(np.linalg.norm(L1) - np.linalg.norm(L2)) < 1e-2:
                        score *= 1.5

                    # Prefer symmetric lattices
                    if prefer_symmetric:
                        if kind == 6:
                            score *= 2
                        elif kind == 4:
                            score *= 1.5

                    # Update best candidate
                    if score > best_score:
                        best_score = score
                        best_pair = (v1, v2)
                        best_kind = kind

            if best_pair is None:
                return None, None, None

            return best_pair[0], best_pair[1], best_kind

        # For heterostructures, disable reciprocal space method
        if np.abs(np.linalg.norm(self._mono_lat_t[0]) -
                  np.linalg.norm(self._mono_lat_b[0])) > 1e-3:
            iLmfromG = False

        # Sort vectors by length
        order = np.argsort(norms)
        vec_sorted = vec_moire[order]
        norms_sorted = norms[order]

        # Estimate primitive area from shortest vectors
        max_pool = min(32, vec_sorted.shape[0])
        vec_pool_for_area = vec_sorted[:max_pool]
        min_area = _find_min_primitive_area(vec_pool_for_area)

        if min_area is None:
            raise Exception("All candidate moiré translations are nearly "
                            "collinear; cannot form a 2D moiré lattice.")

        # Prepare candidate vectors for different selection methods
        dmin = norms_sorted[0]
        len_tol = max(0.10 * dmin, 1e-3)
        cand_mask = norms_sorted <= dmin + len_tol
        cand = vec_sorted[cand_mask]

        if cand.shape[0] < 2:
            cand = vec_sorted[:min(8, vec_sorted.shape[0])]

        # Select basis vectors
        Lm1, Lm2 = None, None

        if write_by_hand is not None:
            # Manual selection
            idx1, idx2 = write_by_hand

            if idx1 < 0 or idx1 >= vec_moire.shape[0] or \
                    idx2 < 0 or idx2 >= vec_moire.shape[0]:
                raise IndexError("write_by_hand index out of range")

            Lm1 = vec_moire[idx1]
            Lm2 = vec_moire[idx2]

            # Check for collinearity
            if _are_collinear(Lm1, Lm2):
                raise ValueError("Manually selected vectors are nearly "
                                 "collinear; choose non-collinear vectors.")
        else:
            if iLmfromG:
                # Reciprocal space method (for homostructures only)
                v_11, v_12 = get_perpendicular_unit_vector(self._mono_lat_t[0])
                v_21, v_22 = get_perpendicular_unit_vector(self._mono_lat_t[1])

                for i in range(cand.shape[0]):
                    use_v1 = cand[i]
                    unit_v1 = use_v1 / np.linalg.norm(use_v1)

                    ilinerly_1, use_sign_1 = linearly_dependent(unit_v1, v_12,
                                                                if_sign=True)
                    if ilinerly_1 and use_sign_1 > 0:
                        Lm1 = use_v1

                    ilinerly_2, use_sign_2 = linearly_dependent(unit_v1, v_22,
                                                                if_sign=True)
                    if ilinerly_2 and use_sign_2 > 0:
                        Lm2 = use_v1

                # Fallback if reciprocal method fails
                if (Lm1 is None) or (Lm2 is None) or _are_collinear(Lm1, Lm2):
                    Lm1, Lm2, _ = _select_basis(vec_pool_for_area,
                                                target_area=min_area)

                    if Lm1 is None:
                        raise Exception("Failed to extract primitive moiré "
                                        "lattice vectors from commensurate set.")
            else:
                # Automatic selection based on primitive area
                Lm1, Lm2, _ = _select_basis(vec_pool_for_area,
                                            target_area=min_area)

                if Lm1 is None:
                    raise Exception("Failed to extract primitive moiré "
                                    "lattice vectors from commensurate set.")

        # Assemble lattice matrix
        Lm = np.zeros((2, 2), dtype=float)
        Lm[0] = Lm1
        Lm[1] = Lm2

        # Ensure right-handed coordinate system
        Lm = self.right_hand(Lm)

        # Determine and store lattice type
        self._lat_kind = _infer_lat_kind(Lm[0], Lm[1])

        return Lm

    def commensurance_list(self, theta_360, lim=10, accurate=0.01, find=False):
        """
        Find integer solutions for commensurate angles.

        Parameters
        ----------
        theta_360 : float
            Twist angle in degrees.
        lim : int, optional
            Search limit for integer indices (default: 10).
        accurate : float, optional
            Tolerance for integer condition (default: 0.01).
        find : bool, optional
            If True, search only positive indices (default: False).

        Returns
        -------
        com_set : numpy.ndarray
            Integer solutions in bottom layer basis (Nx2 array).

        Notes
        -----
        Solves the commensurability condition: R(θ)·L_t·n = L_b·m
        where n and m are integer vectors.
        """
        theta_pi = (theta_360 / 180) * np.pi

        # Get transformation matrix
        Lt = self._mono_lat_t.T
        Lb = self._mono_lat_b.T
        LRL = np.dot(np.linalg.inv(Lb), np.dot(R_theta(theta_pi), Lt))

        # Search for integer solutions
        com_set = []
        begin_int = 0 if find else -lim

        for i in range(begin_int, lim + 1):
            for j in range(begin_int, lim + 1):
                nn_arr = np.array([i, j])
                mm_arr = np.dot(LRL, nn_arr)

                # Check integer condition
                if (np.abs(mm_arr[0] - np.round(mm_arr[0])) < accurate) and \
                        (np.abs(mm_arr[1] - np.round(mm_arr[1])) < accurate):
                    com_set.append(mm_arr)

        com_set = np.array(np.round(com_set), dtype=int)
        return com_set

    def find_commensurate_angle(self, max_angle, min_angle, lim=10,
                                step=0.01, accurate=0.01):
        """
        Search for commensurate angles within a range.

        Parameters
        ----------
        max_angle : float
            Maximum twist angle (degrees).
        min_angle : float
            Minimum twist angle (degrees).
        lim : int, optional
            Search limit for integer solutions (default: 10).
        step : float, optional
            Angle step size (degrees, default: 0.01).
        accurate : float, optional
            Tolerance for commensurability (default: 0.01).

        Returns
        -------
        sorted_data : numpy.ndarray
            Array of [angle, solution_count, moiré_cell_size] for each
            commensurate angle.

        Notes
        -----
        The moiré cell size is estimated from the number of commensurate
        solutions and atomic densities.
        """
        # Generate angle list
        angle_num = int(((max_angle - min_angle) / step) + 1)
        theta_list = np.linspace(max_angle, min_angle, angle_num)

        com_num = []
        theta_use = []

        # Search for commensurate angles
        for i, theta_i in enumerate(theta_list):
            if i % 20 == 0:
                print(f"{int((i / len(theta_list)) * 100)}%")

            com_set = self.commensurance_list(theta_i, lim=lim,
                                              accurate=accurate, find=True)
            if len(com_set) > 0:
                com_num.append(len(com_set))
                theta_use.append(theta_i)

        com_num = np.array(com_num)
        theta_use = np.array(theta_use)

        # Calculate moiré cell size
        use_list = np.zeros((len(com_num), 3), dtype=float)
        use_coe = (lim + 1) * (lim + 1) * len(self._mono_atom_pos_b) * \
                  (1 + self._atom_num_per_area_t / self._atom_num_per_area_b)

        for i in range(len(com_num)):
            use_list[i, 0] = np.round(theta_use[i], 3)  # Angle
            use_list[i, 1] = int(com_num[i])  # Solution count
            use_list[i, 2] = int(use_coe / com_num[i])  # Moiré cell size

        # Sort by angle
        sorted_data = use_list[use_list[:, 0].argsort()]
        return sorted_data