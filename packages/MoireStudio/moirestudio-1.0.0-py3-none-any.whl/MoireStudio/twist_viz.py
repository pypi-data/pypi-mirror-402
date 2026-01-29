"""
Visualization utilities for moiré/twist toolkit.
Provides functions for band structure plotting, moiré lattice visualization, and angle analysis.
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib.pyplot as plt
from typing import Iterable, Optional, Sequence, Tuple, List
from pathlib import Path


def _gammaize(labels: Optional[Sequence[str]]) -> Optional[Tuple[str, ...]]:
    """
    Replace plain 'G' with LaTeX Gamma symbol for prettier band labels.

    Args:
        labels: Sequence of label strings

    Returns:
        Fixed labels with 'G' replaced by Γ symbol, or None if input is None
    """
    if labels is None:
        return None

    fixed = []
    for x in labels:
        if x == "G":
            fixed.append(r"$\Gamma$")
        elif x == "g":
            fixed.append(r"$\gamma$")
        else:
            fixed.append(str(x))

    return tuple(fixed)


def _draw_parallelogram(ax: plt.Axes, Lm2x2: np.ndarray, lw: float = 1.25, ls: str = "--") -> None:
    """
    Draw moiré real-space unit cell as a dashed parallelogram.

    Args:
        ax: Matplotlib axes to draw on
        Lm2x2: 2x2 lattice vectors
        lw: Line width
        ls: Line style
    """
    a1, a2 = np.asarray(Lm2x2[0]), np.asarray(Lm2x2[1])
    origin = np.array([0.0, 0.0])
    pts = np.vstack([origin, a1, a1 + a2, a2, origin])
    ax.plot(pts[:, 0], pts[:, 1], linestyle=ls, linewidth=lw)

def plot_spinful_band(
        filepath = ".",
        filename_up = "Band_up.dat",
        filename_dn = "Band_dn.dat",
        ylim: Optional[Tuple[float, float]] = None,
        color_up: Optional[str] = None,
        color_dn: Optional[str] = None,
        linewidth: float = 2.0,
        save: Optional[str] = None,
        font_size=20,
        units: Optional[str] = "eV",
        ishow_x_label: bool = True,
        ishow_y_label: bool = True,
        legend_loc: str = "best",
        legend_labels: Optional[Tuple[str, str]] = None
):
    evals_up, _ = read_band_file(filename=filepath + "/" + filename_up)
    evals_dn, k_dist = read_band_file(filename=filepath + "/" + filename_dn)
    k_nodes = np.loadtxt(filepath + "/k_node.txt")
    with open(filepath+"/k_labels.txt", "r", encoding="utf-8") as f:
        content = f.read()
        labels = eval(content)
    # Create plot
    # plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = font_size
    plt.rcParams['figure.figsize'] = (8, 6)
    fig, ax = plt.subplots()

    # Set x-ticks and labels
    if labels is not None:
        ax.set_xticks(k_nodes)
        ax.set_xticklabels(_gammaize(labels))
    else:
        ax.set_xticks(k_nodes)

    ax.set_xlim(k_nodes[0], k_nodes[-1])

    if ylim is not None:
        ax.set_ylim(*ylim)

    if ishow_x_label:
        ax.set_xlabel("k-path")
    if ishow_y_label:
        if units == "eV":
            ax.set_ylabel("Energy (eV)")
        else:
            ax.set_ylabel("Energy (meV)")
    # Draw bands
    if color_up is None:
        color_up = "r"
    if color_dn is None:
        color_dn = "b"

    if legend_labels is None:
        label_up = "Spin up"
        label_dn = "Spin down"
    else:
        label_up, label_dn = legend_labels

    for n in range(evals_up.shape[1]):
        if n == 0:
            ax.plot(k_dist, evals_dn[:, n], linewidth=linewidth, color=color_dn, label=label_dn)
            ax.plot(k_dist, evals_up[:, n], linewidth=linewidth, color=color_up, label=label_up)
        else:
            ax.plot(k_dist, evals_dn[:, n], linewidth=linewidth, color=color_dn)
            ax.plot(k_dist, evals_up[:, n], linewidth=linewidth, color=color_up)

    # Add vertical lines at high-symmetry points
    for x in k_nodes:
        ax.axvline(x=x, linewidth=1.0, color="k", alpha=0.35)

    if legend_loc is not None:
        ax.legend(loc=legend_loc, fontsize=font_size - 8, frameon=False)

    fig.tight_layout()

    if save is not None:
        fig.savefig(save, dpi=200, bbox_inches='tight')

    plt.close(fig)

def plot_band(
        ylim: Optional[Tuple[float, float]] = None,
        ef: float = 0.0,
        load: Optional[str] = None,
        save: Optional[str] = None,
        show: bool = True,
        color: Optional[str] = None,
        linewidth: float = 2.0,
        isparse: bool = False,
        units: Optional[str] = "eV",
        ishow_x_label: bool = True,
        ishow_y_label: bool = True,
        font_size=20
):
    """
    Plot band structure from pre-calculated data files.

    This function loads band structure data from files and plots it.

    Args:
        ylim: Energy window to display (ymin, ymax)
        ef: Fermi level to subtract from eigenvalues before plotting
        load: Directory containing band.txt, k_dist.txt, and k_node.txt files
        save: Path where the figure will be saved (PNG, PDF, etc.)
        show: Whether to call plt.show()
        color: Matplotlib color for bands. If None, uses rcParams default.
        linewidth: Line width for band curves
        isparse: If True, plot as scatter points instead of lines
        units: plot units
        ishow_x_label: If True, plot x-axis title
        ishow_y_label: If True, plot y-axis title

    Returns:
        None
    """
    # Load data from files
    load = Path(load)
    if isparse:
        evals = np.loadtxt(load / "band.txt")
        k_dist = np.loadtxt(load / "k_dist.txt")
    else:
        evals, k_dist = read_band_file(filename=str(load) + "/" + "BAND.dat")
    k_nodes = np.loadtxt(load / "k_node.txt")

    if ef != 0.0:
        evals = evals - ef

    # Create plot
    # plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = font_size
    plt.rcParams['figure.figsize'] = (8, 6)
    fig, ax = plt.subplots()
    try:
        with open(str(load) + "/k_labels.txt", "r", encoding="utf-8") as f:
            content = f.read()
            labels = eval(content)
    except:
        labels = None

    # Set x-ticks and labels
    if labels is not None:
        ax.set_xticks(k_nodes)
        ax.set_xticklabels(_gammaize(labels))
    else:
        ax.set_xticks(k_nodes)

    ax.set_xlim(k_nodes[0], k_nodes[-1])

    if ylim is not None:
        ax.set_ylim(*ylim)

    if ishow_x_label:
        ax.set_xlabel("k-path")
    if ishow_y_label:
        if units == "eV":
            ax.set_ylabel("Energy (eV)")
        else:
            ax.set_ylabel("Energy (meV)")

    # Draw bands
    if isparse:
        for n in range(evals.shape[1]):
            if color is None:
                plt.scatter(k_dist, evals[:, n], s=5, color='b')
            else:
                plt.scatter(k_dist, evals[:, n], s=5, color=color)
    else:
        for n in range(evals.shape[1]):
            if color is None:
                ax.plot(k_dist, evals[:, n], linewidth=linewidth)
            else:
                ax.plot(k_dist, evals[:, n], linewidth=linewidth, color=color)

    # Add vertical lines at high-symmetry points
    for x in k_nodes:
        ax.axvline(x=x, linewidth=1.0, color="k", alpha=0.35)

    fig.tight_layout()

    if save is not None:
        fig.savefig(save, dpi=200, bbox_inches='tight')

    if show:
        plt.show()

    plt.close(fig)


def plot_moire_points(
        tb_structure,
        annotate: bool = False,
        draw_cell: bool = True,
        equal_aspect: bool = True,
        alpha_top: float = 0.9,
        alpha_bottom: float = 0.6,
        s_top: float = 18.0,
        s_bottom: float = 12.0,
        save: Optional[str] = None,
        show: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Scatter plot of moiré real-space points for a TB_structure.

    Expects the following attributes on *tb_structure*:
      - _moire_points: (N, 3) Cartesian coordinates (x, y, z)
      - _t_num: Number of top-layer points (first _t_num belong to top)
      - _Lm: (3, 3) or (2, 2) real-space moiré lattice vectors in rows

    Args:
        tb_structure: Structure object with moiré lattice information
        annotate: Whether to annotate a subset of points
        draw_cell: Whether to draw the moiré unit cell
        equal_aspect: Whether to set equal aspect ratio
        alpha_top: Alpha transparency for top layer points
        alpha_bottom: Alpha transparency for bottom layer points
        s_top: Marker size for top layer points
        s_bottom: Marker size for bottom layer points
        save: Output figure path
        show: Whether to display the figure

    Returns:
        Tuple of (top_layer_points, bottom_layer_points, lattice_vectors)
    """
    P = np.asarray(tb_structure._moire_points, float)
    t_num = int(tb_structure._t_num)
    Lm = np.asarray(tb_structure._Lm, float)
    Lm2 = Lm[:2, :2] if Lm.shape == (3, 3) else Lm

    # Split top/bottom layers
    P_top = P[:t_num, :2]
    P_bot = P[t_num:, :2]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(P_bot[:, 0], P_bot[:, 1], s=s_bottom, alpha=alpha_bottom, label="bottom layer")
    ax.scatter(P_top[:, 0], P_top[:, 1], s=s_top, alpha=alpha_top, label="top layer")

    if draw_cell:
        _draw_parallelogram(ax, Lm2)

    if annotate:
        # Annotate subset of points to avoid clutter
        step_t = max(1, len(P_top) // 50)
        step_b = max(1, len(P_bot) // 50)

        for i in range(0, len(P_top), step_t):
            ax.annotate(f"t{i}", (P_top[i, 0], P_top[i, 1]), fontsize=7, alpha=0.7)

        for i in range(0, len(P_bot), step_b):
            ax.annotate(f"b{i}", (P_bot[i, 0], P_bot[i, 1]), fontsize=7, alpha=0.7)

    ax.set_xlabel("x (Å)")
    ax.set_ylabel("y (Å)")

    if equal_aspect:
        ax.set_aspect("equal", adjustable="box")

    ax.legend(loc="best", frameon=False)
    fig.tight_layout()

    if save is not None:
        fig.savefig(save, dpi=200, bbox_inches='tight')

    if show:
        plt.show()

    plt.close(fig)

    return P_top, P_bot, Lm2


def scatter_up_down(
        up_points_xy: np.ndarray,
        down_points_xy: np.ndarray,
        lim: Optional[float] = None,
        save: Optional[str] = None,
        show: bool = True,
) -> None:
    """
    Quick scatter plot for two pre-rotated layers (Γ-aligned).

    Similar to original plot_up_down function.

    Args:
        up_points_xy: Coordinates of upper layer points (N, 2)
        down_points_xy: Coordinates of lower layer points (M, 2)
        lim: Limit for displayed region (-lim to +lim in both dimensions)
        save: Output figure path
        show: Whether to display the figure
    """
    up = np.asarray(up_points_xy, float)
    dw = np.asarray(down_points_xy, float)

    if lim is not None:
        mask_up = (up[:, 0] >= -lim) & (up[:, 0] <= lim) & (up[:, 1] >= -lim) & (up[:, 1] <= lim)
        mask_dw = (dw[:, 0] >= -lim) & (dw[:, 0] <= lim) & (dw[:, 1] >= -lim) & (dw[:, 1] <= lim)
        up = up[mask_up]
        dw = dw[mask_dw]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(dw[:, 0], dw[:, 1], s=14, alpha=0.8, label="down layer")
    ax.scatter(up[:, 0], up[:, 1], s=22, alpha=0.6, label="up layer")

    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False)
    ax.set_xlabel("x (Å)")
    ax.set_ylabel("y (Å)")

    fig.tight_layout()

    if save is not None:
        fig.savefig(save, dpi=200, bbox_inches='tight')

    if show:
        plt.show()

    plt.close(fig)


def plot_commensurate_angles(
        data: np.ndarray,
        save: Optional[str] = None,
) -> np.ndarray:
    """
    Visualize commensurate angle distribution data.

    This function plots the distribution of commensurate angles with
    supercell size information.

    Args:
        data: Array with columns [theta(deg), count_of_solutions, estimated_supercell_size]
        save: Output figure path

    Returns:
        Input data array
    """
    theta = data[:, 0]
    count = data[:, 1]
    size_proxy = data[:, 2]
    lg_atom_num = np.log10(size_proxy)

    font_size = 32
    # plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = font_size
    plt.rcParams['figure.figsize'] = (8, 6)
    fig, ax = plt.subplots()
    ax.plot(theta, lg_atom_num)

    # ax.set_xlabel("Twist angle (degrees)")
    # ax.set_ylabel("lg N")

    fig.tight_layout()

    if save is not None:
        print(save)
        plt.savefig(save, dpi=200, bbox_inches='tight')

    plt.close(fig)

    return data


def write_band_file(evals: np.ndarray, k_dist: np.ndarray, filename: str = 'BAND.dat') -> None:
    """
    Write band structure data to file in BAND.txt format.

    Args:
        evals: Band energies with shape (nk, nbands)
        k_dist: k-point distances along path with shape (nk,)
        filename: Output filename
    """
    nk, nbands = evals.shape

    with open(filename, 'w') as f:
        # Write file header
        f.write("#K-Path(1/A) Energy-Level(eV)\n")
        f.write(f"# NKPTS & NBANDS:  {nk:3d}  {nbands:2d}\n")

        # Write each band separately
        for band_idx in range(nbands):
            f.write(f"# Band-Index    {band_idx + 1:2d}\n")

            # Write k-points and corresponding energies for this band
            for i in range(nk):
                f.write(f"   {k_dist[i]:10.5f}    {evals[i, band_idx]:16.6f}\n")

            # If k_dist is not monotonically increasing, repeat last point for closed path
            if k_dist[0] > k_dist[-1]:
                f.write(f"   {k_dist[-1]:10.5f}    {evals[-1, band_idx]:16.6f}\n")

def read_band_file(filename: str = "BAND.dat", tol: float = 1e-12) -> Tuple[np.ndarray, np.ndarray]:
    """
    Read band structure data from BAND.dat written by write_band_file().

    Expected format:
        #K-Path(1/A) Energy-Level(eV)
        # NKPTS & NBANDS:   nk  nbands
        # Band-Index     1
           k_dist   energy
           ...
        # Band-Index     2
           ...

    Parameters
    ----------
    filename : str
        Input filename (default: "BAND.dat").
    tol : float
        Tolerance for detecting a duplicated last k-point (default: 1e-12).

    Returns
    -------
    evals : np.ndarray
        Energies with shape (nk, nbands).
    k_dist : np.ndarray
        Distances along k-path with shape (nk,).

    Raises
    ------
    ValueError
        If the file format is inconsistent or cannot be parsed.
    """
    nk: Optional[int] = None
    nbands: Optional[int] = None

    # Temporary storage: list of per-band (k_list, e_list)
    band_k: List[List[float]] = []
    band_e: List[List[float]] = []

    current_band_index: Optional[int] = None

    def _ensure_band_storage(bidx: int) -> None:
        """Ensure band_k/band_e have slots up to bidx (0-based)."""
        while len(band_k) <= bidx:
            band_k.append([])
            band_e.append([])

    with open(filename, "r") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Parse nk/nbands line
                if "NKPTS" in line and "NBANDS" in line:
                    # Example: "# NKPTS & NBANDS:  100  8"
                    # Extract all ints in this line and take last two.
                    ints = [int(tok) for tok in line.replace(":", " ").replace("&", " ").split() if tok.isdigit()]
                    if len(ints) < 2:
                        raise ValueError(f"Failed to parse NKPTS/NBANDS from line: {raw_line!r}")
                    nk, nbands = ints[-2], ints[-1]

                # Parse band index line
                if "Band-Index" in line:
                    # Example: "# Band-Index    1"
                    # Take last int on the line as the band number (1-based).
                    tokens = line.replace("#", " ").replace("-", " ").split()
                    band_nums = [int(t) for t in tokens if t.isdigit()]
                    if not band_nums:
                        raise ValueError(f"Failed to parse Band-Index from line: {raw_line!r}")
                    bnum_1based = band_nums[-1]
                    current_band_index = bnum_1based - 1
                    _ensure_band_storage(current_band_index)
                continue

            # Data line: should be "k_dist energy"
            if current_band_index is None:
                raise ValueError(
                    f"Encountered data line before any '# Band-Index' header: {raw_line!r}"
                )

            parts = line.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid data line (need at least 2 columns): {raw_line!r}")

            try:
                k_val = float(parts[0])
                e_val = float(parts[1])
            except ValueError as exc:
                raise ValueError(f"Failed to parse floats from data line: {raw_line!r}") from exc

            band_k[current_band_index].append(k_val)
            band_e[current_band_index].append(e_val)

    if nk is None or nbands is None:
        raise ValueError("Missing '# NKPTS & NBANDS:' header; cannot determine nk/nbands.")

    if len(band_k) != nbands:
        raise ValueError(f"Expected {nbands} bands, but parsed {len(band_k)} band sections.")

    # Post-process each band: remove duplicated last point if present; check length.
    for b in range(nbands):
        if len(band_k[b]) < 2:
            raise ValueError(f"Band {b+1} has too few points: {len(band_k[b])}")

        # If last k equals previous k (within tol), drop the last row (common "repeat last point" pattern)
        if abs(band_k[b][-1] - band_k[b][-2]) <= tol and abs(band_e[b][-1] - band_e[b][-2]) <= 1e-6:
            band_k[b].pop()
            band_e[b].pop()

        if len(band_k[b]) != nk:
            raise ValueError(
                f"Band {b+1}: expected nk={nk} points, got {len(band_k[b])}. "
                f"File may be malformed or written with a different convention."
            )

    # Use k_dist from the first band and validate consistency across bands
    k_dist = np.array(band_k[0], dtype=float)
    for b in range(1, nbands):
        kb = np.array(band_k[b], dtype=float)
        if not np.allclose(kb, k_dist, rtol=0.0, atol=tol):
            raise ValueError(
                f"k_dist mismatch between band 1 and band {b+1}. "
                "This reader assumes the same k_dist for all bands."
            )

    evals = np.empty((nk, nbands), dtype=float)
    for b in range(nbands):
        evals[:, b] = np.array(band_e[b], dtype=float)

    return evals, k_dist


def _build_cli():
    """
    Build command-line interface parser.

    Returns:
        ArgumentParser for the CLI
    """
    import argparse

    p = argparse.ArgumentParser(description="Minimal CLI for twist_viz (bands / moiré points / comm-angles)")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Band structure plotting
    b = sub.add_parser("bands", help="Plot band structure from a pickled model")
    b.add_argument("model_pkl", type=str, help="Path to a pickled model exposing k_path & solve_all")
    b.add_argument("nk", type=int, help="Total number of k-points along the path")
    b.add_argument("path_npy", type=str, help="NumPy .npy file with k-path waypoints (M, d)")
    b.add_argument("--labels", type=str, nargs="*", default=None,
                   help="Tick labels for waypoints (e.g., G M K G)")
    b.add_argument("--ylim", type=float, nargs=2, default=None,
                   help="Energy window (ymin ymax)")
    b.add_argument("--ef", type=float, default=0.0,
                   help="Fermi level shift to subtract (eV/meV)")
    b.add_argument("--save", type=str, default=None,
                   help="Output figure path")

    # Moiré points plotting
    m = sub.add_parser("moire", help="Plot moiré lattice points from a pickled TB_structure")
    m.add_argument("structure_pkl", type=str,
                   help="Path to a pickled TB_structure object")
    m.add_argument("--annotate", action="store_true",
                   help="Annotate a subset of points")
    m.add_argument("--save", type=str, default=None,
                   help="Output figure path")

    # Commensurate angles plotting
    c = sub.add_parser("comm", help="Plot commensurate angle distribution using TB_structure methods")
    c.add_argument("structure_pkl", type=str,
                   help="Path to a pickled TB_structure object")
    c.add_argument("max_angle", type=float)
    c.add_argument("min_angle", type=float)
    c.add_argument("--lim", type=int, default=10)
    c.add_argument("--step", type=float, default=0.01)
    c.add_argument("--accurate", type=float, default=0.01)
    c.add_argument("--save", type=str, default=None)

    return p


def main(argv=None):
    """
    Command-line interface for quick testing with pickled objects.

    Power users are expected to import the functions directly.
    """
    import pickle
    import numpy as np

    p = _build_cli()
    args = p.parse_args(argv)

    if args.cmd == "bands":
        with open(args.model_pkl, "rb") as f:
            model = pickle.load(f)
        path = np.load(args.path_npy)
        plot_band(model, path, args.nk, labels=args.labels,
                  ylim=tuple(args.ylim) if args.ylim else None,
                  ef=args.ef, save=args.save)
    elif args.cmd == "moire":
        with open(args.structure_pkl, "rb") as f:
            S = pickle.load(f)
        plot_moire_points(S, annotate=args.annotate, save=args.save)
    elif args.cmd == "comm":
        with open(args.structure_pkl, "rb") as f:
            S = pickle.load(f)
        plot_commensurate_angles(S, args.max_angle, args.min_angle,
                                 lim=args.lim, step=args.step,
                                 accurate=args.accurate, save=args.save)


if __name__ == "__main__":
    main()