# Parallel Processing Guide for TEM1D

This guide explains how to use parallel processing to compute millions of TEM1D forward responses efficiently using the multiprocessing-based parallel execution utilities.

## Overview

The parallel processing system is designed to:
- Scale from thousands to millions of forward models
- Achieve near-linear speedup on multi-core systems
- Handle memory efficiently through chunking
- Provide automatic load balancing
- Validate correctness against sequential computation

## Quick Start

```python
import numpy as np
from parallel_utils import parallel_tem1d

# Generate 10,000 random 3-layer models
N_MODELS = 10000
N_LAYERS = 3

resistivities = 10 ** np.random.uniform(0, 3, size=(N_MODELS, N_LAYERS))
depths = np.zeros((N_MODELS, N_LAYERS))
# ... (depth generation logic)

# Compute in parallel
results = parallel_tem1d(
    resistivities,
    depths,
    n_workers=8,      # Use 8 CPU cores
    chunk_size=500,   # Process 500 models per chunk
    verbose=True,
)

print(f"Processed {len(results)} models")
```

## Architecture

### Multiprocessing Strategy

The system uses Python's `multiprocessing` module with a process pool to bypass the Global Interpreter Lock (GIL):

```
Main Process
├── Generate models (numpy arrays)
├── Split into chunks (e.g., 500 models/chunk)
└── Process Pool (N workers)
    ├── Worker 1: process chunk 1
    ├── Worker 2: process chunk 2
    ├── ...
    └── Worker N: process chunk N
```

**Why multiprocessing instead of threading?**
- TEM1D computation is CPU-bound (pure Fortran numerical code)
- Python's GIL prevents true parallel execution with threads
- Each process has its own Python interpreter and GIL
- Each process loads its own Fortran library instance

### Chunking System

Models are grouped into chunks to balance:
- **Serialization overhead**: Sending data between processes
- **Load balancing**: Distributing work evenly
- **Memory usage**: Limiting per-chunk memory footprint

**Example**: 10,000 models with chunk_size=500
- Creates 20 chunks
- Each chunk: 500 models
- With 8 workers: ~2-3 chunks per worker
- Good load balancing, moderate overhead

## Performance Characteristics

### Benchmark Results (128-core system)

| Model Count | Sequential | Parallel | Speedup | Throughput |
|-------------|-----------|----------|---------|------------|
| 100 models | 0.5s | 2.3s | 0.2x | 44 models/s |
| 1,000 models | 4.96s | 3.42s | 1.45x | 292 models/s |
| 10,000 models | 50.3s | 1.40s | 35.8x | **7,121 models/s** |
| 100,000 models | ~503s | ~14s | ~36x | ~7,000 models/s |
| 1,000,000 models | ~1.4 hours | ~2.3 min | ~36x | ~7,000 models/s |

**Key observations**:
1. **Small batches (<1000)**: Sequential is faster due to multiprocessing overhead
2. **Medium batches (1K-10K)**: Parallel starts to shine
3. **Large batches (>10K)**: Massive speedup (30-40x)

### Scaling Behavior

**Speedup vs Number of Workers** (10,000 models, chunk_size=100):
- 1 worker: 1.0x (baseline)
- 4 workers: 3.5-3.8x (88-95% efficiency)
- 8 workers: 6.5-7.5x (81-94% efficiency)
- 16 workers: 12-15x (75-94% efficiency)
- 32 workers: 20-28x (62-87% efficiency)
- 64 workers: 30-40x (47-62% efficiency)
- 128 workers: 35-45x (27-35% efficiency)

**Efficiency = Speedup / N_workers × 100%**

Efficiency decreases with more workers due to:
- Overhead from process creation and management
- Memory bandwidth limitations
- Hyperthreading (logical vs physical cores)
- Diminishing returns beyond physical cores

## Optimization Guide

### Choosing Number of Workers

**General rule**: `n_workers = number of physical CPU cores`

```python
from multiprocessing import cpu_count

# Get total CPU count (includes hyperthreading)
total_cpus = cpu_count()  # e.g., 16 on 8-core hyperthreaded CPU

# Recommendation:
# - For CPU-bound work: Use physical cores only
# - For mixed workload: Use all logical cores

n_workers = total_cpus  # Start here, then tune
```

**System-specific recommendations**:
- **Desktop (4-8 cores)**: Use all cores (`n_workers=None`)
- **Workstation (16-32 cores)**: Use all cores or `n_workers = cpu_count()`
- **Server (64+ cores)**: May need tuning; test different values
- **Cluster**: Consider using Dask or Ray for multi-node

### Choosing Chunk Size

**Rule of thumb**: Aim for **10-20 chunks per worker**

```python
from parallel_utils import adaptive_chunk_size

# Automatically compute optimal chunk size
chunk_size = adaptive_chunk_size(n_models, n_workers)
```

