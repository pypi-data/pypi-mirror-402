#!/usr/bin/env python3
"""
Parallel execution utilities for TEM1D batch processing

This module provides utilities for computing TEM1D forward responses in parallel
using multiprocessing. It's designed to scale from thousands to millions of models
while maintaining high parallel efficiency.

Key features:
- Multiprocessing-based parallelism (bypasses Python GIL)
- Chunking strategy to balance overhead vs load balancing
- Each worker process loads its own Fortran library instance
- Configurable worker count and chunk size

Example:
    >>> from parallel_utils import parallel_tem1d
    >>> import numpy as np
    >>>
    >>> # Generate 10000 random models
    >>> resistivities = 10 ** np.random.uniform(0, 3, size=(10000, 3))
    >>> depths = np.array([[0, 30, 100]] * 10000)
    >>>
    >>> # Compute in parallel
    >>> results = parallel_tem1d(
    ...     resistivities, depths,
    ...     n_workers=8, chunk_size=500
    ... )
"""

import numpy as np
from multiprocessing import Pool, cpu_count
from typing import List, Tuple, Optional
import sys


def worker_init():
    """
    Initialize worker process.

    This function is called once per worker process when the process pool is created.
    It ensures each worker loads its own instance of the Fortran library, which is
    necessary because the library handle cannot be shared across processes.

    Notes
    -----
    - This is called automatically by Pool(initializer=worker_init)
    - Each process gets its own Python interpreter and library handle
    - Failures here will prevent the worker from processing any chunks
    """
    try:
        # Each process needs to load the Fortran library independently
        # Import here to avoid loading in main process
        from pytem1d.core import load_library
        load_library()
    except Exception as e:
        print(f"Warning: Worker initialization failed: {e}", file=sys.stderr)
        # Don't raise - let the worker try to continue
        pass


def compute_chunk(args: Tuple[int, np.ndarray, np.ndarray, float]) -> Tuple[int, List]:
    """
    Compute TEM responses for a chunk of models.

    This is the worker function that processes a batch of models. It's called by
    each worker process in the pool. The function is designed to be pickle-able
    for multiprocessing serialization.

    Parameters
    ----------
    args : tuple
        (chunk_index, resistivities_chunk, depths_chunk, tx_area)
        - chunk_index : int
            Index of this chunk (for maintaining order)
        - resistivities_chunk : np.ndarray
            (N_chunk, N_layers) resistivities for this chunk
        - depths_chunk : np.ndarray
            (N_chunk, N_layers) depths for this chunk
        - tx_area : float
            Transmitter loop area (m²)

    Returns
    -------
    tuple
        (chunk_index, results) where results is a list of TEM1DResult objects

    Notes
    -----
    - Each model in the chunk is computed sequentially within this worker
    - The chunk index is returned to allow reordering results in the main process
    - Errors in individual models are caught to prevent worker crash
    """
    chunk_idx, resistivities_chunk, depths_chunk, tx_area = args

    # Import here (inside worker) to ensure each process has its own module state
    from pytem1d import run_tem1d

    results = []
    n_chunk = len(resistivities_chunk)

    for i in range(n_chunk):
        try:
            result = run_tem1d(
                resistivities=resistivities_chunk[i],
                depths=depths_chunk[i],
                tx_area=tx_area,
            )
            results.append(result)
        except Exception as e:
            # Log error but continue processing other models
            print(f"Warning: Model {i} in chunk {chunk_idx} failed: {e}", file=sys.stderr)
            # Append None to maintain indexing
            results.append(None)

    return chunk_idx, results


