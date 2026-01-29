#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT-Clause
#
# Project: MoireStudio: A Universal Twisted Electronic Structure Calculation Package
# File: driver.py
# Version: 1.0.0
# Authors: Junxi Yu <junxiyu@bit.edu.cn>, Yichen Liu <liuyichen@bit.edu.cn>, Cheng-cheng Liu <ccliu@bit.edu.cn>
# Affiliation: Beijing Institute of Technology (BIT), Beijing, China
# Created: 2025-11-14
# Description:
#   CLI entry for running geometry (struc.*), tight-binding (tb.*),
#   and continuum k·p (kp.*) tasks with JSON inputs.
#
# How to cite:
#   Please cite:
#   1) https://link.aps.org/doi/10.1103/PhysRevB.111.075434
#   2) This CPC program article: [submitted/DOI placeholder]
#
# CPC Program Library identifier: [TBD]
# Repository: https://github.com/your-org/your-repo (placeholder)
# Issue tracker: https://github.com/your-org/your-repo/issues
#
# Python: >= 3.9
# Required deps: numpy, scipy, matplotlib
# Optional deps: MKL/BLAS (performance), wannier90 (I/O interface)
#
# Coordinate & unit conventions:
#   - Length in Å, energy in eV, angles in degrees.
#   - k-points given in fractional coordinates of the chosen reciprocal basis.
#   - Top/Bottom rotation: (+/-) θ/2 (top: -θ/2, bottom: +θ/2).
#   - Valley labels: "K", "Γ(Gamma)", "M".
#
# Parallelization & threads:
#   - Windows uses "spawn"; protect parallel entry with
#       if __name__ == "__main__": main()
#   - BLAS threads clamped via environment (OMP_NUM_THREADS, MKL_NUM_THREADS, etc.).
#
# Logging & exit codes:
#   - LOG level via env TWISTLAB_LOG_LEVEL (DEBUG/INFO/WARN/ERROR).
#   - Exit codes: 0=OK; 2=bad input; 3=runtime error; 4=I/O error.
#
# CLI usage:
#   python driver.py --input input.json
#   python -m package.driver --input input.json
#
# Outputs (typical):
#   outputs/band.txt, k_vec.txt, k_dist.txt, k_node.txt, *.png
#
# Reproducibility:
#   - Deterministic diagonalization where applicable.
#   - Record software/env versions in outputs/metadata.json.
#
# References:
#   - [1] J. Yu, S. Qian, and C.-C. Liu, General electronic structure calculation method for twisted systems,
#         Phys. Rev. B 111, 075434 (2025).
#   - [2] arXiv:2509.13114 [cond-mat]
#   - [3] CPC author guidelines (for structure) (placeholder)

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import textwrap
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Local imports
from .kp_parameter import gen_TBG_parameter, gen_tTMD_parameter
from .read_tb_model import (
    devide2mono,
    read_fermi_energy,
    read_mono,
    read_POSCAR,
)
from .solver import solve_all, solve_all_parallel, solve_low_energy_streaming_parallel
from .tb_parameter import gen_tb_parameter
from .twist_geometry import TwistGeometry
from .twist_kp import TwistKP
from .twist_relaxation import TwistRelaxGeometry, TwistRelaxKP
from .twist_tb import TwistTB, build_ham_from_npz
from .twist_viz import (
    plot_band as viz_plot_band,
    plot_commensurate_angles,
    plot_moire_points,
    write_band_file,
)

_VIZ_OK = True

# Parallelization setup for Windows
plat_name = sys.platform
if plat_name == "linux":
    mp_start_de = None
else:
    mp_start_de = "spawn"

__VERSION__ = "1.0.0"  # Keep in sync with header
_PRB_DOI = "10.1103/PhysRevB.111.075434"
_CPC_DOI = "TBD"

_ASCII = r"""
  __  __       _             ____    _             _ _      
 |  \/  | ___ (_) _ __ ___  / ___| _| |_ _   _  __| (_) ___  
 | |\/| |/ _ \| || '__/ _ \ \___ \ _  __| | | |/ _` | |/ _ \ 
 | |  | | (_) | || | |  __/  ___) | | |_| |_| | (_| | | (_) |
 |_|  |_|\___/|_||_|  \___| |____/   \__|\__,_|\__,_|_|\___/ 
                                                       1.0.0
"""


# ============================================================================
# Utility functions
# ============================================================================
def _supports_color(no_color_flag: bool = False) -> bool:
    """
    Check if the terminal supports ANSI color codes.

    Args:
        no_color_flag: If True, color is disabled regardless of terminal.

    Returns:
        True if color is supported and should be used.
    """
    if no_color_flag:
        return False
    try:
        return sys.stdout.isatty() and os.environ.get("TERM", "") not in ("", "dumb")
    except Exception:
        return False


def _c(s: str, code: str, enable: bool) -> str:
    """
    Wrap a string with ANSI color codes if enabled.

    Args:
        s: String to colorize.
        code: ANSI color code (e.g., "36;1").
        enable: Whether to apply color.

    Returns:
        Colorized string if enabled, otherwise original string.
    """
    return f"\033[{code}m{s}\033[0m" if enable else s


def _detect_blas_backend() -> str:
    """
    Detect the BLAS/LAPACK backend used by NumPy.

    Returns:
        String describing the backend (MKL, OpenBLAS, or Unknown).
    """
    try:
        info = np.__config__.get_info("lapack_opt_info")
        libs = info.get("libraries", []) if isinstance(info, dict) else []
        libs_str = " ".join(libs).lower()
        if "mkl" in libs_str:
            return "MKL (lapack_opt)"
        if "openblas" in libs_str:
            return "OpenBLAS (lapack_opt)"
        # fallback: try blas_opt_info
        info2 = np.__config__.get_info("blas_opt_info")
        libs2 = info2.get("libraries", []) if isinstance(info2, dict) else []
        libs2_str = " ".join(libs2).lower()
        if "mkl" in libs2_str:
            return "MKL (blas_opt)"
        if "openblas" in libs2_str:
            return "OpenBLAS (blas_opt)"
    except Exception:
        pass
    return "Unknown"