**Manual tuning**:
| Model Count | Recommended Chunk Size | Reasoning |
|-------------|----------------------|-----------|
| 100-1,000 | 50-100 | Small overhead, maximize parallelism |
| 1,000-10,000 | 100-500 | Balance overhead vs load balancing |
| 10,000-100,000 | 500-1,000 | Amortize overhead, still good balance |
| 100,000+ | 1,000-2,000 | Minimize overhead, plenty of chunks |

**Testing chunk sizes**:
```python
# Test different chunk sizes to find optimal
for chunk_size in [100, 250, 500, 1000]:
    start = time.time()
    results = parallel_tem1d(
        resistivities, depths,
        chunk_size=chunk_size,
        verbose=False
    )
    elapsed = time.time() - start
    print(f"Chunk {chunk_size}: {elapsed:.2f}s")
```

### Memory Considerations

**Memory per model**: ~50 KB (input arrays + results)
- 10,000 models: ~500 MB
- 100,000 models: ~5 GB
- 1,000,000 models: ~50 GB

**Memory per worker**: ~50 MB (Python runtime + Fortran library)
- 8 workers: ~400 MB overhead
- 128 workers: ~6.4 GB overhead

**For very large batches (>10M models)**:
```python
# Option 1: Process in batches
batch_size = 1_000_000
for i in range(0, n_total_models, batch_size):
    batch_results = parallel_tem1d(
        resistivities[i:i+batch_size],
        depths[i:i+batch_size],
        ...
    )
    # Save or process batch_results
    save_batch(batch_results, f"batch_{i}.npz")

# Option 2: Use shared memory (advanced)
from multiprocessing import shared_memory
# See parallel_utils.py for implementation details
```

## Usage Examples

### Example 1: Monte Carlo Uncertainty Analysis

```python
import numpy as np
from parallel_utils import parallel_tem1d

# Generate 100,000 random models for uncertainty quantification
np.random.seed(42)
N_MODELS = 100000
N_LAYERS = 3

# Log-normal distribution for resistivities
resistivities = 10 ** np.random.normal(
    loc=2.0, scale=0.5, size=(N_MODELS, N_LAYERS)
)

# Normal distribution for layer thicknesses
thicknesses = np.random.normal(
    loc=[30, 70], scale=[5, 10], size=(N_MODELS, 2)
)
depths = np.zeros((N_MODELS, N_LAYERS))
depths[:, 1] = thicknesses[:, 0]
depths[:, 2] = thicknesses[:, 0] + thicknesses[:, 1]

# Compute all responses in parallel
results = parallel_tem1d(
    resistivities, depths,
    n_workers=16,
    chunk_size=1000,
    verbose=True
)

# Compute ensemble statistics
all_responses = np.array([r.responses for r in results])
median = np.median(all_responses, axis=0)
p10 = np.percentile(all_responses, 10, axis=0)
p90 = np.percentile(all_responses, 90, axis=0)
```

### Example 2: Parameter Space Exploration

```python
from parallel_utils import parallel_tem1d
import numpy as np

# Systematically sample parameter space
rho1_values = np.logspace(1, 3, 50)  # 50 values
rho2_values = np.logspace(0, 2, 40)  # 40 values
h1_values = np.linspace(10, 100, 30)  # 30 values

# Create all combinations: 50 × 40 × 30 = 60,000 models
rho1, rho2, h1 = np.meshgrid(rho1_values, rho2_values, h1_values)
rho1 = rho1.ravel()
rho2 = rho2.ravel()
h1 = h1.ravel()

n_models = len(rho1)
resistivities = np.column_stack([rho1, rho2])
depths = np.column_stack([np.zeros(n_models), h1])

# Parallel computation
results = parallel_tem1d(
    resistivities, depths,
    chunk_size=500,
    verbose=True
)

# Reshape results for analysis
responses_grid = np.array([r.responses for r in results]).reshape(
    (50, 40, 30, -1)  # (rho1, rho2, h1, time)
)
```

### Example 3: Validation and Comparison

```python
from parallel_utils import parallel_tem1d
from pytem1d import run_tem1d
import numpy as np

# Generate test models
n_test = 1000
resistivities = 10 ** np.random.uniform(0, 3, size=(n_test, 3))
depths = np.array([[0, 30, 100]] * n_test)

# Compute subset sequentially for validation
print("Computing 100 models sequentially...")
results_seq = []
for i in range(100):
    results_seq.append(run_tem1d(resistivities[i], depths[i]))

# Compute all in parallel
print("Computing all 1000 models in parallel...")
results_par = parallel_tem1d(resistivities, depths)

# Validate
print("\nValidation:")
for i in range(100):
    diff = np.abs(results_seq[i].responses - results_par[i].responses).max()
    assert diff < 1e-10, f"Model {i} differs by {diff}"
print("✓ All results match!")
```

## Troubleshooting

### Issue: Poor Speedup (<2x with 8+ cores)

**Possible causes and solutions**:

1. **Too few models**: Need >10,000 for good speedup
   ```python
   # Solution: Only use parallel for large batches
   if n_models > 10000:
       results = parallel_tem1d(...)
   else:
       results = [run_tem1d(...) for ...]  # Sequential
   ```

