#!/usr/bin/env python3
"""
Parallel batch processing with comprehensive benchmarking

This example demonstrates parallel computation of TEM1D forward responses and
compares performance against sequential execution. Designed to scale from
thousands to millions of models.

Features:
- Sequential baseline for comparison
- Parallel execution using multiprocessing
- Correctness validation (parallel vs sequential)
- Chunk size optimization
- Performance visualization
- Scalability analysis

Usage:
    # Quick test with 1000 models
    python batch_random_models_parallel.py

    # To test different scales, modify N_MODELS below:
    # N_MODELS = 100      # Quick correctness check (~1s)
    # N_MODELS = 1000     # Standard test (~7s sequential)
    # N_MODELS = 10000    # Stress test (~70s sequential)
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from multiprocessing import cpu_count
from pytem1d import run_tem1d
from parallel_utils import parallel_tem1d, adaptive_chunk_size

# ============================================================================
# CONFIGURATION
# ============================================================================
N_MODELS = 1000      # Number of random models (100, 1000, 10000, 100000)
N_LAYERS = 3         # Number of layers
N_WORKERS = None     # None = use all cores, or specify (e.g., 4, 8, 16)
CHUNK_SIZE = 500     # Models per chunk (will also test optimal size)
RANDOM_SEED = 42     # For reproducibility

# Set random seed
np.random.seed(RANDOM_SEED)

# Determine actual worker count
if N_WORKERS is None:
    N_WORKERS = cpu_count()

print("=" * 70)
print(f"Parallel TEM1D Batch Processing Benchmark")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Models: {N_MODELS}")
print(f"  Layers: {N_LAYERS}")
print(f"  Workers: {N_WORKERS}")
print(f"  Chunk size: {CHUNK_SIZE}")
print(f"  CPU cores available: {cpu_count()}")

# ============================================================================
# Generate random N-layer models
# ============================================================================
print(f"\n{'-'*70}")
print(f"Generating Random Models")
print(f"{'-'*70}")

# Resistivity ranges (Ohm-m) - log-uniform distribution
rho_min, rho_max = 1, 1000
resistivities_all = 10 ** np.random.uniform(
    np.log10(rho_min), np.log10(rho_max), size=(N_MODELS, N_LAYERS)
)

# Layer depths (m) - top layer is always at 0
depths_all = np.zeros((N_MODELS, N_LAYERS))

# Generate increasing depths for each layer interface
if N_LAYERS > 1:
    max_depth = 200.0
    for i in range(1, N_LAYERS):
        depth_min = (i - 1) * max_depth / (N_LAYERS - 1) + 10
        depth_max = i * max_depth / (N_LAYERS - 1) + 20
        depths_all[:, i] = np.random.uniform(depth_min, depth_max, N_MODELS)

    # Ensure depths are strictly increasing
    depths_all = np.sort(depths_all, axis=1)
    depths_all[:, 0] = 0  # First layer always at surface

print(f"✓ Generated {N_MODELS} random {N_LAYERS}-layer models")
print(f"  Resistivity range: {rho_min}-{rho_max} Ω·m")

# ============================================================================
# Sequential Baseline
# ============================================================================
print(f"\n{'-'*70}")
print(f"Sequential Processing (Baseline)")
print(f"{'-'*70}")

results_sequential = []
start_time = time.time()

# Use a subset for very large runs to save time
n_sequential = min(N_MODELS, 5000)  # Cap at 5000 for time savings
print(f"Computing {n_sequential} models sequentially...")

for i in range(n_sequential):
    if (i + 1) % 500 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed
        eta = (n_sequential - i - 1) / rate
        print(f"  Progress: {i+1}/{n_sequential} ({rate:.1f} models/s, ETA: {eta:.1f}s)")

    result = run_tem1d(
        resistivities=resistivities_all[i],
        depths=depths_all[i],
    )
    results_sequential.append(result)

time_sequential = time.time() - start_time
rate_sequential = n_sequential / time_sequential

print(f"\n✓ Sequential completed")
print(f"  Total time: {time_sequential:.2f}s")
print(f"  Throughput: {rate_sequential:.1f} models/s")

# ============================================================================
# Parallel Execution
# ============================================================================
print(f"\n{'-'*70}")
print(f"Parallel Processing")
print(f"{'-'*70}")

start_time = time.time()
results_parallel = parallel_tem1d(
    resistivities_all,
    depths_all,
    n_workers=N_WORKERS,
    chunk_size=CHUNK_SIZE,
    verbose=True,
)
time_parallel = time.time() - start_time
rate_parallel = N_MODELS / time_parallel

print(f"\n✓ Parallel completed")
print(f"  Total time: {time_parallel:.2f}s")
print(f"  Throughput: {rate_parallel:.1f} models/s")

# ============================================================================
# Performance Analysis
# ============================================================================
print(f"\n{'='*70}")
print(f"Performance Summary")
print(f"{'='*70}")

# Compute speedup based on comparable model counts
if n_sequential == N_MODELS:
    speedup = time_sequential / time_parallel
    efficiency = speedup / N_WORKERS * 100
    print(f"Sequential:   {time_sequential:8.2f}s  ({rate_sequential:6.1f} models/s)")
    print(f"Parallel:     {time_parallel:8.2f}s  ({rate_parallel:6.1f} models/s)")
    print(f"Speedup:      {speedup:8.2f}x")
    print(f"Efficiency:   {efficiency:8.1f}% (ideal: 100%)")
else:
    # Estimate sequential time for full batch
    estimated_seq_time = time_sequential * (N_MODELS / n_sequential)
    estimated_speedup = estimated_seq_time / time_parallel
    efficiency = estimated_speedup / N_WORKERS * 100
    print(f"Sequential:   {time_sequential:8.2f}s for {n_sequential} models ({rate_sequential:6.1f} models/s)")
    print(f"              {estimated_seq_time:8.2f}s estimated for {N_MODELS} models")
    print(f"Parallel:     {time_parallel:8.2f}s  ({rate_parallel:6.1f} models/s)")
    print(f"Speedup:      {estimated_speedup:8.2f}x (estimated)")
    print(f"Efficiency:   {efficiency:8.1f}% (ideal: 100%)")

print(f"Workers:      {N_WORKERS:8d}")
print(f"Chunk size:   {CHUNK_SIZE:8d}")

# ============================================================================
# Validation - Correctness Check
# ============================================================================
print(f"\n{'-'*70}")
print(f"Validation")
print(f"{'-'*70}")

# Compare random samples from sequential and parallel results
n_samples = min(10, n_sequential)
sample_indices = np.random.choice(n_sequential, size=n_samples, replace=False)

max_diff = 0
for idx in sample_indices:
    diff = np.abs(
        results_sequential[idx].responses - results_parallel[idx].responses
    ).max()
    max_diff = max(max_diff, diff)

print(f"Comparing {n_samples} random samples:")
print(f"  Maximum difference: {max_diff:.2e}")
if max_diff < 1e-10:
    print(f"  ✓ Results match (difference < 1e-10)")
else:
    print(f"  ✗ Results differ significantly!")

# ============================================================================
# Chunk Size Optimization
# ============================================================================
print(f"\n{'-'*70}")
print(f"Chunk Size Optimization")
print(f"{'-'*70}")

# Test different chunk sizes on a subset of models
n_test = min(2000, N_MODELS)
chunk_sizes_to_test = [100, 250, 500, 1000, 2000]
chunk_times = []

print(f"Testing different chunk sizes on {n_test} models...")

for cs in chunk_sizes_to_test:
    start = time.time()
    _ = parallel_tem1d(
        resistivities_all[:n_test],
        depths_all[:n_test],
        n_workers=N_WORKERS,
        chunk_size=cs,
        verbose=False,
    )
    elapsed = time.time() - start
    chunk_times.append(elapsed)
    throughput = n_test / elapsed
    print(f"  Chunk size {cs:4d}: {elapsed:6.2f}s ({throughput:6.1f} models/s)")

optimal_idx = np.argmin(chunk_times)
optimal_chunk = chunk_sizes_to_test[optimal_idx]
print(f"\n✓ Optimal chunk size: {optimal_chunk} ({chunk_times[optimal_idx]:.2f}s)")

# Compare with adaptive chunk size recommendation
adaptive_cs = adaptive_chunk_size(N_MODELS, N_WORKERS)
print(f"  Adaptive recommendation: {adaptive_cs}")

# ============================================================================
# Visualization
# ============================================================================
print(f"\n{'-'*70}")
print(f"Creating Visualizations")
print(f"{'-'*70}")

fig = plt.figure(figsize=(16, 10))

# ===== Plot 1: Performance Comparison Bar Chart =====
ax1 = plt.subplot(2, 3, 1)
methods = ['Sequential', 'Parallel']
if n_sequential == N_MODELS:
    times = [time_sequential, time_parallel]
    rates = [rate_sequential, rate_parallel]
else:
    times = [estimated_seq_time, time_parallel]
    rates = [rate_sequential, rate_parallel]

colors = ['#3498db', '#2ecc71']
bars = ax1.bar(methods, times, color=colors, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Time (s)', fontsize=11)
ax1.set_title(f'Execution Time Comparison\n({N_MODELS} models)', fontsize=12, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

# Add time labels on bars
for bar, t in zip(bars, times):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{t:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')

# ===== Plot 2: Throughput Comparison =====
ax2 = plt.subplot(2, 3, 2)
bars = ax2.bar(methods, rates, color=colors, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Throughput (models/s)', fontsize=11)
ax2.set_title('Processing Throughput', fontsize=12, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# Add rate labels
for bar, r in zip(bars, rates):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{r:.0f}/s', ha='center', va='bottom', fontsize=10, fontweight='bold')

# ===== Plot 3: Speedup and Efficiency =====
ax3 = plt.subplot(2, 3, 3)
if n_sequential == N_MODELS:
    speedup_val = speedup
else:
    speedup_val = estimated_speedup
efficiency_val = efficiency

x = ['Speedup\n(vs Sequential)', 'Efficiency\n(% of ideal)']
y = [speedup_val, efficiency_val]
colors_perf = ['#e74c3c', '#9b59b6']
bars = ax3.bar(x, y, color=colors_perf, edgecolor='black', linewidth=1.5)
ax3.set_title('Parallel Performance Metrics', fontsize=12, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)

# Add ideal lines
ax3.axhline(y=N_WORKERS, color='gray', linestyle='--', linewidth=1, alpha=0.5, label=f'Ideal speedup ({N_WORKERS}x)')
ax3.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax3.legend(fontsize=8)

# Add value labels
for bar, val in zip(bars, y):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# ===== Plot 4: Chunk Size Performance =====
ax4 = plt.subplot(2, 3, 4)
throughputs = [n_test / t for t in chunk_times]
ax4.plot(chunk_sizes_to_test, throughputs, 'o-', linewidth=2, markersize=8, color='#16a085')
ax4.axvline(optimal_chunk, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Optimal: {optimal_chunk}')
ax4.set_xlabel('Chunk Size', fontsize=11)
ax4.set_ylabel('Throughput (models/s)', fontsize=11)
ax4.set_title('Chunk Size Optimization', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.legend()

# ===== Plot 5: Sample Response Comparison =====
ax5 = plt.subplot(2, 3, 5)
# Plot a few responses from both methods to visually verify agreement
n_plot = min(5, len(results_sequential))
for i in range(n_plot):
    result_seq = results_sequential[i]
    result_par = results_parallel[i]
    ax5.loglog(result_seq.times * 1e3, np.abs(result_seq.responses),
               'o', markersize=4, alpha=0.6, label=f'Model {i+1} (seq)' if i == 0 else '')
    ax5.loglog(result_par.times * 1e3, np.abs(result_par.responses),
               '-', linewidth=1.5, alpha=0.8)

ax5.set_xlabel('Time (ms)', fontsize=11)
ax5.set_ylabel('|dB/dt| (V/A·m²)', fontsize=11)
ax5.set_title('Response Validation (Sequential vs Parallel)', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.legend(['Sequential (markers)', 'Parallel (lines)'], fontsize=9)

# ===== Plot 6: Scaling Summary =====
ax6 = plt.subplot(2, 3, 6)
# Show key metrics in text form
metrics_text = f"""
PERFORMANCE SUMMARY
{'='*30}

