# pytem1d Examples

This directory contains example scripts demonstrating various features of pytem1d.

## Quick Start

```bash
# Run any example
python basic_usage.py
python class_api.py
python plotting_demo.py
python batch_random_models.py
python numerical_derivatives.py
```

## Example Descriptions

### 1. basic_usage.py
**Simple functional API demonstration**

- Computes response for a simple 2-layer model
- Uses the functional `run_tem1d()` interface
- Creates a basic log-log plot
- **Best for**: Getting started, quick calculations

```python
result = run_tem1d([100, 10], [0, 50], tx_area=314.16)
plt.loglog(result.times * 1e3, abs(result.responses))
```

**Output**: `basic_tem_response.png`

### 2. class_api.py
**Advanced class-based API demonstration**

- Uses the `TEM1DModel` class for stateful modeling
- Demonstrates parameter studies (varying resistivity)
- Shows derivative calculation
- Uses built-in plotting functions
- **Best for**: Parameter studies, multiple runs

```python
tem = TEM1DModel()
tem.set_earth_model([100, 10, 50], [0, 30, 100])
tem.enable_derivatives(True)
result = tem.run()
```

**Output**:
- `class_api_response.png`
- `class_api_derivatives.png`
- `class_api_parameter_study.png`

### 3. plotting_demo.py
**Comprehensive visualization demonstration**

- Demonstrates all plotting utilities
- Creates multi-panel figures
- Shows different model types (2-layer, 3-layer, H-type)
- Includes normalized responses, decay curves
- Derivative heatmaps
- **Best for**: Publication-quality figures

**Output**:
- `plotting_demo_all.png` (6-panel figure)
- `derivatives_heatmap.png`

### 4. batch_random_models.py ⭐ NEW
**Batch processing and API comparison with configurable layers**

- Generates 1000 random N-layer models (default: 3 layers)
- Computes responses using BOTH functional and class-based APIs
- Validates that both APIs produce identical results
- Performance comparison between approaches
- Ensemble statistics and visualization
- **Best for**: Monte Carlo studies, uncertainty quantification

**Features**:
- **Configurable number of layers** (set `N_LAYERS` at top of file)
- Random model generation (log-uniform resistivities, 1-1000 Ω·m)
- Automatic depth generation (ensures monotonically increasing interfaces)
- Progress tracking with timing
- Comprehensive validation
- Statistical analysis (median, percentiles, variability)
- Adaptive plots (adjust to number of layers)

**Configuration** (edit at top of file):
```python
N_MODELS = 1000      # Number of random models
N_LAYERS = 3         # Number of layers (2, 3, 4, 5, ...)
RANDOM_SEED = 42     # For reproducibility
```

**Examples**:
```bash
# Default: 1000 random 3-layer models
python batch_random_models.py

# Modify script to use 5 layers:
# Set N_LAYERS = 5 at top of file
python batch_random_models.py

# Quick test with 100 models:
# Set N_MODELS = 100 at top of file
python batch_random_models.py
```

**Output**:
- `batch_random_models_ensemble.png` (ensemble statistics, 4 panels)
- `batch_random_models_parameters.png` (parameter distributions, adapts to N_LAYERS)

**Key Results**:
```
1000 models in ~7 seconds
Class-based API is ~1.2x faster for batch work
Maximum difference between APIs: 0.00e+00 (identical!)
Scales to any number of layers (tested 2-10 layers)
```

### 5. numerical_derivatives.py
**Finite difference derivatives workaround**

- Computes numerical Jacobian using finite differences
- Workaround for analytical derivative limitation
- Demonstrates perturbation method
- Includes sensitivity plots
- **Best for**: When you need derivatives for inversion

```python
times, jacobian, param_names = compute_numerical_jacobian(
    [100, 10, 50], [0, 30, 100], delta_percent=1.0
)
```

**Output**: `numerical_derivatives.png`

### 6. parallel_utils.py ⚡ NEW
**Parallel execution infrastructure**

- Multiprocessing-based parallel computation
- Automatic chunking and load balancing
- Worker initialization and library loading
- Configurable worker count and chunk size
- **Best for**: Processing thousands to millions of models

**Key functions**:
```python
from parallel_utils import parallel_tem1d

results = parallel_tem1d(
    resistivities_all, depths_all,
    n_workers=8, chunk_size=500
)
```