def _git_short_hash() -> str | None:
    """
    Get the short Git commit hash of the current repository (best-effort).

    Returns:
        Short Git hash string, or None if not available.
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return None


def _sha256_file(path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        path: Path to the file.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _print_banner(cfg: "InputConfig", in_path: Path, args) -> dict:
    """
    Print the program banner, summary, and environment information.

    Args:
        cfg: Input configuration object.
        in_path: Path to input JSON file.
        args: Command-line arguments.

    Returns:
        Dictionary containing metadata about the run.
    """
    color = _supports_color(getattr(args, "no_color", False))
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{random.randint(0, 0xFFF):03x}"
    git = _git_short_hash()
    blas = _detect_blas_backend()
    pyver = platform.python_version()
    npver = np.__version__
    try:
        import scipy

        spver = scipy.__version__
    except Exception:
        spver = "not-installed"

    # Environment threads
    env_threads = {
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
        "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
    }

    sha256 = _sha256_file(in_path) if in_path.exists() else "N/A"
    mode = cfg.mode
    task = cfg.task
    nk = None
    try:
        if mode == "tb":
            _, nk = cfg.tb_k_path()
        elif mode == "kp":
            _, nk = cfg.kp_path()
    except Exception:
        nk = None

    # Print banner
    if not getattr(args, "quiet", False):
        print(_c(_ASCII, "36;1", color))
        title = f"MoireStudio v{__VERSION__}  |  Run ID: {run_id}"
        if git:
            title += f"  |  git:{git}"
        print(_c(title, "33;1", color))

        # Summary
        print(_c("== Task Summary ==", "32;1", color))
        print(f"  Mode/Task     : {mode}.{task}")
        print(f"  Input JSON    : {in_path.resolve()}")
        print(f"  Output Dir    : {cfg.output_dir.resolve()}")
        if nk is not None:
            print(f"  k-sampling    : nk = {nk}")
        if mode == "tb":
            print(f"  TB cores      : {cfg.tb_num_core()}    sparse: {cfg.tb_sparse()}")
            print(f"  theta_deg     : {cfg.theta_deg:.6g}")
        elif mode == "kp":
            Vz, mz = cfg.kp_Vz_mz()
            print(
                f"  kp.tr         : {cfg.kp_tr()}    valley: {cfg.kp_valley_name()}    Vz/mz: {Vz}/{mz}"
            )
            print(f"  theta_deg     : {cfg.theta_deg:.6g}")
            irelax, order_num, kappa_parallel, kappa_perp = cfg.relax_para()
            if irelax:
                print(f"  relax         : on")
            else:
                print(f"  relax         : off")

        # Environment
        print(_c("== Environment ==", "32;1", color))
        print(f"  Python/NumPy/SciPy : {pyver} / {npver} / {spver}")
        print(f"  BLAS/LAPACK        : {blas}")
        print(f"  Platform/CPU cores : {platform.platform()} / {os.cpu_count()}")
        print(f"  Threads (env)      : {env_threads}")
        print(f"  input.json sha256  : {sha256}")

        # Citation
        print(_c("== Citation ==", "32;1", color))
        print(f"  PRB: doi:{_PRB_DOI}")
        print(f"  CPC: doi:{_CPC_DOI} (to appear)")

        # Reproducible command
        print(_c("== Reproducibility ==", "32;1", color))
        cmd = f"python {Path(sys.argv[0]).name} --input {in_path.name}"
        if getattr(args, "quiet", False):
            cmd += " --quiet"
        if getattr(args, "no_color", False):
            cmd += " --no-color"
        print(f"  Re-run: {cmd}")
        print()

    return {
        "run_id": run_id,
        "git": git,
        "blas": blas,
        "python": pyver,
        "numpy": npver,
        "scipy": spver,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "threads_env": {k: (v if v is not None else "") for k, v in env_threads.items()},
        "input_sha256": sha256,
        "mode": mode,
        "task": task,
        "nk": nk,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "version": __VERSION__,
        "prb_doi": _PRB_DOI,
        "cpc_doi": _CPC_DOI,
    }


def _write_metadata(cfg: "InputConfig", in_path: Path, meta: dict) -> None:
    """
    Write metadata about the run to a JSON file.

    Args:
        cfg: Input configuration object.
        in_path: Path to input JSON file.
        meta: Metadata dictionary from _print_banner.
    """
    try:
        out = cfg.output_dir / "metadata.json"
        payload = {
            "run": meta,
            "paths": {
                "input": str(in_path.resolve()),
                "output_dir": str(cfg.output_dir.resolve()),
            },
        }
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"[meta] wrote {out}")
    except Exception as e:
        print(f"[meta] skipped ({e})")


def _to_complex(x: Any) -> complex:
    """
    Parse a JSON scalar or [re, im] list into a complex number.

    Args:
        x: Input value (scalar, list of two numbers, or single‑element list).

    Returns:
        Corresponding complex number.

    Raises:
        ValueError: If the input format is invalid.
    """
    if isinstance(x, (int, float)):
        return complex(float(x), 0.0)
    if isinstance(x, list):
        if len(x) == 2 and all(isinstance(v, (int, float)) for v in x):
            re, im = x
            return complex(float(re), float(im))
        # Allow single-item list [a] as a real scalar
        if len(x) == 1 and isinstance(x[0], (int, float)):
            return complex(float(x[0]), 0.0)
    raise ValueError(f"Invalid complex literal: {x}")


def _to_matrix(mat: Any) -> np.ndarray:
    """
    Convert nested JSON array of numbers or [re,im] pairs into a complex numpy array.

    Rules:
        - scalar or [re,im] -> shape (1,1)
        - 1D list of scalars/complex tokens -> shape (N,1)
        - 2D list -> shape (N,M)

    Args:
        mat: Input JSON‑like matrix representation.

    Returns:
        2D complex numpy array.

    Raises:
        ValueError: If the input is not a scalar, 1D, or 2D structure.
    """
    # scalar or complex pair
    if isinstance(mat, (int, float)) or (
        isinstance(mat, list)
        and (len(mat) == 2 and all(isinstance(v, (int, float)) for v in mat))
    ):
        return np.array([[_to_complex(mat)]], dtype=complex)
    arr = np.asarray(mat, dtype=object)
    if arr.ndim == 1:
        out = np.array([[_to_complex(v)] for v in arr.tolist()], dtype=complex)
        return out
    if arr.ndim == 2:
        out = np.zeros(arr.shape, dtype=complex)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                out[i, j] = _to_complex(arr[i, j])
        return out
    raise ValueError("Matrix literal must be scalar, 1D, or 2D.")


def _to_array2(a: Any, dtype=float) -> np.ndarray:
    """
    Force a JSON‑like array to be a 2D numpy array.

    Args:
        a: Input array‑like data.
        dtype: Data type for the resulting array.

    Returns:
        2D numpy array.
    """
    arr = np.array(a, dtype=dtype)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr


def _ensure_dir(p: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        p: Directory path.

    Returns:
        Path object of the directory.
    """
    pth = Path(p)
    pth.mkdir(parents=True, exist_ok=True)
    return pth