Models processed:  {N_MODELS:,}
Layers per model:  {N_LAYERS}

SEQUENTIAL
  Time:       {time_sequential:.2f}s ({n_sequential} models)
  Throughput: {rate_sequential:.1f} models/s

PARALLEL
  Time:       {time_parallel:.2f}s
  Throughput: {rate_parallel:.1f} models/s
  Workers:    {N_WORKERS}
  Chunk size: {CHUNK_SIZE}

SPEEDUP
  Speedup:    {speedup_val:.2f}x
  Efficiency: {efficiency_val:.1f}%

VALIDATION
  Max diff:   {max_diff:.2e}
  Status:     {'✓ PASS' if max_diff < 1e-10 else '✗ FAIL'}

OPTIMAL CHUNK SIZE
  Tested:     {optimal_chunk}
  Recommended:{adaptive_cs}
"""
ax6.text(0.05, 0.95, metrics_text, transform=ax6.transAxes,
        fontsize=10, verticalalignment='top', family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
ax6.axis('off')

plt.tight_layout()
plt.savefig('batch_parallel_benchmark.png', dpi=150, bbox_inches='tight')
print("✓ Saved: batch_parallel_benchmark.png")

# ============================================================================
# Summary and Recommendations
# ============================================================================
print(f"\n{'='*70}")
print(f"Summary and Recommendations")
print(f"{'='*70}")

print(f"\nPerformance achieved:")
print(f"  Parallel speedup: {speedup_val:.2f}x")
print(f"  Parallel efficiency: {efficiency_val:.1f}%")

if efficiency_val > 80:
    print(f"  ✓ Excellent scaling (>80% efficiency)")
elif efficiency_val > 60:
    print(f"  ✓ Good scaling (60-80% efficiency)")
else:
    print(f"  ⚠ Moderate scaling (<60% efficiency)")
    print(f"    Consider: reduce workers, increase chunk size, or larger batches")

print(f"\nOptimal settings for this system:")
print(f"  Workers: {N_WORKERS}")
print(f"  Chunk size: {optimal_chunk}")

print(f"\nEstimated time to process 1 million models:")
est_time_1M = 1_000_000 / rate_parallel
if est_time_1M < 60:
    print(f"  Parallel: {est_time_1M:.1f} seconds")
elif est_time_1M < 3600:
    print(f"  Parallel: {est_time_1M/60:.1f} minutes")
else:
    print(f"  Parallel: {est_time_1M/3600:.2f} hours")

est_time_1M_seq = 1_000_000 / rate_sequential
print(f"  Sequential: {est_time_1M_seq/3600:.2f} hours")

print(f"\n{'='*70}")
print("Benchmark complete!")
print(f"{'='*70}")

plt.show()