### 7. batch_random_models_parallel.py ⚡ NEW
**Comprehensive parallel benchmarking**

- Compares sequential vs parallel performance
- Chunk size optimization
- Correctness validation
- Performance visualization
- Scalability analysis
- **Best for**: Large-scale Monte Carlo studies, benchmarking

**Key Results** (128-core system):
```
1,000 models:   ~1.5x speedup (chunk_size=100)
10,000 models:  ~36x speedup, 7,121 models/s
1M models:      ~2.3 minutes (estimated)
```

**Configuration** (edit at top of file):
```python
N_MODELS = 1000      # Number of random models
N_LAYERS = 3         # Number of layers
N_WORKERS = None     # None = all cores, or specify (4, 8, 16, ...)
CHUNK_SIZE = 500     # Models per chunk
```

**Output**:
- `batch_parallel_benchmark.png` (6-panel performance analysis)

**Recommendations**:
- For <1000 models: Use chunk_size = 100
- For 10K-100K models: Use chunk_size = 500
- For >100K models: Use chunk_size = 1000-2000
- Set n_workers to physical core count on hyperthreaded systems

### 8. benchmark_speedup_final.py ⚡⚡ NEW
**Comprehensive speedup documentation (varying N)**

Documents parallel speedup across model counts: 100, 1K, 10K, 100K, 1M

- Systematic benchmarking from 100 to 1 million models
- Sequential time extrapolation for large N (saves time)
- 6-panel visualization showing time, speedup, throughput, efficiency
- Saves raw data for further analysis
- **Best for**: Performance documentation, system characterization

**Measured Results** (128-core system):
```
N = 100:         0.55× speedup (overhead dominates)
N = 1,000:       4.76× speedup, 1,000 models/s
N = 10,000:      36.4× speedup, 7,243 models/s
N = 100,000:     64.9× speedup, 11,273 models/s (peak throughput!)
N = 1,000,000:   52.0× speedup, 11,004 models/s in 1.5 minutes
```

**Key Findings**:
- Small batches (<1000): Sequential faster due to overhead
- Large batches (>10K): Massive parallel advantage (30-65× speedup)
- Peak throughput: ~11,000 models/s at N=100K
- 1 million models: 90 seconds parallel vs 1.3 hours sequential

**Output**:
- `speedup_benchmark_results.npz` (raw data: times, speedup, efficiency)
- `speedup_benchmark_plots.png` (6-panel visualization)

**Usage**:
```bash
python benchmark_speedup_final.py
# Runs all tests, creates plots, takes ~5 minutes
```

### 9. benchmark_speedup_cpu.py ⚡⚡ NEW
**CPU scaling benchmark (strong scaling, fixed N)**

Documents parallel speedup as a function of CPU count for fixed problem size.
Tests N_cpu = 1, 2, 4, 8, 16, 32, 64, 128 with N = 100,000 models.

- Strong scaling study (fixed problem size, varying workers)
- Demonstrates Amdahl's Law in action
- Identifies optimal CPU count for efficiency
- 5-panel visualization: time, speedup, efficiency, throughput, scaling
- **Best for**: System characterization, finding optimal worker count

**Measured Results** (128-core system, N=100,000):
```
N_cpu =   1:  541s (baseline)  100.0% efficiency    185 models/s
N_cpu =   2:  281s (1.93×)      96.4% efficiency    356 models/s
N_cpu =   4:  151s (3.59×)      89.7% efficiency    663 models/s
N_cpu =   8:   76s (7.10×)      88.7% efficiency  1,311 models/s
N_cpu =  16:   41s (13.1×)      82.0% efficiency  2,425 models/s
N_cpu =  32:   19s (29.2×)      91.4% efficiency  5,403 models/s
N_cpu =  64:   10s (52.5×) ⭐   82.0% efficiency  9,702 models/s (PEAK)
N_cpu = 128:   11s (50.2×)      39.2% efficiency  9,275 models/s
```