def _amp_pha_2_coe(amps, phas) -> np.ndarray:
    """
    Convert amplitudes and phases (in degrees) to complex coefficients.

    Args:
        amps: Array of amplitudes.
        phas: Array of phases in degrees.

    Returns:
        Array of complex coefficients.
    """
    phas = np.deg2rad(phas)
    coes = np.array(amps) * np.exp(1.0j * phas)
    return coes


# ============================================================================
# Input configuration class
# ============================================================================
class InputConfig:
    """Light‑weight reader/validator for input.json."""

    def __init__(self, d: Dict[str, Any]) -> None:
        """
        Initialize configuration from parsed JSON dictionary.

        Args:
            d: Dictionary parsed from input.json.

        Raises:
            ValueError: If required fields are missing.
        """
        self.raw = d
        # Required
        self.task: str = d.get("task", "").strip()
        self.mode: str = d.get("mode", "struc").strip()
        if not self.task:
            raise ValueError(
                "`task` is required in input.json (e.g., 'kp.band', 'kp.chern', 'struc.find_com', 'tb.band')."
            )

        # IO
        self.io: Dict[str, Any] = d.get("io", {})
        self.output_dir: Path = _ensure_dir(self.io.get("output_dir", "./outputs"))
        self.input_dir: str = self.io.get("input_dir", "./inputs")
        # Backward compatibility
        self.figure: str = self.io.get("figure", f"{self.task}.pdf")
        # New explicit figure names
        self.fig_band: str = self.io.get("fig_band", self.figure)
        self.fig_moire: str = self.io.get("fig_moire", "moire_points.pdf")
        self.show_plots: bool = bool(self.io.get("show_plots", False))

        self.theta_deg = d.get("theta_deg", 21.79)

        # Blocks
        self.kp: Dict[str, Any] = d.get("kp", {})
        self.tb: Dict[str, Any] = d.get("tb", {})
        self.struc: Dict[str, Any] = d.get("struc", {})
        self.relax: Dict[str, Any] = d.get("relax", {})

    # --- KP methods ---
    def kp_tr(self) -> int:
        """Return the truncation radius for k·p coupling."""
        return int(self.kp.get("tr", 3))

    def kp_valley_pos(self) -> np.ndarray:
        """Return the fractional coordinates of the valley point."""
        return np.array(self.kp.get("valley_pos", [2 / 3, 1 / 3]), dtype=float)

    def kp_mono_lat(self) -> np.ndarray:
        """Return the 2×2 monolayer lattice vectors (in Å)."""
        out = _to_array2(
            self.kp.get(
                "mono_lat",
                [[2.46, 0.0], [2.46 * 0.5, 2.46 * np.sqrt(3) / 2]],
            ),
            dtype=float,
        )
        if out.shape != (2, 2):
            raise ValueError("kp.mono_lat must be 2x2.")
        return out

    def kp_valley_name(self) -> str:
        """Return the valley name (e.g., 'K', 'Gamma', 'M')."""
        return str(self.kp.get("valley_name", "K"))

    def kp_mass(self) -> Optional[List[float]]:
        """Return the effective mass [mx, my] if specified, else None."""
        m = self.kp.get("mass", None)
        if m is None:
            return None
        if len(m) != 2:
            raise ValueError("kp.mass must be [mx, my].")
        return [float(m[0]), float(m[1])]

    def kp_hv_a(self) -> Optional[float]:
        """Return the Dirac velocity (ħv/a) if specified, else None."""
        hv = self.kp.get("hv_a", None)
        return float(hv) if hv is not None else None

    def kp_Vz_mz(self) -> Tuple[float, float]:
        """Return the out‑of‑plane electric field (Vz) and exchange field (mz)."""
        Vz = float(self.kp.get("V_z", 0.0))
        mz = float(self.kp.get("m_z", 0.0))
        return Vz, mz

    def kp_couplings(
        self,
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """Extract all coupling matrices (inter‑ and intra‑layer)."""
        inter_idxs = np.array(self.kp.get("inter_idxs", []))
        inter_amps = np.array(self.kp.get("inter_amps", []))
        inter_phas = np.array(self.kp.get("inter_phas", []))
        inter_coes = _amp_pha_2_coe(inter_amps, inter_phas)

        intra_t_idxs = np.array(self.kp.get("intra_t_idxs", []))
        intra_t_amps = np.array(self.kp.get("intra_t_amps", []))
        intra_t_phas = np.array(self.kp.get("intra_t_phas", []))
        intra_t_coes = _amp_pha_2_coe(intra_t_amps, intra_t_phas)

        intra_b_idxs = np.array(self.kp.get("intra_b_idxs", []))
        intra_b_amps = np.array(self.kp.get("intra_b_amps", []))
        intra_b_phas = np.array(self.kp.get("intra_b_phas", []))
        intra_b_coes = _amp_pha_2_coe(intra_b_amps, intra_b_phas)

        return (
            inter_idxs,
            intra_t_idxs,
            intra_b_idxs,
            inter_coes,
            intra_t_coes,
            intra_b_coes,
        )

    def kp_path(self) -> Tuple[np.ndarray, int]:
        """Return the k‑path (2D array) and number of k‑points."""
        path = _to_array2(self.kp.get("k_path", []), dtype=float)
        nk = int(self.kp.get("nk", 121))
        return path, nk

    def kp_band_plot(self) -> Tuple[Optional[List[str]], Optional[List[float]]]:
        """Return band plot labels and y‑axis limits."""
        labels = self.kp.get("labels", None)
        ylim = self.kp.get("ylim", None)
        return labels, ylim

    def kp_chern(self) -> Tuple[int, int]:
        """Return parameters for Chern number calculation: mesh size and band index."""
        n = int(self.kp.get("n_mesh", 25))
        band_index = self.kp.get("band_index", 1)
        return n, band_index

    def kp_shift(self):
        """Return Fermi energy shift (float or 'max'/'min')."""
        fermi_shift = self.kp.get("fermi_shift", 0)
        return fermi_shift

    def kp_system_name(self):
        """Return the k·p system name (e.g., 'tTMD', 'TBG')."""
        system_name = self.kp.get("system_name", None)
        return system_name

    def kp_lat_a(self):
        """Return the monolayer lattice constant (in Å)."""
        lat_a = self.kp.get("lat_a", 2.46)
        return lat_a

    def kp_valley_idx(self):
        """Return the valley index (1 for K, 2 for K')."""
        valley_idx = self.kp.get("valley_idx", 1)
        return valley_idx

    def kp_tmd_para(self):
        """Return tTMD parameters: omega, V, psi."""
        omega = self.kp.get("omega", -8.5)
        V = self.kp.get("V", 8)
        psi = self.kp.get("psi", -90)
        return omega, V, psi

    def kp_tbg_para(self):
        """Return TBG parameters: u1, u2."""
        u1 = self.kp.get("u1", 90)
        u2 = self.kp.get("u2", 90)
        return u1, u2

    def relax_para(self) -> Tuple[bool, int, float, float]:
        """Return relaxation parameters: whether to relax, order number, and κ∥."""
        irelax = self.relax.get("irelax", False)
        order_num = self.relax.get("order_num", 0)
        kappa_parallel = self.relax.get("kappa_parallel", 0)
        kappa_perp = self.relax.get("kappa_perp", 0)
        return irelax, order_num, kappa_parallel, kappa_perp

    def relax_u_idxs(self):
        u_in_idxs = self.relax.get("u_in_idxs", None)
        u_out_idxs = self.relax.get("u_out_idxs", None)
        return u_in_idxs, u_out_idxs

    # --- IO methods ---
    def io_in_dir(self) -> str:
        """Return the input directory."""
        return self.input_dir

    def io_out_dir(self) -> Path:
        """Return the output directory as a Path."""
        return self.output_dir

    def bilayer_struc_num(self) -> int:
        """Return the number of bilayer structures (for TB)."""
        return int(self.struc.get("bilayer_num", 1))

    def io_in_pos(self) -> Tuple[str, str]:
        """Return path and prefix for POSCAR‑like files."""
        pos_path = self.struc.get("pos_path", self.input_dir)
        pos_prefix = self.struc.get("pos_prefix", "POSCAR")
        return pos_path, pos_prefix

    def io_in_type(self) -> Tuple[str, str, bool]:
        """Return read mode, layer type, and heterostructure flag."""
        read_mode = self.struc.get("read_mode", "POSCAR")
        read_layer = self.struc.get("read_layer", "bilayer")
        ihetero = self.struc.get("ihetero", False)
        return read_mode, read_layer, ihetero

    def io_in_model_hetero(self) -> Tuple[str, str, str, float, float]:
        """Return parameters for reading heterostructure TB models."""
        t_pref = self.io.get("t_prefix", "t_wannier90")
        t_ef = self.io.get("t_fermi_energy", 0)
        b_pref = self.io.get("b_prefix", "b_wannier90")
        b_ef = self.io.get("b_fermi_energy", 0)
        return self.input_dir, str(t_pref), str(b_pref), float(t_ef), float(b_ef)

    def io_in_pos_hetero(self) -> Tuple[str, str, str]:
        """Return parameters for reading heterostructure POSCAR files."""
        t_pref = self.io.get("t_prefix", "t_POSCAR")
        b_pref = self.io.get("b_prefix", "b_POSCAR")
        return self.input_dir, str(t_pref), str(b_pref)

    def io_in_w90(self) -> Tuple[str, str, Optional[float]]:
        """Return parameters for reading Wannier90 data."""
        pref = self.tb.get("wannier", {}).get("prefix", "wannier90")
        ef = self.tb.get("wannier", {}).get("fermi_energy", None)
        if ef is None:
            efpath = Path(self.input_dir + "/FERMI_ENERGY")
            ief = efpath.exists()
            if ief:
                ef = read_fermi_energy(efpath)
            else:
                ef = 0
        return self.input_dir, str(pref), float(ef)

    def struc_interlayer_distance_ids(self) -> Tuple[float, float]:
        """Return AA and AB interlayer distances (in Å)."""
        d_0 = float(self.struc.get("d_0", 3.5))
        dAA = self.struc.get("d_AA", None)
        dAB = self.struc.get("d_AB", None)
        if dAA == None:
            dAA, dAB = d_0, d_0
        return dAA, dAB

    def struc_params(self) -> Dict[str, Any]:
        """Return a dictionary of structural generation parameters."""
        irelax, order_num, kappa_parallel, kappa_perp = self.relax_para()
        if irelax:
            iLmfromG = True
        else:
            iLmfromG = bool(self.struc.get("iLmfromG", False))
        return {
            "zero_point": self.struc.get("zero_point", [0, 0]),
            "lim": int(self.struc.get("lim", 20)),
            "search": int(self.struc.get("search", 0)),
            "accurate": float(self.struc.get("accurate", 0.01)),
            "iLmfromG": iLmfromG,
            "if_gen_pos": bool(self.struc.get("if_gen_pos", True)),
            "write_by_hand": self.struc.get("write_by_hand", None),
            "if_plot": bool(self.struc.get("if_plot", False)),
        }

    def struc_find(self) -> Tuple[float, float, int, float, float]:
        """Return parameters for commensurate angle search."""
        max_angle = float(self.struc.get("max_angle", 180))
        min_angle = float(self.struc.get("min_angle", 1))
        lim = int(self.struc.get("lim", 10))
        step = float(self.struc.get("step", 0.01))
        accurate = float(self.struc.get("accurate", 0.01))
        return max_angle, min_angle, lim, step, accurate

    def tb_num_core(self) -> int:
        """Return the number of CPU cores for TB calculations."""
        return int(self.tb.get("cores", 1))

    def tb_sparse(self) -> bool:
        """Return whether to use sparse matrix diagonalization for TB."""
        return bool(self.tb.get("isparse", False))

    def tb_k_path(self) -> Tuple[np.ndarray, int]:
        """Return the TB k‑path and number of k‑points."""
        path = _to_array2(
            self.tb.get("k_path", [[0, 0], [0.5, 0], [1 / 3, 1 / 3], [0, 0]]),
            dtype=float,
        )
        nk = int(self.tb.get("nk", 121))
        return path, nk

    def tb_band_plot(self) -> Tuple[Optional[List[str]], Optional[List[float]]]:
        """Return TB band plot labels and y‑axis limits."""
        labels = self.tb.get("labels", None)
        ylim = self.tb.get("ylim", None)
        return labels, ylim

    def tb_inter_layer_data(self) -> float:
        """Return the inter‑layer coupling scaling factor."""
        inter_coe = self.tb.get("inter_coe", 1)
        return inter_coe

    def tb_out_wannier(self) -> bool:
        """Return the ioutwannier (return twisted wannier model or not)"""
        ioutwannier = self.tb.get("ioutwannier", False)
        return ioutwannier

    def tb_isymmetry(self) -> bool:
        isymmetry = self.tb.get("isymmetry", False)
        return isymmetry

# ============================================================================
# Task runners
# ============================================================================
def read_tb_data(cfg: InputConfig):
    """
    Read tight‑binding data according to the configuration.

    Args:
        cfg: Input configuration.

    Returns:
        Tuple of (mono_t, mono_b, h0, d0, r0) where:
            mono_t: Top monolayer model.
            mono_b: Bottom monolayer model.
            h0, d0, r0: Inter‑layer coupling matrices (complex, real, real).
    """
    read_mode, read_layer, ihetero = cfg.io_in_type()
    if ihetero:
        if read_mode == "POSCAR":
            path, t_pref, b_pref = cfg.io_in_pos_hetero()
            mono_t = read_POSCAR(path, t_pref, ifmodel=True)
            mono_b = read_POSCAR(path, b_pref, ifmodel=True)
            h0, d0, r0 = None, None, None
        else:
            path, t_pref, b_pref, t_ef, b_ef = cfg.io_in_model_hetero()
            mono_t = read_mono(path, t_pref, t_ef)
            mono_b = read_mono(path, b_pref, b_ef)
            h0, d0, r0 = None, None, None
    else:
        if read_mode == "POSCAR":
            pos_path, pos_prefix = cfg.io_in_pos()
            if read_layer == "bilayer":
                bilayer_model = read_POSCAR(pos_path, pos_prefix, ifmodel=True)
                mono_t, mono_b, h0, d0 = devide2mono(bilayer_model)
                r0 = None
            else:
                mono_model = read_POSCAR(pos_path, pos_prefix, ifmodel=True)
                mono_t, mono_b = mono_model, mono_model
                h0, d0, r0 = None, None, None
        else:
            (wpath, wpref, ef_opt) = cfg.io_in_w90()
            bilayer_num = cfg.bilayer_struc_num()
            input_dir = cfg.input_dir
            if read_layer == "bilayer":
                mono_t, mono_b, h0, d0, r0 = gen_tb_parameter(
                    bilayer_num, input_dir, wpref
                )
            else:
                mono_model = read_mono(wpath, wpref, fermi_energy=ef_opt)
                mono_t, mono_b = mono_model, mono_model
                h0, d0, r0 = None, None, None
    if np.all(h0) is None:
        t_orb_num = len(mono_t._orb)
        b_orb_num = len(mono_b._orb)
        h0 = np.zeros((t_orb_num, b_orb_num), dtype=complex)
        d0 = np.zeros((t_orb_num, b_orb_num), dtype=float)
    return mono_t, mono_b, h0, d0, r0


def gen_struc_model(cfg: InputConfig):
    """
    Generate a TwistGeometry object from the configuration.

    Args:
        cfg: Input configuration.

    Returns:
        TwistGeometry object.
    """
    theta = cfg.theta_deg
    mono_t, mono_b, _, _, _ = read_tb_data(cfg)
    dAA, dAB = cfg.struc_interlayer_distance_ids()
    inter_ids = (dAA, dAB)

    tb_struct = TwistGeometry(
        theta_360=theta,
        mono_t_model=mono_t,
        mono_b_model=mono_b,
        inter_ids=inter_ids,
    )

    return tb_struct


def gen_pos(tb_struct, cfg: InputConfig):
    """
    Generate the moiré structure and optionally relax it, then save POSCAR.

    Args:
        tb_struct: TwistGeometry object.
        cfg: Input configuration.
    """
    theta_deg = cfg.theta_deg
    irelax, order_num, kappa_parallel, kappa_perp = cfg.relax_para()

    Lm, moire_points, atom_index = tb_struct.gen_structure(**cfg.struc_params())

    print(
        "[struc] lattice vector of twisted structure:\n",
        Lm
    )

    if irelax:

        # twist_relax = TwistRelaxGeometry(tb_struct)
        # u_idxs, u_coes_t, u_coes_b = twist_relax.gen_relax_pattern(
        #     theta_deg, kappa_parallel
        # )


        u_in_idxs, u_out_idxs = cfg.relax_u_idxs()
        twist_relax = TwistRelaxGeometry(tb_struct, u_in_idxs=u_in_idxs, u_out_idxs=u_out_idxs)
        u_in_idxs, u_in_coes_t, u_in_coes_b = twist_relax.gen_relax_pattern_in_plane(
            theta_deg, kappa_parallel
        )
        u_out_idxs, u_out_coes_t, u_out_coes_b = twist_relax.gen_relax_pattern_out_plane(
            theta_deg, kappa_perp
        )


        relaxed_points = twist_relax.gen_relaxed_struc(moire_points)
        prefix = str(np.round(theta_deg, 2)) + "_relaxed"
        tb_struct._moire_points = relaxed_points
        tb_struct.gen_POSCAR(relaxed_points, prefix)



    # Save POSCAR if generated
    poscar = Path("POSCAR")
    if poscar.exists():
        target = cfg.output_dir / "POSCAR"
        target.write_bytes(poscar.read_bytes())
        print(f"[TwistGeometry] POSCAR written to: {target.resolve()}")

    # Visualization: moiré points
    if _VIZ_OK:
        try:
            fig_path = cfg.output_dir / cfg.fig_moire
            plot_moire_points(
                tb_struct, annotate=False, save=str(fig_path), show=cfg.show_plots
            )
            print(f"[viz] moiré points saved to {fig_path}")
        except Exception as e:
            print(f"[viz] moiré plotting skipped due to error: {e}")
    else:
        print("[viz] twist_viz not found; skip moiré plot.")


def find_com(tb_struct, cfg: InputConfig):
    """
    Find commensurate twist angles and save results.

    Args:
        tb_struct: TwistGeometry object.
        cfg: Input configuration.
    """
    print("find_com")
    max_angle, min_angle, lim, step, accurate = cfg.struc_find()
    data = tb_struct.find_commensurate_angle(
        max_angle, min_angle, lim=lim, step=step, accurate=accurate
    )
    out_txt = cfg.output_dir / "commensurate_angle.txt"
    np.savetxt(out_txt, data, fmt="%.8f")
    print(f"[struc.find_com] Saved: {out_txt}")

    # Visualization
    if _VIZ_OK:
        try:
            fig_path = str(cfg.output_dir) + "/" + "comm_angles.pdf"
            plot_commensurate_angles(data, save=fig_path)
            print(f"[viz] commensurate-angle plot saved to {fig_path}")
        except Exception as e:
            print(f"[viz] commensurate-angle plotting skipped due to error: {e}")
    else:
        print("[viz] twist_viz not found; skip commensurate-angle plot.")


def gen_tb_model(cfg: InputConfig):
    """
    Generate a TwistTB model from the configuration.

    Args:
        cfg: Input configuration.

    Returns:
        TwistTB object.
    """
    theta = cfg.theta_deg
    mono_t, mono_b, h0, d0, r0 = read_tb_data(cfg)

    isymmetry = cfg.tb_isymmetry()
    if isymmetry:
        d0 = (d0 * 0) + np.min(d0)
        r0 = (r0 * 0) + np.min(r0)

    inter_coe = cfg.tb_inter_layer_data()
    h0 = inter_coe * h0
    tmstruc = gen_struc_model(cfg)
    gen_pos(tmstruc, cfg)
    tm = TwistTB(
        theta_360=theta,
        mono_t_model=mono_t,
        mono_b_model=mono_b,
        TB_structure=tmstruc,
        h0=h0,
        d0=d0,
        r0=r0,
    )
    # Build real-space Hamiltonian if desired later; we defer to band task

    num_core = cfg.tb_num_core()
    isparse = cfg.tb_sparse()

    if num_core > 1:
        if isparse:
            twist_ham_sparse = tm.gen_r_ham_sparse_parallel(
                num_processes=num_core, mp_start=mp_start_de
            )
        else:
            twist_ham = tm.gen_r_ham_mulp(num_core)
    else:
        twist_ham = tm.gen_r_ham()
        # save_ham_path = cfg.output_dir / Path("twist_ham.npy")
        # np.save(save_ham_path, twist_ham)

    ioutwannier = cfg.tb_out_wannier()
    if ioutwannier:
        if isparse:
            raise Exception(
                "Error, in the case of sparse matrices,the generated wannier_hr.dat will become extremely large"
                            )
        tm.change_to_pythtb()
        tm.output(path=str(cfg.output_dir), prefix="wannier90", isparse=isparse)

    return tm


def gen_tb_band(tm, cfg: InputConfig) -> None:
    """
    Compute and save tight‑binding band structure.

    Args:
        tm: TwistTB object.
        cfg: Input configuration.
    """
    # Prepare k‑path
    path, nk = cfg.tb_k_path()
    k_vec, k_dist, k_node = tm.k_path(path, nk)
    np.savetxt(cfg.output_dir / "k_vec.txt", k_vec)
    np.savetxt(cfg.output_dir / "k_dist.txt", k_dist)
    np.savetxt(cfg.output_dir / "k_node.txt", k_node)

    # np.save("twist_ham.npy", tm._twist_ham)

    # Build H(k) and solve bands
    num_core = cfg.tb_num_core()
    isparse = cfg.tb_sparse()

    # Prefer direct k‑H build (usually faster than streaming unless huge)
    if num_core > 1:
        if isparse:
            # Fallback: streaming sparse blocks if available
            print(f"[tb.band] trying sparse streaming...")
            _ = tm.export_sparse_blocks(out_dir="./twist_blocks")
            builder = partial(build_ham_from_npz, npz_dir="./twist_blocks")
            k_list = k_vec.tolist()
            evals = solve_low_energy_streaming_parallel(
                k_list=k_list,
                build_ham_at_k=builder,
                num_eigs=40,
                eigvecs=False,
                core_num=max(1, num_core),
                sigma=0.0,
                tol=1e-8,
                mp_start=mp_start_de,
            )
        else:
            ham_k = tm.gen_all_k_ham(k_vec)
            evals = solve_all_parallel(
                ham_k,
                eig=False,
                core_num=num_core,
                backend="process",
                blas_threads=1,
                mp_start=mp_start_de,
            )
            file_name = str(cfg.output_dir) + "/" + "BAND.dat"
            write_band_file(evals, k_dist, filename=file_name)
    else:
        ham_k = tm.gen_all_k_ham(k_vec)
        evals = solve_all(ham_k)
        file_name = str(cfg.output_dir) + "/" + "BAND.dat"
        write_band_file(evals, k_dist, filename=file_name)

    np.savetxt(cfg.output_dir / "band.txt", evals)
    print(f"[tb.band] Saved bands to {cfg.output_dir/'band.txt'}")

    # Visualization
    labels, ylim = cfg.tb_band_plot()
    with open(str(cfg.output_dir) + "/k_labels.txt", "w", encoding="utf-8") as f:
        f.write(str(labels))
    if _VIZ_OK:
        try:
            fig_path = cfg.output_dir / cfg.fig_band
            viz_plot_band(
                ylim=tuple(ylim) if ylim else None,
                ef=0.0,
                load=str(cfg.output_dir),
                save=str(fig_path),
                show=cfg.show_plots,
                color="k",
                isparse=isparse,
            )
            print(f"[viz] TB band figure saved to {fig_path}")
        except Exception as e:
            print(f"[viz] TB band plotting skipped due to error: {e}")
    else:
        print("[viz] twist_viz not found; skip TB band plot.")


def gen_kp_model(cfg: InputConfig):
    """
    Generate a TwistKP model from the configuration.

    Args:
        cfg: Input configuration.

    Returns:
        TwistKP object.
    """
    theta = cfg.theta_deg
    tr = cfg.kp_tr()
    Vz, mz = cfg.kp_Vz_mz()
    system_name = cfg.kp_system_name()

    if system_name == "tTMD":
        lat_a = cfg.kp_lat_a()
        valley_idx = cfg.kp_valley_idx()
        omega, V, psi = cfg.kp_tmd_para()
        (
            mono_lat,
            valley_pos,
            valley_name,
            inter_idxs,
            intra_t_idxs,
            intra_b_idxs,
            inter_coes,
            intra_t_coes,
            intra_b_coes,
        ) = gen_tTMD_parameter(lat_a, valley_idx, omega, V, psi)

    elif system_name == "TBG":
        lat_a = cfg.kp_lat_a()
        valley_idx = cfg.kp_valley_idx()
        u_1, u_2 = cfg.kp_tbg_para()
        (
            mono_lat,
            valley_pos,
            valley_name,
            inter_idxs,
            intra_t_idxs,
            intra_b_idxs,
            inter_coes,
            intra_t_coes,
            intra_b_coes,
        ) = gen_TBG_parameter(lat_a, valley_idx, u_1, u_2)
    else:
        valley_pos = cfg.kp_valley_pos()
        mono_lat = cfg.kp_mono_lat()
        (
            inter_idxs,
            intra_t_idxs,
            intra_b_idxs,
            inter_coes,
            intra_t_coes,
            intra_b_coes,
        ) = cfg.kp_couplings()

    model_kwargs = dict(
        theta_360=theta,
        tr=tr,
        valley_pos=valley_pos,
        mono_lat=mono_lat,
        V_z=Vz,
        m_z=mz,
    )
    mass = cfg.kp_mass()
    hv_a = cfg.kp_hv_a()
    if (mass is None) == (hv_a is None):
        raise ValueError(
            "For KP model, specify EITHER `kp.mass` OR `kp.hv_a` (not both)."
        )
    if mass is not None:
        model_kwargs["mass"] = mass
        band_num = 1
    else:
        model_kwargs["hv_a"] = hv_a
        band_num = 2
    tm = TwistKP(**model_kwargs)

    print(
        "[kp] Reciprocal lattice vector of single-layer structure: \n",
        tm._mono_b_base,
    )
    print("[kp] Reciprocal lattice vector of moire structure: \n", tm._moire_b_base)

    if intra_t_idxs.shape[0] == 0:
        intra_t_idxs = np.array([[0, 0]])
        intra_t_coes = np.zeros((1, band_num, band_num), dtype=complex)
    if intra_b_idxs.shape[0] == 0:
        intra_b_idxs = np.array([[0, 0]])
        intra_b_coes = np.zeros((1, band_num, band_num), dtype=complex)

    irelax, order_num, kappa_parallel, _ = cfg.relax_para()
    if irelax:
        twist_relax = TwistRelaxKP(tm)
        u_idxs, u_coes = twist_relax.gen_relax_pattern(theta, kappa_parallel)

        inter_idxs, inter_coes = twist_relax.gen_relax_coupling(
            inter_idxs, inter_coes, order_num, valley_pos=tm._valley_pos
        )
        intra_t_idxs, intra_t_coes = twist_relax.gen_relax_coupling(
            intra_t_idxs, intra_t_coes, order_num
        )
        intra_b_idxs, intra_b_coes = twist_relax.gen_relax_coupling(
            intra_b_idxs, intra_b_coes, order_num
        )

    tm.gen_couple(
        inter_idxs,
        intra_t_idxs,
        intra_b_idxs,
        inter_coes,
        intra_t_coes,
        intra_b_coes,
    )
    return tm


def gen_kp_band(tm, cfg: InputConfig) -> None:
    """
    Compute and save k·p band structure.

    Args:
        tm: TwistKP object.
        cfg: Input configuration.
    """
    path, nk = cfg.kp_path()
    labels, ylim = cfg.kp_band_plot()
    k_vec, k_dist, k_node = tm.k_path(path, nk)
    evals = tm.solve_all(k_vec)

    fermi_shift = cfg.kp_shift()
    if fermi_shift == "max":
        fermi_energy = np.max(evals)
    elif fermi_shift == "min":
        fermi_energy = np.min(evals)
    else:
        fermi_energy = fermi_shift
    evals = evals - fermi_energy

    file_name = str(cfg.output_dir) + "/" + "BAND.dat"
    write_band_file(evals, k_dist,filename=file_name)
    np.savetxt(cfg.output_dir / "band.txt", evals)
    np.savetxt(cfg.output_dir / "k_vec.txt", k_vec)
    np.savetxt(cfg.output_dir / "k_dist.txt", k_dist)
    np.savetxt(cfg.output_dir / "k_node.txt", k_node)
    print(f"[kp.band] Saved bands to {cfg.output_dir/'BAND.dat'}")

    with open(str(cfg.output_dir) + "/k_labels.txt", "w", encoding="utf-8") as f:
        f.write(str(labels))
    # Visualization
    if _VIZ_OK:
        try:
            fig_path = cfg.output_dir / cfg.fig_band
            viz_plot_band(
                ylim=tuple(ylim) if ylim else None,
                ef=0.0,
                save=str(fig_path),
                load=str(cfg.output_dir),
                show=cfg.show_plots,
                color="k",
                units="meV"
            )
            print(f"[viz] KP band figure saved to {fig_path}")
        except Exception as e:
            print(f"[viz] KP band plotting skipped due to error: {e}")
    else:
        print("[viz] twist_viz not found; skip KP band plot.")


def gen_kp_chern(tm, cfg: InputConfig) -> None:
    """
    Compute and save the Chern number for a k·p band.

    Args:
        tm: TwistKP object.
        cfg: Input configuration.
    """
    n, band_index = cfg.kp_chern()
    Q = tm.gen_chern_number(n=n, band_index=band_index)
    out_file = cfg.output_dir / "chern_number.txt"
    np.savetxt(out_file, np.atleast_1d(Q), fmt="%d")
    print(f"[kp.chern] Saved Chern number to {out_file}")


def gen_mono_model(cfg: InputConfig):
    (wpath, wpref, ef_opt) = cfg.io_in_w90()
    mono_model = read_mono(wpath, wpref, fermi_energy=ef_opt)
    return mono_model

def gen_mono_band(mono_model, cfg: InputConfig):
    path, nk = cfg.tb_k_path()
    k_vec, k_dist, k_node = mono_model.k_path(path, nk)
    evals = mono_model.solve_all(k_vec)
    file_name = str(cfg.output_dir) + "/" + "BAND.dat"
    write_band_file(evals, k_dist, filename=file_name)

    labels, ylim = cfg.tb_band_plot()
    if _VIZ_OK:
        try:
            fig_path = cfg.output_dir / cfg.fig_band
            viz_plot_band(ylim=tuple(ylim) if ylim else None,
                          ef=0.0, load=str(cfg.output_dir), save=str(fig_path), show=cfg.show_plots, color='k',
                          isparse=False)
            print(f"[viz] TB band figure saved to {fig_path}")
        except Exception as e:
            print(f"[viz] TB band plotting skipped due to error: {e}")
    else:
        print("[viz] twist_viz not found; skip TB band plot.")
# ============================================================================
# Task dispatcher
# ============================================================================
MODE_REGISTRY = {
    "kp": gen_kp_model,
    "tb": gen_tb_model,
    "struc": gen_struc_model,
    "mono": gen_mono_model,
}
GE_TASK_REGISTRY = {
    "find_com": find_com,
    "gen_struc": gen_pos,
}
TB_TASK_REGISTRY = {
    "band": gen_tb_band,
}
KP_TASK_REGISTRY = {
    "band": gen_kp_band,
    "chern": gen_kp_chern,
}
MN_TASK_REGISTRY = {
    "band": gen_mono_band,
}


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Driver for twist electronic‑structure code (with viz)."
    )
    parser.add_argument(
        "--input", "-i", default="input.json", help="Path to input.json"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress banner and summary output"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="disable ANSI color in TTY output"
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--cite", action="store_true", help="print citation info and exit")
    args = parser.parse_args()

    if args.version:
        print(f"MoireStudio {__VERSION__}")
        return
    if args.cite:
        print(f"PRB doi:{_PRB_DOI}\nCPC doi:{_CPC_DOI}")
        return

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cfg = InputConfig(data)
    run_meta = _print_banner(cfg, in_path, args)
    _write_metadata(cfg, in_path, run_meta)
    task = cfg.task.lower()
    mode = cfg.mode.lower()

    if mode not in MODE_REGISTRY:
        raise KeyError(f"Unknown mode '{mode}'. Valid: {list(MODE_REGISTRY.keys())}")
    tm = MODE_REGISTRY[mode](cfg)

    if not args.quiet:
        try:
            if mode == "tb":
                nst = getattr(tm, "_total_state_num", None)
                if nst is not None:
                    print(f"[tb] total states per k: {nst}")
            elif mode == "kp":
                # Example: kp band count or shell number
                print(
                    f"[kp] G‑shell truncation: tr={cfg.kp_tr()}  valley={cfg.kp_valley_name()}"
                )
        except Exception:
            pass

    if mode == "kp":
        if task not in KP_TASK_REGISTRY:
            raise KeyError(f"Unknown KP task '{task}'. Valid: {list(KP_TASK_REGISTRY.keys())}")
        KP_TASK_REGISTRY[task](tm, cfg)
    elif mode == "tb":
        if task not in TB_TASK_REGISTRY:
            raise KeyError(f"Unknown TB task '{task}'. Valid: {list(TB_TASK_REGISTRY.keys())}")
        TB_TASK_REGISTRY[task](tm, cfg)
    elif mode == "struc":
        if task not in GE_TASK_REGISTRY:
            raise KeyError(
                f"Unknown struc task '{task}'. Valid: {list(GE_TASK_REGISTRY.keys())}"
            )
        GE_TASK_REGISTRY[task](tm, cfg)
    if not args.quiet:
        print("== Done ==")
    print("over")


if __name__ == "__main__":
    main()