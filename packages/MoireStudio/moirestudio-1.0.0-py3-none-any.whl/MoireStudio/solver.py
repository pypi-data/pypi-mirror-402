"""
Parallel and streaming eigensolver for moiré/twisted systems.

This module provides parallel and memory-efficient eigensolvers for large-scale
tight-binding calculations in twisted bilayer systems. It supports both dense
and sparse Hamiltonian matrices, with cross-platform compatibility (Linux/Windows/macOS)
and memory-safe operation for large problems.
"""

import os
import sys
import math
import warnings
import tempfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import numpy as np


def solve_all(ham_k, eig=False):
    """
    Sequential eigensolver for a batch of dense Hamiltonian matrices.

    Parameters
    ----------
    ham_k : numpy.ndarray
        Array of Hamiltonian matrices with shape (k_num, dim_ham, dim_ham).
    eig : bool, optional
        If True, return both eigenvalues and eigenvectors (default: False).

    Returns
    -------
    numpy.ndarray or tuple
        - If eig=False: eigenvalues array with shape (k_num, dim_ham)
        - If eig=True: tuple (eigenvalues, eigenvectors) where eigenvalues
          has shape (k_num, dim_ham) and eigenvectors has shape (k_num, dim_ham, dim_ham)

    Notes
    -----
    Uses numpy.linalg.eigh/eigvalsh for sequential computation.
    Suitable for small to medium-sized problems where parallel overhead
    would outweigh benefits.
    """
    k_num = ham_k.shape[0]
    dim_ham = ham_k.shape[1]

    if eig:
        evals = np.zeros((k_num, dim_ham), dtype=float)
        eiges = np.zeros((k_num, dim_ham, dim_ham), dtype=complex)
        for i in range(k_num):
            evals[i], eiges[i] = np.linalg.eigh(ham_k[i])
        return evals, eiges
    else:
        evals = np.zeros((k_num, dim_ham), dtype=float)
        for i in range(k_num):
            evals[i] = np.linalg.eigvalsh(ham_k[i])
        return evals


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
    - Linux: Uses 'forkserver' for stability (less state leakage than 'fork')
    - Windows/macOS: Uses 'spawn' (only option available)
    - Can be overridden by passing explicit 'start' parameter
    """
    import multiprocessing as mp
    if start:
        return mp.get_context(start)
    if sys.platform.startswith("linux"):
        return mp.get_context("forkserver")
    return mp.get_context("spawn")


def _init_blas_threads(blas_threads: int = 1):
    """
    Set BLAS/OMP environment variables within a process to avoid oversubscription.

    Parameters
    ----------
    blas_threads : int, optional
        Number of threads for BLAS/OMP operations (default: 1).

    Notes
    -----
    Recommendation: use blas_threads=1 in a process pool; for a thread pool,
    lower MKL/OMP threads to avoid oversubscription.
    """
    for var in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "BLIS_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[var] = str(blas_threads)


def _dense_worker_eigh_from_memmap(i, eig, shape, dtype, filename):
    """
    Child-process worker for dense matrix diagonalization from memory-mapped file.

    Parameters
    ----------
    i : int
        Index of the Hamiltonian matrix to process.
    eig : bool
        If True, compute both eigenvalues and eigenvectors.
    shape : tuple
        Shape of the full Hamiltonian array (k_num, dim_ham, dim_ham).
    dtype : str
        Data type of the Hamiltonian matrices.
    filename : str
        Path to memory-mapped file containing Hamiltonian data.

    Returns
    -------
    tuple
        (i, w, v) where:
        - i: input index
        - w: eigenvalues array
        - v: eigenvectors array or None if eig=False

    Notes
    -----
    Reads a single dense Hamiltonian H from a shared memory-mapped file and
    computes eigenvalues/eigenvectors using numpy.linalg.eigh/eigvalsh.
    Memory-efficient for large batches as it avoids data duplication.
    """
    arr = np.memmap(filename, dtype=np.dtype(dtype), mode="r", shape=tuple(shape))
    H = np.array(arr[i], copy=False)

    if eig:
        w, v = np.linalg.eigh(H)
        return i, w, v
    else:
        w = np.linalg.eigvalsh(H)
        return i, w, None


def _chunk_indices(n, chunks):
    """
    Split a range [0..n) into roughly equal contiguous chunks.

    Parameters
    ----------
    n : int
        Total number of items.
    chunks : int
        Number of chunks to create.

    Returns
    -------
    list of numpy.ndarray
        List of arrays, each containing indices for one chunk.

    Notes
    -----
    Used to reduce scheduler overhead in parallel computations.
    Ensures all chunks are non-empty and as balanced as possible.
    """
    edges = np.linspace(0, n, num=chunks + 1, dtype=int)
    return [np.arange(edges[j], edges[j + 1]) for j in range(chunks) if edges[j] < edges[j + 1]]


def solve_all_parallel(
        ham_k: np.ndarray,
        eig: bool = False,
        core_num: int | None = None,
        blas_threads: int = 1,
        use_memmap: bool = True,
        memmap_path: str | None = None,
        keep_memmap: bool = False,
        backend: str = "process",
        thread_workers: int | None = None,
        mp_start: str | None = None,
):
    """
    Parallel dense eigensolver for a batch of Hermitian matrices.

    Solves eigenvalue problems for a batch of dense Hermitian matrices
    ham_k[k, n, n] using parallel computation.

    Parameters
    ----------
    ham_k : numpy.ndarray
        Array of Hamiltonian matrices with shape (k_num, dim_ham, dim_ham).
    eig : bool, optional
        If True, return both eigenvalues and eigenvectors (default: False).
    core_num : int or None, optional
        Number of processes/cores to use. If None, uses os.cpu_count() (default: None).
    blas_threads : int, optional
        Number of BLAS/OMP threads per process (default: 1).
    use_memmap : bool, optional
        Use memory-mapped files for data sharing between processes (default: True).
    memmap_path : str or None, optional
        Path for memory-mapped file. If None, creates temporary file (default: None).
    keep_memmap : bool, optional
        Keep memory-mapped file after computation (default: False).
    backend : str, optional
        Parallelization backend: 'process' or 'thread' (default: 'process').
    thread_workers : int or None, optional
        Number of threads for thread backend. If None, uses min(4, cpu_count) (default: None).
    mp_start : str or None, optional
        Multiprocessing start method (see pick_mp_context) (default: None).

    Returns
    -------
    numpy.ndarray or tuple
        - If eig=False: eigenvalues array with shape (k_num, dim_ham)
        - If eig=True: tuple (eigenvalues, eigenvectors) where eigenvalues
          has shape (k_num, dim_ham) and eigenvectors has shape (k_num, dim_ham, dim_ham)

    Raises
    ------
    ValueError
        If backend is not 'process' or 'thread'.

    Notes
    -----
    Supports two backends:
    1. 'process': Uses process pool with memory-mapped files for data sharing
       (Windows/macOS friendly, avoids pickle serialization overhead).
    2. 'thread': Uses thread pool (lower overhead on Windows) but requires
       careful BLAS thread management to avoid oversubscription.

    For large datasets, memory-mapped files significantly reduce memory usage
    by avoiding data duplication between processes.
    """
    k_num = ham_k.shape[0]
    dim_ham = ham_k.shape[1]

    if core_num is None or core_num <= 0:
        core_num = os.cpu_count() or 1

    # Pre-allocate results
    if eig:
        evals = np.empty((k_num, dim_ham), dtype=float)
        eigvecs = np.empty((k_num, dim_ham, dim_ham), dtype=complex)
    else:
        evals = np.empty((k_num, dim_ham), dtype=float)
        eigvecs = None

    if backend not in ("process", "thread"):
        raise ValueError("backend must be 'process' or 'thread'")

    # Prepare memory-mapped file if requested
    need_cleanup = False
    if use_memmap:
        if memmap_path is None:
            fd, memmap_path = tempfile.mkstemp(prefix="hamk_", suffix=".mmap")
            os.close(fd)
            need_cleanup = not keep_memmap

        # Write data to memory-mapped file
        mm = np.memmap(memmap_path, dtype=ham_k.dtype, mode="w+", shape=ham_k.shape)
        mm[...] = ham_k
        del mm  # Flush to disk
        ham_meta = (ham_k.shape, str(ham_k.dtype), memmap_path)
    else:
        ham_meta = None

    try:
        if backend == "thread":
            # Thread backend: keep BLAS threads modest to avoid oversubscription
            if thread_workers is None or thread_workers <= 0:
                thread_workers = min(4, os.cpu_count() or 1)
            _init_blas_threads(max(1, (os.cpu_count() or 1) // thread_workers))

            def _worker_direct(i, eig_=False):
                """Worker function for thread backend using direct array access."""
                H = ham_k[i]
                if eig_:
                    w, v = np.linalg.eigh(H)
                    return i, w, v
                else:
                    w = np.linalg.eigvalsh(H)
                    return i, w, None

            with ThreadPoolExecutor(max_workers=thread_workers) as ex:
                futs = []
                if use_memmap:
                    shape, dtype, filename = ham_meta
                    for i in range(k_num):
                        futs.append(ex.submit(_dense_worker_eigh_from_memmap,
                                              i, eig, shape, dtype, filename))
                else:
                    for i in range(k_num):
                        futs.append(ex.submit(_worker_direct, i, eig))

                # Collect results
                for fu in as_completed(futs):
                    i, w, v = fu.result()
                    evals[i] = w
                    if eig and v is not None:
                        eigvecs[i] = v

        else:
            # Process backend
            ctx = pick_mp_context(mp_start)
            with ProcessPoolExecutor(
                    max_workers=core_num,
                    mp_context=ctx,
                    initializer=_init_blas_threads,
                    initargs=(blas_threads,),
            ) as ex:
                futs = []
                if use_memmap:
                    shape, dtype, filename = ham_meta
                    for i in range(k_num):
                        futs.append(ex.submit(_dense_worker_eigh_from_memmap,
                                              i, eig, shape, dtype, filename))
                else:
                    def _worker_direct(i, eig_=False):
                        """Worker function for process backend using direct array access."""
                        H = ham_k[i]
                        if eig_:
                            w, v = np.linalg.eigh(H)
                            return i, w, v
                        else:
                            w = np.linalg.eigvalsh(H)
                            return i, w, None

                    for i in range(k_num):
                        futs.append(ex.submit(_worker_direct, i, eig))

                # Collect results
                for fu in as_completed(futs):
                    i, w, v = fu.result()
                    evals[i] = w
                    if eig and v is not None:
                        eigvecs[i] = v

    finally:
        # Clean up temporary memory-mapped file
        if use_memmap and need_cleanup:
            try:
                os.remove(memmap_path)
            except OSError:
                pass

    return (evals, eigvecs) if eig else evals


def _sparse_worker_streaming(
        indices,
        k_list,
        build_ham_at_k,
        num_eigs,
        eigvecs,
        which,
        sigma,
        tol,
        maxiter,
        evals_memmap_path,
        evals_shape,
        evals_dtype,
        save_eigvecs_dir,
        blas_threads,
):
    """
    Child-process worker for streaming sparse eigensolver.

    Parameters
    ----------
    indices : numpy.ndarray
        Array of k-point indices to process.
    k_list : list
        List of k-points (objects/arrays).
    build_ham_at_k : callable
        Function that builds Hamiltonian matrix H(k) for given k-point.
    num_eigs : int
        Number of eigenvalues/eigenvectors to compute.
    eigvecs : bool
        If True, compute eigenvectors.
    which : str
        Which eigenvalues to compute ('LM', 'SA', etc.).
    sigma : float or None
        Shift for shift-invert mode.
    tol : float
        Tolerance for eigenvalue convergence.
    maxiter : int or None
        Maximum number of iterations.
    evals_memmap_path : str
        Path to memory-mapped file for storing eigenvalues.
    evals_shape : tuple
        Shape of eigenvalues array (k_num, num_eigs).
    evals_dtype : str
        Data type for eigenvalues.
    save_eigvecs_dir : str or None
        Directory to save eigenvectors (None if not saving).
    blas_threads : int
        Number of BLAS threads per process.

    Returns
    -------
    int
        Number of k-points processed.

    Notes
    -----
    For each k-point in 'indices', builds H(k) via 'build_ham_at_k', runs
    scipy.sparse.linalg.eigsh, and writes results to shared memory-mapped file.

    If sigma is provided but H is a LinearOperator, falls back to normal mode
    (shift-invert not supported for LinearOperator).
    """
    _init_blas_threads(blas_threads)
    from scipy.sparse.linalg import eigsh, LinearOperator

    # Open shared memory-mapped file for eigenvalues
    evals_mm = np.memmap(evals_memmap_path, dtype=np.dtype(evals_dtype),
                         mode="r+", shape=evals_shape)

    for gi in indices:
        kobj = k_list[gi]
        H = build_ham_at_k(kobj)

        # Handle LinearOperator limitations
        use_sigma = sigma
        use_which = which
        if isinstance(H, LinearOperator) and sigma is not None:
            use_sigma = None
            use_which = "SA" if which not in ("LA", "SA") else which

        # Compute eigenvalues/eigenvectors
        res = eigsh(
            H,
            k=num_eigs,
            which=use_which,
            sigma=use_sigma,
            tol=tol,
            maxiter=maxiter,
            return_eigenvectors=eigvecs,
        )

        if eigvecs:
            vals, vecs = res
        else:
            vals = res
            vecs = None

        # Sort eigenvalues
        order = np.argsort(vals.real)
        vals = vals[order]

        # Store eigenvalues in shared memory
        evals_mm[gi, : len(vals)] = vals.real

        # Save eigenvectors if requested
        if eigvecs and save_eigvecs_dir and vecs is not None:
            vecs = vecs[:, order]
            np.save(os.path.join(save_eigvecs_dir, f"eigvecs_k{gi}.npy"), vecs)

    return len(indices)


def solve_low_energy_streaming_parallel(
        k_list: list,
        build_ham_at_k,
        num_eigs: int = 32,
        eigvecs: bool = True,
        core_num: int | None = None,
        sigma: float | None = None,
        which: str | None = None,
        tol: float = 1e-8,
        maxiter: int | None = None,
        save_dir: str | None = None,
        blas_threads: int = 1,
        mp_start: str | None = None,
) -> np.ndarray:
    """
    Streaming, memory-efficient parallel solver for large sparse Hermitian matrices.

    Designed for very large sparse Hamiltonian matrices H(k) (e.g., ~20k x 20k)
    where only a small number of low-energy eigenpairs are needed.

    Parameters
    ----------
    k_list : list
        List of k-points to process.
    build_ham_at_k : callable
        Function that builds Hamiltonian matrix H(k) for given k-point.
        Can return CSR/CSC matrix or LinearOperator.
    num_eigs : int, optional
        Number of eigenvalues/eigenvectors to compute (default: 32).
    eigvecs : bool, optional
        If True, compute and save eigenvectors (default: True).
    core_num : int or None, optional
        Number of processes to use. If None, uses os.cpu_count() (default: None).
    sigma : float or None, optional
        Shift for shift-invert mode (default: None).
    which : str or None, optional
        Which eigenvalues to compute ('LM', 'SA', 'LA', etc.).
        If None: 'LM' if sigma is not None, else 'SA' (default: None).
    tol : float, optional
        Tolerance for eigenvalue convergence (default: 1e-8).
    maxiter : int or None, optional
        Maximum number of iterations (default: None).
    save_dir : str or None, optional
        Directory to save eigenvectors. If None and eigvecs=True,
        creates temporary directory (default: None).
    blas_threads : int, optional
        Number of BLAS threads per process (default: 1).
    mp_start : str or None, optional
        Multiprocessing start method (default: None).

    Returns
    -------
    numpy.ndarray
        Eigenvalues array with shape (len(k_list), num_eigs).

    Raises
    ------
    ValueError
        If k_list is empty.

    Notes
    -----
    - Uses memory-mapped files for eigenvalue storage to avoid memory duplication.
    - If sigma is not None, shift-invert is used (requires concrete sparse matrix).
    - If build_ham_at_k returns a LinearOperator, sigma must be None (falls back to normal mode).
    - Eigenvectors are saved to individual .npy files in save_dir.
    - For very large problems, this streaming approach is more memory-efficient
      than collecting all eigenvectors in memory.
    """
    if core_num is None or core_num <= 0:
        core_num = os.cpu_count() or 1

    # Determine which eigenvalues to compute
    if which is None:
        which = "LM" if sigma is not None else "SA"

    k_num = len(k_list)
    if k_num == 0:
        raise ValueError("k_list is empty.")

    # Create shared memory-mapped file for eigenvalues
    fd, evals_path = tempfile.mkstemp(prefix="evals_", suffix=".mmap")
    os.close(fd)
    evals_mm = np.memmap(evals_path, dtype=np.float64, mode="w+", shape=(k_num, num_eigs))
    evals_mm[...] = np.nan  # Initialize with NaN

    # Prepare eigenvector directory
    made_temp_vec_dir = False
    if eigvecs:
        if save_dir is None:
            import tempfile as _tf
            save_dir = _tf.mkdtemp(prefix="eigvecs_")
            made_temp_vec_dir = True
        os.makedirs(save_dir, exist_ok=True)

    # Split work into chunks
    chunks = _chunk_indices(k_num, core_num)

    try:
        ctx = pick_mp_context(mp_start)
        with ProcessPoolExecutor(
                max_workers=core_num,
                mp_context=ctx,
                initializer=_init_blas_threads,
                initargs=(blas_threads,),
        ) as ex:
            # Submit all chunks for parallel processing
            futs = []
            for arr_idx in chunks:
                futs.append(
                    ex.submit(
                        _sparse_worker_streaming,
                        arr_idx,
                        k_list,
                        build_ham_at_k,
                        num_eigs,
                        eigvecs,
                        which,
                        sigma,
                        tol,
                        maxiter,
                        evals_path,
                        (k_num, num_eigs),
                        str(np.float64().dtype),
                        save_dir if eigvecs else None,
                        blas_threads,
                    )
                )

            # Wait for completion
            _ = [fu.result() for fu in as_completed(futs)]

    finally:
        # Read results from memory-mapped file
        evals = np.array(evals_mm)

        # Clean up temporary files
        try:
            os.remove(evals_path)
        except OSError:
            pass

        # Warn about temporary eigenvector directory
        if eigvecs and made_temp_vec_dir:
            warnings.warn(f"Eigenvectors saved to temporary directory: {save_dir}")

    return evals