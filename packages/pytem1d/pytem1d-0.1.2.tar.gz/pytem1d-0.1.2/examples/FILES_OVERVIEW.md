# Python Examples Directory - File Overview

This directory contains examples demonstrating various features of the pytem1d package, including parallel processing capabilities.

## Core Examples

### Basic Usage
- `basic_usage.py` (1.5K) - Simple functional API demonstration
- `class_api.py` (2.7K) - Advanced class-based API demonstration
- `plotting_demo.py` (3.8K) - Comprehensive visualization demonstration
- `numerical_derivatives.py` (4.2K) - Finite difference derivatives workaround

### Batch Processing
- `batch_random_models.py` (16K) - Sequential batch processing with configurable layers
- `batch_random_models_parallel.py` (15K) - Parallel vs sequential comparison

### Parallel Processing Infrastructure
- `parallel_utils.py` (9.7K) - Reusable parallel execution utilities
  - `parallel_tem1d()` - Main parallel execution function
  - `adaptive_chunk_size()` - Automatic chunk size optimization
  - `worker_init()` - Worker process initialization

### Performance Benchmarks
- `benchmark_speedup_final.py` (16K) - Weak scaling study (varying N, fixed CPUs)
  - Tests N = 100, 1K, 10K, 100K, 1M models
  - Runtime: ~5 minutes
  - Output: `speedup_benchmark_plots.png`, `speedup_benchmark_results.npz`

- `benchmark_speedup_cpu.py` (14K) - Strong scaling study (fixed N, varying CPUs)
  - Tests N_cpu = 1, 2, 4, 8, 16, 32, 64, 128
  - Fixed N = 100,000 models (configurable)
  - Runtime: ~20 minutes
  - Output: `speedup_cpu_plots.png`, `speedup_cpu_results.npz`

## Documentation

### User Guides
- `README.md` (13K) - Main examples documentation
  - Quick start guide
  - Example descriptions
  - Performance benchmarks
  - Expected runtimes

- `PARALLEL_PROCESSING.md` (15K) - Comprehensive parallel processing guide
  - Architecture explanation
  - Performance characteristics
  - Optimization guide
  - Usage examples
  - Troubleshooting

### Benchmark Documentation
- `BENCHMARK_OVERVIEW.md` (8.0K) - Overview of all benchmarking scripts
  - Comparison of weak vs strong scaling
  - When to use which benchmark
  - Key findings summary

- `SPEEDUP_BENCHMARK_SUMMARY.md` (8.2K) - Weak scaling results and analysis
  - Problem size scaling (N = 100 to 1M)
  - Performance metrics
  - Recommendations

- `CPU_SCALING_SUMMARY.md` (9.9K) - Strong scaling results and analysis
  - CPU count scaling (1 to 128 CPUs)
  - Amdahl's Law analysis
  - Optimal CPU recommendations

- `BATCH_EXAMPLES.md` (6.3K) - Guide for configurable layer batch processing
  - Layer count configuration
  - Use cases by layer count
  - Runtime examples

## Generated Files (Not in Repository)

When you run the examples, they will generate:

### Plots (*.png)
- `basic_tem_response.png` - From basic_usage.py
- `class_api_*.png` - From class_api.py
- `plotting_demo_all.png` - From plotting_demo.py
- `derivatives_heatmap.png` - From plotting_demo.py
- `numerical_derivatives.png` - From numerical_derivatives.py
- `batch_random_models_ensemble.png` - From batch_random_models.py
- `batch_random_models_parameters.png` - From batch_random_models.py
- `batch_parallel_benchmark.png` - From batch_random_models_parallel.py
- `speedup_benchmark_plots.png` - From benchmark_speedup_final.py
- `speedup_cpu_plots.png` - From benchmark_speedup_cpu.py

### Data (*.npz)
- `speedup_benchmark_results.npz` - Raw data from benchmark_speedup_final.py
- `speedup_cpu_results.npz` - Raw data from benchmark_speedup_cpu.py

### Logs (*.log)
- Various log files from benchmark runs

**Note**: Generated files are excluded from version control (add to .gitignore)

## File Organization

```
python/examples/
├── Core Examples (5 files)
│   ├── basic_usage.py
│   ├── class_api.py
│   ├── plotting_demo.py
│   ├── numerical_derivatives.py
│   └── batch_random_models.py
│
├── Parallel Processing (4 files)
│   ├── parallel_utils.py
│   ├── batch_random_models_parallel.py
│   ├── benchmark_speedup_final.py
│   └── benchmark_speedup_cpu.py
│
└── Documentation (6 files)
    ├── README.md
    ├── PARALLEL_PROCESSING.md
    ├── BENCHMARK_OVERVIEW.md
    ├── SPEEDUP_BENCHMARK_SUMMARY.md
    ├── CPU_SCALING_SUMMARY.md
    └── BATCH_EXAMPLES.md
```

## Quick Start

```bash
# Basic examples
python basic_usage.py
python class_api.py

# Batch processing
python batch_random_models.py

# Parallel processing
python batch_random_models_parallel.py

# Benchmarking
python benchmark_speedup_final.py      # ~5 min
python benchmark_speedup_cpu.py        # ~20 min
```

## Total File Count

- **Python scripts**: 9 files (82K total)
- **Documentation**: 6 files (60K total)
- **Total**: 15 files (142K total)

All files are production-ready and documented.