**Key Findings**:
- **Linear scaling up to 64 CPUs** (>80% efficiency)
- **Peak speedup: 52.5× at 64 CPUs** (likely 64 physical + 64 hyperthreaded)
- Beyond 64 CPUs: Diminishing returns (efficiency drops to 39%)
- **Serial fraction: 1.2%** (Amdahl's Law estimate - excellent!)
- 100K models: 9 minutes → 10 seconds with optimal CPU count

**Output**:
- `speedup_cpu_results.npz` (raw data for each CPU count)
- `speedup_cpu_plots.png` (6-panel strong scaling visualization)

**Usage**:
```bash
python benchmark_speedup_cpu.py
# Fixed N=100K, tests 1-128 CPUs, takes ~20 minutes
```

**Recommendation**:
- For this system: Use 32-64 CPUs for best efficiency/performance balance
- Beyond 64 CPUs: Hyperthreading overhead outweighs benefits

## Performance Benchmarks

### Sequential Performance
Based on running `batch_random_models.py`:

| API Style | Speed | Use Case |
|-----------|-------|----------|
| Functional | ~140 models/s | Quick one-off calculations |
| Class-based | ~170 models/s | Batch processing, parameter studies |

**Recommendation**: Use class-based API for batch processing (20-30% faster due to object reuse).

### Parallel Performance
Based on running `benchmark_speedup_final.py` on a 128-core system:

| Model Count | Sequential | Parallel | Speedup | Throughput | Efficiency |
|-------------|-----------|----------|---------|------------|------------|
| 100 models | 0.50s | 0.90s | 0.55× | 111 models/s | 0.4% |
| 1,000 models | 4.76s | 1.00s | 4.76× | 1,000 models/s | 3.7% |
| 10,000 models | 50.2s | 1.38s | 36.4× | 7,243 models/s | 28.4% |
| 100,000 models | 9.6min | 8.87s | **64.9×** | **11,273 models/s** | **50.7%** |
| 1,000,000 models | 1.31hr | 90.9s | 52.0× | 11,004 models/s | 40.6% |

**Key findings**:
- Optimal chunk size: 100 for N≤100K, 800 for N=1M (adaptive)
- Speedup scales with model count (more models = better efficiency)
- **Sweet spot: N=100K** - Best efficiency (50.7%) and peak throughput (11K/s)
- For small batches (N<1000), overhead dominates; sequential is faster
- For large batches (N>10K), parallel provides 30-65× speedup

**Time savings examples**:
- 100K models: 9.6min → 8.9s (saves 8.7 minutes)
- 1M models: 1.31hrs → 1.5min (saves 77 minutes)

**Recommendations**:
- Use sequential for N < 1,000 (parallel overhead not worth it)
- Use parallel for N ≥ 10,000 (massive speedup)
- Optimal settings vary by CPU count (see `benchmark_speedup_final.py`)

## Expected Runtime

| Example | Runtime | Models Computed |
|---------|---------|-----------------|
| basic_usage.py | ~1s | 1 |
| class_api.py | ~2s | 5 |
| plotting_demo.py | ~3s | 4 |
| batch_random_models.py | ~5s | 1,000 |
| numerical_derivatives.py | ~1s | 7 (base + 6 perturbed) |
| batch_random_models_parallel.py | ~4s | 1,000 (includes benchmarking) |
| batch_random_models_parallel.py | ~10s | 10,000 (128-core system) |
| benchmark_speedup_final.py | ~5min | 1,112,100 (all tests: 100+1K+10K+100K+1M) |
| benchmark_speedup_cpu.py | ~20min | 800,000 (100K × 8 CPU counts) |

## Requirements

All examples require:
- numpy
- matplotlib
- pytem1d (installed with `pip install -e .`)

## Tips

1. **Modify parameters**: All examples use reasonable defaults, but feel free to change resistivities, depths, etc.

2. **Save results**: Use `save_result()` to save computed responses:
   ```python
   from pytem1d import save_result
   save_result(result, "my_result.npz")
   ```

3. **Combine examples**: Mix and match code from different examples

4. **Scaling up**: `batch_random_models.py` can handle 10,000+ models by changing `N_MODELS`

5. **Reproducibility**: Examples use fixed random seeds (`np.random.seed(42)`)

## Troubleshooting

**Import error**: Make sure pytem1d is installed:
```bash
cd ../
pip install -e .
```

**Plotting issues**: If plots don't show, you may need to set the backend:
```python
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg'
```

**Slow performance**: First run may be slower due to library loading. Subsequent runs are faster.

## Contributing

Have an interesting use case? Consider contributing an example! Examples should:
- Be self-contained (one file)
- Include docstring explaining what it does
- Save output figures
- Run in < 30 seconds (or provide `N_MODELS` parameter to scale)