2. **Chunk size too large**: Not enough chunks for all workers
   ```python
   # Solution: Reduce chunk size
   chunk_size = n_models // (n_workers * 10)  # 10 chunks per worker
   ```

3. **Hyperthreading**: Logical cores don't double performance
   ```python
   # Solution: Use physical cores only
   import psutil
   n_workers = psutil.cpu_count(logical=False)
   ```

### Issue: Memory Error

**Solution 1: Reduce batch size**
```python
# Process in smaller batches
batch_size = 100000
for i in range(0, n_total, batch_size):
    batch_results = parallel_tem1d(
        resistivities[i:i+batch_size], ...
    )
    np.savez(f"batch_{i}.npz", results=batch_results)
```

**Solution 2: Reduce workers**
```python
# Fewer workers = less memory overhead
n_workers = max(4, cpu_count() // 4)
```

### Issue: "Library not loaded" error in workers

**Cause**: Each worker process must load Fortran library independently

**Solution**: Ensure `worker_init()` is properly configured
```python
# In parallel_utils.py, worker_init() should:
from pytem1d.core import load_library
load_library()  # Loads libtem1d.so in this process
```

### Issue: Results differ between sequential and parallel

**Diagnosis**:
```python
# Check maximum difference
max_diff = 0
for i in range(min(len(results_seq), len(results_par))):
    diff = np.abs(results_seq[i].responses - results_par[i].responses).max()
    max_diff = max(max_diff, diff)
print(f"Max diff: {max_diff}")
```

**Expected**: `max_diff < 1e-10` (numerical precision)

**If max_diff > 1e-6**: Potential bug; please report

## Advanced Topics

### Custom Worker Initialization

```python
def custom_worker_init():
    """Custom initialization per worker"""
    import os
    # Set worker-specific environment variables
    worker_id = os.getpid()
    os.environ['WORKER_ID'] = str(worker_id)

    # Load library
    from pytem1d.core import load_library
    load_library()

# Use custom initializer
with Pool(processes=n_workers, initializer=custom_worker_init) as pool:
    ...
```

### Progress Tracking

```python
from multiprocessing import Manager, Pool
from tqdm import tqdm

def compute_chunk_with_progress(args):
    chunk_idx, resistivities, depths, tx_area, progress_dict = args
    # ... compute chunk ...
    progress_dict['completed'] += len(resistivities)
    return chunk_idx, results

# Use Manager for shared progress counter
manager = Manager()
progress_dict = manager.dict({'completed': 0})

# Add progress_dict to chunk arguments
chunks_with_progress = [
    (*chunk, progress_dict) for chunk in chunks
]

# Monitor progress in main process
with Pool(n_workers) as pool:
    async_result = pool.map_async(compute_chunk_with_progress, chunks_with_progress)

    with tqdm(total=n_models) as pbar:
        while not async_result.ready():
            pbar.n = progress_dict['completed']
            pbar.refresh()
            time.sleep(0.1)
```

### Integration with Dask (Multi-Node)

```python
from dask.distributed import Client
import dask.array as da

# Connect to Dask cluster
client = Client('scheduler-address:8786')

# Convert to Dask arrays
resistivities_da = da.from_array(resistivities, chunks=(1000, N_LAYERS))
depths_da = da.from_array(depths, chunks=(1000, N_LAYERS))

# Define computation function
def compute_model(rho, dep):
    from pytem1d import run_tem1d
    return run_tem1d(rho, dep)

# Map across Dask array (distributed)
results = da.map_blocks(
    lambda block: np.array([compute_model(block[i], depths[i]) for i in range(len(block))]),
    resistivities_da
)

# Compute on cluster
results_computed = results.compute()
```

## Best Practices

1. **Test scaling empirically**: Systems vary; always benchmark on your hardware
2. **Start small**: Test with 100-1000 models before scaling to millions
3. **Validate correctness**: Always compare parallel vs sequential on a subset
4. **Monitor memory**: Use `psutil` or system monitor for large runs
5. **Save incrementally**: For very large batches, save results as you go
6. **Use appropriate chunk size**: Follow the 10-20 chunks per worker rule
7. **Consider your use case**:
   - One-time analysis: Maximize workers
   - Production service: Leave cores for other processes
   - Shared system: Be considerate of other users

## Summary

- **Parallel processing enables**: 30-40x speedup for large batches (>10K models)
- **Best for**: Monte Carlo studies, parameter sweeps, uncertainty quantification
- **Not worth it for**: <1000 models (overhead dominates)
- **Key parameters**: `n_workers` (physical cores) and `chunk_size` (10-20 per worker)
- **Correctness**: Results identical to sequential (validated to numerical precision)

For questions or issues, see:
- `examples/batch_random_models_parallel.py` - Comprehensive benchmarking script
- `examples/parallel_utils.py` - Core parallel utilities
- `examples/test_parallel_10k.py` - Large-scale test example
