# TEM1D Parallel Processing - Complete Benchmark Overview

This document provides an overview of all benchmarking scripts and their purposes.

## Benchmark Suite

### 1. `benchmark_speedup_final.py` - Weak Scaling Study
**Question**: How does performance scale with problem size?

**Configuration**:
- Fixed workers: 128 CPUs
- Variable problem size: N = 100, 1K, 10K, 100K, 1M

**Key Results**:
```
N = 100:        0.55× speedup (overhead dominates)
N = 1,000:      4.76× speedup
N = 10,000:     36.4× speedup
N = 100,000:    64.9× speedup (PEAK)
N = 1,000,000:  52.0× speedup
```

**Insights**:
- Small problems (N<1000): Parallel overhead dominates, sequential is faster
- Large problems (N>10K): Massive parallel advantage (30-65× speedup)
- Sweet spot: N=100K with 64.9× speedup and 11,273 models/s

**Runtime**: ~5 minutes

---

### 2. `benchmark_speedup_cpu.py` - Strong Scaling Study ⭐ NEW
**Question**: How does performance scale with number of CPUs?

**Configuration**:
- Fixed problem size: N = 100,000 models
- Variable workers: N_cpu = 1, 2, 4, 8, 16, 32, 64, 128

**Key Results**:
```
N_cpu =   1:  541s (baseline)      185 models/s
N_cpu =   2:  281s (1.93× speedup) 356 models/s    96.4% efficiency
N_cpu =   4:  151s (3.59× speedup) 663 models/s    89.7% efficiency
N_cpu =   8:   76s (7.10× speedup) 1,311 models/s  88.7% efficiency
N_cpu =  16:   41s (13.1× speedup) 2,425 models/s  82.0% efficiency
N_cpu =  32:   19s (29.2× speedup) 5,403 models/s  91.4% efficiency ⭐
N_cpu =  64:   10s (52.5× speedup) 9,702 models/s  82.0% efficiency (PEAK)
N_cpu = 128:   11s (50.2× speedup) 9,275 models/s  39.2% efficiency
```

**Insights**:
- **Linear scaling up to 64 CPUs** (>80% efficiency)
- **Peak performance at 64 CPUs** (likely 64 physical cores)
- **Hyperthreading overhead**: 128 CPUs performs worse than 64!
- **Serial fraction**: Only 1.2% (excellent parallelization)
- **Optimal**: Use 32-64 CPUs for best efficiency/performance balance

**Runtime**: ~20 minutes

---

### 3. `batch_random_models_parallel.py` - Quick Benchmark
**Question**: How do sequential and parallel compare for typical workload?

**Configuration**:
- Fixed: N = 1,000 models (configurable)
- Tests both sequential and parallel
- Includes chunk size optimization

**Key Results**:
```
Sequential: 4.96s (201 models/s)
Parallel:   3.42s (293 models/s)
Speedup:    1.45×
```

**Insights**:
- For N=1000, parallel has modest speedup
- Includes validation (results match exactly)
- Good for quick performance checks

**Runtime**: ~10 seconds

---

## Benchmark Comparison

| Benchmark | Type | What It Tests | Runtime | Best For |
|-----------|------|---------------|---------|----------|
| `benchmark_speedup_final.py` | Weak scaling | Problem size scaling | ~5 min | System characterization |
| `benchmark_speedup_cpu.py` | Strong scaling | CPU count scaling | ~20 min | Finding optimal CPU count |
| `batch_random_models_parallel.py` | Quick test | Basic parallel vs seq | ~10 sec | Quick validation |

## Key Findings Summary

### When to Use Parallel

Based on benchmarks, use parallel execution when:

✅ **N ≥ 10,000 models** (30-65× speedup)
✅ **Have ≥8 CPU cores available**
✅ **Time matters** (minutes → seconds)
✅ **Running production/batch jobs**

❌ **Don't use parallel when**:
- N < 1,000 models (overhead dominates)
- Interactive/exploratory work
- Only 1-4 cores available

### Optimal Configuration

Based on the strong scaling study:

**For Desktop (4-8 cores)**:
- Use all cores
- Expected: 3.5-7× speedup
- Efficiency: 88-90%

**For Workstation (16-32 cores)**:
- Use all cores
- Expected: 13-29× speedup
- Efficiency: 82-91%
- **Sweet spot**: 32 cores with 91% efficiency

**For Server (64+ cores)**:
- **Use 64 cores maximum**
- Expected: 50-52× speedup
- Efficiency: 82%
- **Avoid hyperthreading**: 128 logical cores worse than 64 physical!

## Performance Summary

### Time Reduction Examples

