# TEM1D CPU Scaling Benchmark Summary (Strong Scaling Study)

## Overview

This document summarizes the CPU scaling benchmark that tests parallel performance as a function of the number of workers for a **fixed problem size**. This is known as a "strong scaling" study and is critical for understanding how efficiently the code uses additional CPUs.

## Benchmark Configuration

- **Problem size**: N = 100,000 models (FIXED for all tests)
- **Layer configuration**: 3-layer models
- **CPU counts tested**: 1, 2, 4, 8, 16, 32, 64, 128
- **System**: 128-core processor (likely 64 physical + 64 hyperthreaded)
- **Resistivity range**: 1-1000 Ω·m (log-uniform distribution)
- **Depth range**: 0-220 m (automatically generated)

## Results

### Performance Summary Table

| N_cpu | Time | Speedup | Efficiency | Throughput | Chunk Size |
|-------|------|---------|------------|------------|------------|
| **1** | 541.14s (9.0m) | 1.00× | 100.0% | 185 models/s | 100,000 |
| **2** | 280.70s (4.7m) | 1.93× | 96.4% | 356 models/s | 5,000 |
| **4** | 150.89s (2.5m) | 3.59× | 89.7% | 663 models/s | 2,500 |
| **8** | 76.25s (1.3m) | 7.10× | 88.7% | 1,311 models/s | 1,250 |
| **16** | 41.24s | 13.12× | 82.0% | 2,425 models/s | 650 |
| **32** | 18.51s | 29.24× | **91.4%** | 5,403 models/s | 300 |
| **64** | 10.31s | **52.50×** ⭐ | 82.0% | **9,702 models/s** ⭐ | 150 |
| **128** | 10.78s | 50.19× | 39.2% | 9,275 models/s | 100 |

### Key Performance Metrics