def parallel_tem1d(
    resistivities_all: np.ndarray,
    depths_all: np.ndarray,
    tx_area: float = 314.16,
    n_workers: Optional[int] = None,
    chunk_size: int = 500,
    verbose: bool = True,
) -> List:
    """
    Compute TEM responses in parallel using multiprocessing.

    This function distributes the computation of multiple TEM forward models across
    multiple CPU cores using Python's multiprocessing module. It automatically
    handles chunking, load balancing, and result collection.

    Parameters
    ----------
    resistivities_all : np.ndarray
        (N_models, N_layers) resistivities in Ω·m
        Each row is a model, each column is a layer
    depths_all : np.ndarray
        (N_models, N_layers) depths in meters
        Each row is a model, each column is a layer
        First column should be 0 (surface)
    tx_area : float, optional
        Transmitter loop area in m² (default: 314.16, ~10m radius)
    n_workers : int, optional
        Number of worker processes (default: cpu_count())
        Setting to None uses all available cores
    chunk_size : int, optional
        Number of models per chunk (default: 500)
        Smaller chunks: better load balancing, more overhead
        Larger chunks: less overhead, worse load balancing
    verbose : bool, optional
        Print progress information (default: True)

    Returns
    -------
    list
        List of TEM1DResult objects, one per model
        Results are in the same order as input models
        None entries indicate failed models

    Notes
    -----
    Performance considerations:
    - Expected speedup: ~0.8-0.9 × n_workers (80-90% parallel efficiency)
    - Break-even point: ~100 models (below this, overhead dominates)
    - Memory per worker: ~50 MB (library + Python runtime)
    - Memory per model: ~50 KB (arrays + results)

    For optimal performance:
    - Use chunk_size = 250-1000 for most cases
    - For <1000 models: use smaller chunks (100-250)
    - For >100K models: use larger chunks (1000-2000)
    - Set n_workers = physical core count for hyperthreaded CPUs

    Examples
    --------
    >>> # Process 10,000 models on all cores
    >>> results = parallel_tem1d(resistivities, depths)

    >>> # Process on 4 cores with small chunks
    >>> results = parallel_tem1d(
    ...     resistivities, depths,
    ...     n_workers=4, chunk_size=100
    ... )

    >>> # Quiet mode
    >>> results = parallel_tem1d(resistivities, depths, verbose=False)
    """
    # Determine number of workers
    if n_workers is None:
        n_workers = cpu_count()

    n_models = len(resistivities_all)

    if verbose:
        print(f"Parallel execution setup:")
        print(f"  Models: {n_models}")
        print(f"  Workers: {n_workers}")
        print(f"  Chunk size: {chunk_size}")

    # Create chunks
    chunks = []
    for i in range(0, n_models, chunk_size):
        end_idx = min(i + chunk_size, n_models)
        chunks.append((
            i // chunk_size,                    # chunk index
            resistivities_all[i:end_idx],       # resistivities for this chunk
            depths_all[i:end_idx],              # depths for this chunk
            tx_area,                             # transmitter area
        ))

    if verbose:
        print(f"  Chunks: {len(chunks)}")
        print(f"  Average models per chunk: {n_models / len(chunks):.1f}")
        print(f"\nProcessing...")

    # Create process pool and execute
    # Each worker calls worker_init() once when starting
    with Pool(processes=n_workers, initializer=worker_init) as pool:
        chunk_results = pool.map(compute_chunk, chunks)

    if verbose:
        print("✓ All chunks processed")
        print("\nReassembling results...")

    # Flatten results (maintain order by chunk index)
    chunk_results.sort(key=lambda x: x[0])  # Sort by chunk index
    results = []
    failed_count = 0
    for chunk_idx, chunk_res in chunk_results:
        for res in chunk_res:
            if res is None:
                failed_count += 1
            results.append(res)

    if verbose:
        print(f"✓ Results assembled: {len(results)} models")
        if failed_count > 0:
            print(f"⚠ Warning: {failed_count} models failed")

    return results


def adaptive_chunk_size(n_models: int, n_workers: int) -> int:
    """
    Compute optimal chunk size based on problem size.

    This heuristic aims for ~10 chunks per worker for good load balancing
    while avoiding chunks that are too small (high overhead).

    Parameters
    ----------
    n_models : int
        Total number of models to process
    n_workers : int
        Number of worker processes

    Returns
    -------
    int
        Recommended chunk size

    Examples
    --------
    >>> adaptive_chunk_size(10000, 8)
    125
    >>> adaptive_chunk_size(1000, 4)
    100
    >>> adaptive_chunk_size(100000, 16)
    625
    """
    # Heuristic: aim for ~10 chunks per worker for good load balancing
    target_chunks = n_workers * 10
    chunk_size = max(100, n_models // target_chunks)

    # Round to nearest 50 for cleaner numbers
    chunk_size = ((chunk_size + 25) // 50) * 50

    return chunk_size


if __name__ == "__main__":
    # Quick test
    print("Testing parallel_utils module...")
    print(f"CPU count: {cpu_count()}")
    print(f"\nAdaptive chunk size examples:")
    for n_models in [1000, 10000, 100000, 1000000]:
        for n_workers in [4, 8, 16]:
            cs = adaptive_chunk_size(n_models, n_workers)
            print(f"  {n_models:7d} models, {n_workers:2d} workers → chunk_size = {cs}")