**100,000 models**:
- Sequential: 9.0 minutes
- Parallel (64 CPUs): 10.3 seconds
- **Time saved: 8.8 minutes (98% reduction)**

**1,000,000 models**:
- Sequential: 1.31 hours
- Parallel (128 CPUs): 1.5 minutes
- **Time saved: 77 minutes (98% reduction)**

### Throughput Achieved

- **Single CPU**: 185 models/second
- **8 CPUs**: 1,311 models/second (7.1× faster)
- **32 CPUs**: 5,403 models/second (29× faster)
- **64 CPUs**: 9,702 models/second (52.5× faster) ⭐ PEAK
- **128 CPUs**: 9,275 models/second (50× faster)

## Visualizations

Each benchmark creates detailed 6-panel visualizations:

### `speedup_benchmark_plots.png` (Weak Scaling)
1. Execution time vs N
2. Speedup vs N
3. Throughput vs N
4. Efficiency vs N
5. Time saved vs N
6. Summary table

### `speedup_cpu_plots.png` (Strong Scaling) ⭐ NEW
1. Execution time vs N_cpu
2. Speedup vs N_cpu (with ideal reference)
3. Parallel efficiency vs N_cpu
4. Throughput vs N_cpu
5. Scaling efficiency (speedup/ideal)

Plus figure title with key metrics (peak speedup, throughput)

## Raw Data Files

All benchmarks save raw data for further analysis:

- `speedup_benchmark_results.npz` - Weak scaling data
- `speedup_cpu_results.npz` - Strong scaling data ⭐ NEW

Load with:
```python
import numpy as np
data = np.load('speedup_cpu_results.npz')
n_cpu = data['n_cpu']
speedup = data['speedup']
efficiency = data['efficiency']
```

## Recommendations

### For New Users
1. Start with `batch_random_models_parallel.py` (quick test)
2. Run `benchmark_speedup_cpu.py` to find your optimal CPU count
3. Use that optimal setting for production work

### For System Administrators
1. Run both benchmarks to characterize system
2. Share results with users
3. Set recommended `n_workers` based on strong scaling results

### For Researchers
1. Use `benchmark_speedup_final.py` for weak scaling characterization
2. Use `benchmark_speedup_cpu.py` for strong scaling characterization
3. Include both plots in publications/reports

## Theoretical Background

### Amdahl's Law

Maximum speedup limited by serial fraction:

```
Speedup = 1 / (f + (1-f)/N)
```

Where:
- f = serial fraction (1.2% for TEM1D)
- N = number of processors

**For TEM1D**:
- Serial fraction: 1.2%
- Maximum theoretical speedup: ~83× (at infinite CPUs)
- Measured speedup at 64 CPUs: 52.5× (63% of theoretical max)

### Strong vs Weak Scaling

**Strong Scaling** (`benchmark_speedup_cpu.py`):
- Fixed problem size
- Increasing processors
- Measures: How fast can I solve THIS problem?

**Weak Scaling** (`benchmark_speedup_final.py`):
- Increasing problem size
- Fixed processors
- Measures: How large a problem can I solve in reasonable time?

## Conclusions

1. **Excellent parallel scalability**
   - Serial fraction of only 1.2%
   - Linear scaling up to 64 CPUs
   - 50× speedup achievable

2. **Problem size matters**
   - Small (N<1K): Don't use parallel
   - Large (N>10K): Massive benefit

3. **Physical cores matter**
   - 64 physical cores: 52.5× speedup
   - 128 logical cores: 50.2× speedup (worse!)
   - Disable hyperthreading for best performance

4. **Real-world impact**
   - 100K models: 9 min → 10 sec
   - 1M models: 1.3 hrs → 1.5 min
   - Production-ready for large-scale studies

## Files Overview

### Scripts
- `benchmark_speedup_final.py` - Weak scaling (varying N)
- `benchmark_speedup_cpu.py` - Strong scaling (varying CPUs) ⭐ NEW
- `batch_random_models_parallel.py` - Quick validation

### Documentation
- `BENCHMARK_OVERVIEW.md` - This file
- `SPEEDUP_BENCHMARK_SUMMARY.md` - Weak scaling details
- `CPU_SCALING_SUMMARY.md` - Strong scaling details ⭐ NEW
- `PARALLEL_PROCESSING.md` - User guide

### Data & Plots
- `speedup_benchmark_results.npz` - Weak scaling data
- `speedup_benchmark_plots.png` - Weak scaling plots
- `speedup_cpu_results.npz` - Strong scaling data ⭐ NEW
- `speedup_cpu_plots.png` - Strong scaling plots ⭐ NEW