- **Peak Speedup**: 52.50× at 64 CPUs
- **Peak Throughput**: 9,702 models/second at 64 CPUs
- **Best Efficiency Range**: 2-32 CPUs (>88% efficiency)
- **Linear Scaling Region**: Up to 64 CPUs (>80% efficiency)
- **Time Reduction**: 541s → 10.3s (9 minutes → 10 seconds)
- **Estimated Serial Fraction**: 1.2% (from Amdahl's Law)

## Analysis

### Scaling Regions

The benchmark reveals distinct scaling regions:

#### 1. Near-Perfect Linear Scaling (1-8 CPUs)
- Efficiency: 88.7-100%
- Speedup: Nearly ideal (7.10× with 8 CPUs vs ideal 8.0×)
- Behavior: Overhead is minimal, workers are fully utilized
- **Recommendation**: Ideal range for smaller systems

#### 2. Good Linear Scaling (16-32 CPUs)
- Efficiency: 82-91%
- Speedup: 13-29× (good but sub-linear)
- Behavior: Some overhead, but still excellent scaling
- **Recommendation**: Optimal for workstations/small servers

#### 3. Sublinear Scaling (64 CPUs)
- Efficiency: 82%
- Speedup: 52.5× (peak performance)
- Behavior: Best absolute performance despite lower efficiency
- **Recommendation**: Best for large-scale production runs

#### 4. Hyperthreading Region (128 CPUs)
- Efficiency: 39% (drops significantly)
- Speedup: 50.2× (slightly worse than 64 CPUs!)
- Behavior: Hyperthreading overhead outweighs benefits
- **Observation**: System likely has 64 physical cores + 64 HT cores

### Why Does Efficiency Drop?

**Factors limiting scaling beyond 64 CPUs**:

1. **Hyperthreading Overhead**
   - 64 physical cores + 64 logical cores (hyperthreading)
   - Logical cores share execution resources
   - Overhead from managing 128 processes

2. **Amdahl's Law**
   - Serial fraction ≈ 1.2% (excellent, but still limits speedup)
   - Maximum theoretical speedup ≈ 1/(0.012) ≈ 83×
   - At 128 CPUs, already approaching theoretical limit

3. **Memory Bandwidth**
   - All 128 cores compete for memory bus
   - Memory bandwidth saturates before CPU capacity
   - Cache coherence overhead increases with core count

4. **Process Management Overhead**
   - Creating/managing 128 processes has overhead
   - Inter-process communication costs
   - Context switching overhead

### Amdahl's Law Analysis

Using the formula: `f = (1/S - 1/N) / (1 - 1/N)`

Where:
- f = serial fraction
- S = speedup (50.19)
- N = number of processors (128)

**Result**: f ≈ 1.2%

This means:
- **98.8% of the code is perfectly parallelizable** (excellent!)
- **1.2% must run sequentially** (model generation, result collection, etc.)
- **Maximum theoretical speedup**: ~83× (at infinite CPUs)

### Optimal CPU Count

Based on the benchmark data:

**For Maximum Throughput**:
- Use **64 CPUs**
- Achieves 9,702 models/s
- Speedup: 52.5×

**For Best Efficiency**:
- Use **32 CPUs** if efficiency matters
- Achieves 91.4% efficiency
- Speedup: 29.2×
- Throughput: 5,403 models/s

**For Budget/Shared Systems**:
- Use **8-16 CPUs**
- Efficiency: 82-89%
- Still good speedup (7-13×)

## Comparison: Ideal vs Measured Speedup

| N_cpu | Ideal Speedup | Measured Speedup | Efficiency |
|-------|---------------|------------------|------------|
| 1 | 1.0× | 1.00× | 100.0% |
| 2 | 2.0× | 1.93× | 96.4% |
| 4 | 4.0× | 3.59× | 89.7% |
| 8 | 8.0× | 7.10× | 88.7% |
| 16 | 16.0× | 13.12× | 82.0% |
| 32 | 32.0× | 29.24× | 91.4% |
| 64 | 64.0× | 52.50× | 82.0% |
| 128 | 128.0× | 50.19× | 39.2% |

**Observations**:
- Nearly ideal up to 8 CPUs
- 32 CPUs shows surprisingly good efficiency (91.4%)
- 64 CPUs: Best absolute performance
- 128 CPUs: Hyperthreading overhead dominates

## Throughput Analysis

**Throughput scaling**:
- 1 CPU: 185 models/s (baseline)
- 64 CPUs: 9,702 models/s (**52.5× faster**)
- 128 CPUs: 9,275 models/s (slightly slower than 64!)

**Key insight**: Beyond physical core count (64), adding logical cores (hyperthreading) **decreases** performance due to overhead.

## Chunk Size Adaptation

The adaptive chunking algorithm adjusts automatically:

| N_cpu | Chunk Size | Chunks | Chunks per Worker |
|-------|------------|--------|-------------------|
| 1 | 100,000 | 1 | 1 |
| 2 | 5,000 | 20 | 10 |
| 4 | 2,500 | 40 | 10 |
| 8 | 1,250 | 80 | 10 |
| 16 | 650 | 154 | ~10 |
| 32 | 300 | 334 | ~10 |
| 64 | 150 | 667 | ~10 |
| 128 | 100 | 1,000 | ~8 |

**Strategy**: Maintain ~10 chunks per worker for good load balancing.

## Real-World Impact

### Time Savings Examples

For N = 100,000 models:

| N_cpu | Time | Time Saved vs Sequential |
|-------|------|--------------------------|
| 1 | 9.0 minutes | - (baseline) |
| 8 | 1.3 minutes | 7.7 minutes (86% faster) |
| 32 | 18.5 seconds | 8.7 minutes (96% faster) |
| 64 | 10.3 seconds | 8.8 minutes (98% faster) |

### Scaling to Larger Problems

If we had N = 1,000,000 models (10× larger):

**Estimated times** (based on throughput):
- 1 CPU: ~90 minutes (1.5 hours)
- 8 CPUs: ~13 minutes
- 32 CPUs: ~3 minutes
- 64 CPUs: ~1.7 minutes (103 seconds)

**Time saved**: 88 minutes by using 64 CPUs vs 1 CPU

## Recommendations by System Size

### Desktop (4-8 cores)
- **Use**: All available cores
- **Expected speedup**: 3.5-7×
- **Efficiency**: 88-90%
- **Best use**: Small to medium batches (N < 100K)

### Workstation (16-32 cores)
- **Use**: All available cores
- **Expected speedup**: 13-29×
- **Efficiency**: 82-91%
- **Best use**: Large batches (N = 100K-1M)

### Server (64+ physical cores)
- **Use**: Physical cores only (disable hyperthreading or set n_workers=64)
- **Expected speedup**: 50-52×
- **Efficiency**: 82%
- **Best use**: Very large batches (N > 1M)
- **Avoid**: Using all logical cores (128) - worse than 64!

### HPC Cluster
- **Use**: Multiple nodes with distributed computing (Dask/Ray)
- **Expected speedup**: Linear across nodes (if network is fast)
- **Best use**: Massive ensembles (N > 10M)

## Visualization

The benchmark creates `speedup_cpu_plots.png` with 5 panels (2×3 layout):

1. **Panel A**: Execution time vs N_cpu (log scale)
   - Shows diminishing returns clearly

2. **Panel B**: Speedup vs N_cpu
   - Compares measured to ideal linear speedup
   - Shows plateau around 64 CPUs

3. **Panel C**: Parallel efficiency vs N_cpu
   - Shows efficiency drop beyond 64 CPUs
   - Reference lines at 100%, 80%, 50%

4. **Panel D**: Throughput vs N_cpu
   - Models per second
   - Shows saturation at 64 CPUs

5. **Panel E**: Scaling efficiency vs N_cpu
   - Speedup as percentage of ideal
   - Highlights deviation from linear

**Figure title** displays key results:
- Problem size (N=100,000 models)
- Peak speedup (52.5× at 64 CPUs)
- Maximum throughput (9,702 models/s)

## Conclusions

1. **Excellent parallel efficiency**
   - Serial fraction of only 1.2% is outstanding
   - 98.8% of computation is fully parallelizable

2. **Linear scaling up to 64 CPUs**
   - Efficiency >80% up to 64 cores
   - Ideal for large-scale production use

3. **Hyperthreading not beneficial**
   - 128 logical cores perform worse than 64 physical
   - Overhead outweighs any benefit
   - **Recommendation**: Disable HT or cap workers at 64

4. **Sweet spot: 32-64 CPUs**
   - 32 CPUs: Best efficiency (91.4%)
   - 64 CPUs: Best absolute performance (52.5×)

5. **Massive time savings possible**
   - 100K models: 9 minutes → 10 seconds (98% reduction)
   - 1M models: 1.5 hours → 1.7 minutes (98% reduction)

## Comparison with Other Studies

This benchmark demonstrates **strong scaling**:
- Fixed problem size (N = 100,000)
- Variable number of workers
- Measures parallel efficiency

Complements `benchmark_speedup_final.py` which shows **weak scaling**:
- Fixed number of workers (128)
- Variable problem size (N = 100 to 1M)
- Measures throughput scaling

Together, these benchmarks provide complete characterization of parallel performance.

## Future Optimizations

Potential improvements beyond current performance:

1. **NUMA-aware scheduling**: Pin processes to specific NUMA nodes
2. **GPU acceleration**: Offload Hankel transforms to GPU
3. **Distributed computing**: Multi-node parallelism with Dask/Ray
4. **Hybrid MPI+OpenMP**: Combine process and thread parallelism
5. **Memory pinning**: Reduce cache misses with memory affinity

## References

- Script: `benchmark_speedup_cpu.py`
- Data: `speedup_cpu_results.npz`
- Plots: `speedup_cpu_plots.png`
- Related: `benchmark_speedup_final.py` (weak scaling study)
