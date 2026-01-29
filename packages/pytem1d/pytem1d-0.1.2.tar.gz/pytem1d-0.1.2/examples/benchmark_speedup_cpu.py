#!/usr/bin/env python3
"""
CPU Scaling Benchmark (Strong Scaling Study)

Tests parallel speedup as a function of number of CPUs for a FIXED problem size.
This is a "strong scaling" study showing how well the code scales with more workers.

Fixed Problem Size: N = 100,000 models (3 layers)
Variable: Number of CPUs = 1, 2, 4, 8, 16, 32, 64, 128 (up to available)

Plots:
- Execution time vs N_cpu
- Speedup vs N_cpu (with ideal linear reference)
- Parallel efficiency vs N_cpu
- Throughput vs N_cpu

Usage:
    python benchmark_speedup_cpu.py

Output:
    - speedup_cpu_results.npz (raw data)
    - speedup_cpu_plots.png (visualization)
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
N_MODELS = 100000       # Fixed problem size (strong scaling)
N_LAYERS = 8            # Fixed layer count
RANDOM_SEED = 42        # For reproducibility

# CPU counts to test (will filter to available cores)
CPU_COUNTS_TO_TEST = [1, 2, 4, 8, 16, 32, 64, 128]

# Set random seed
np.random.seed(RANDOM_SEED)

# Get available CPU count
n_cpu_available = cpu_count()
print("=" * 80)
print("TEM1D CPU Scaling Benchmark (Strong Scaling)")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Fixed problem size: N = {N_MODELS:,} models")
print(f"  Layers per model: {N_LAYERS}")
print(f"  CPU cores available: {n_cpu_available}")

# Filter CPU counts to those available
cpu_counts = [n for n in CPU_COUNTS_TO_TEST if n <= n_cpu_available]
print(f"  Testing CPU counts: {cpu_counts}")

if len(cpu_counts) == 0:
    print(f"\nError: Need at least 1 CPU to test!")
    exit(1)

# ============================================================================
# Generate fixed model set (same for all tests)
# ============================================================================
print(f"\n{'-'*80}")
print(f"Generating {N_MODELS:,} random models (fixed dataset for all tests)")
print(f"{'-'*80}")

# Resistivities: log-uniform from 1 to 1000 Ω·m
resistivities = 10 ** np.random.uniform(0, 3, size=(N_MODELS, N_LAYERS))

# Depths: monotonically increasing
depths = np.zeros((N_MODELS, N_LAYERS))
if N_LAYERS > 1:
    max_depth = 200.0
    for i in range(1, N_LAYERS):
        depth_min = (i - 1) * max_depth / (N_LAYERS - 1) + 10
        depth_max = i * max_depth / (N_LAYERS - 1) + 20
        depths[:, i] = np.random.uniform(depth_min, depth_max, N_MODELS)
    depths = np.sort(depths, axis=1)
    depths[:, 0] = 0

print(f"✓ Generated {N_MODELS:,} models")
print(f"  Resistivity range: 1-1000 Ω·m (log-uniform)")
print(f"  Depth range: 0-{depths.max():.1f} m")

# ============================================================================
# Storage for results
# ============================================================================
results = {
    'n_cpu': [],
    'time': [],
    'speedup': [],
    'efficiency': [],
    'throughput': [],
    'chunk_size': [],
}

# ============================================================================
# Run benchmarks for each CPU count
# ============================================================================
time_baseline = None  # Will be set by N_cpu=1 run

for n_cpu in cpu_counts:
    print(f"\n{'='*80}")
    print(f"Benchmarking with N_cpu = {n_cpu}")
    print(f"{'='*80}")

    # Determine chunk size
    if n_cpu == 1:
        # For single CPU, we'll run sequentially (no parallel overhead)
        chunk_size = N_MODELS
    else:
        chunk_size = adaptive_chunk_size(N_MODELS, n_cpu)

    print(f"Chunk size: {chunk_size}")

    # ========================================================================
    # Run computation
    # ========================================================================
    start_time = time.time()

    if n_cpu == 1:
        # Single CPU: run sequentially to get true baseline
        print("Running sequentially (N_cpu=1, no parallel overhead)...")
        results_computed = []
        for i in range(N_MODELS):
            if (i + 1) % 10000 == 0 or (i + 1) == N_MODELS:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (N_MODELS - i - 1) / rate if rate > 0 else 0
                print(f"  {i+1:,}/{N_MODELS:,} ({rate:.1f} models/s, ETA: {eta:.1f}s)")

            result = run_tem1d(resistivities[i], depths[i])
            results_computed.append(result)
    else:
        # Parallel execution
        print(f"Running in parallel with {n_cpu} workers...")
        results_computed = parallel_tem1d(
            resistivities,
            depths,
            n_workers=n_cpu,
            chunk_size=chunk_size,
            verbose=True,
        )

    elapsed_time = time.time() - start_time
    throughput = N_MODELS / elapsed_time

    print(f"\n✓ Completed in {elapsed_time:.2f}s ({throughput:.1f} models/s)")

    # ========================================================================
    # Compute metrics
    # ========================================================================
    if n_cpu == 1:
        # Baseline
        time_baseline = elapsed_time
        speedup = 1.0
        efficiency = 100.0
    else:
        # Compare to baseline
        speedup = time_baseline / elapsed_time
        efficiency = (speedup / n_cpu) * 100.0

    print(f"{'-'*80}")
    print(f"Metrics:")
    print(f"  Time:        {elapsed_time:10.2f}s")
    print(f"  Speedup:     {speedup:10.2f}× (vs N_cpu=1)")
    print(f"  Efficiency:  {efficiency:10.1f}%")
    print(f"  Throughput:  {throughput:10.1f} models/s")

    # ========================================================================
    # Store results
    # ========================================================================
    results['n_cpu'].append(n_cpu)
    results['time'].append(elapsed_time)
    results['speedup'].append(speedup)
    results['efficiency'].append(efficiency)
    results['throughput'].append(throughput)
    results['chunk_size'].append(chunk_size)

# ============================================================================
# Save results
# ============================================================================
print(f"\n{'='*80}")
print("Saving Results")
print(f"{'='*80}")

for key in results:
    results[key] = np.array(results[key])

np.savez(
    'speedup_cpu_results.npz',
    **results,
    n_models=N_MODELS,
    n_layers=N_LAYERS,
)
print("✓ Saved: speedup_cpu_results.npz")

# ============================================================================
# Create Visualization
# ============================================================================
print(f"\nCreating plots...")

fig = plt.figure(figsize=(16, 10))

n_cpu = results['n_cpu']
times = results['time']
speedup = results['speedup']
efficiency = results['efficiency']
throughput = results['throughput']

# ===== Plot 1: Execution Time vs N_cpu =====
ax1 = plt.subplot(2, 3, 1)
ax1.semilogy(n_cpu, times, 'o-', linewidth=2.5, markersize=10, color='#3498db')
ax1.set_xlabel('Number of CPUs', fontsize=12, fontweight='bold')
ax1.set_ylabel('Execution Time (s)', fontsize=12, fontweight='bold')
ax1.set_title('A) Execution Time vs CPU Count', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.set_xticks(n_cpu)

# Add time labels
for i in range(len(n_cpu)):
    t = times[i]
    label = f"{t:.1f}s" if t < 60 else f"{t/60:.1f}m"
    ax1.annotate(label, (n_cpu[i], t), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=8, color='#3498db')

# ===== Plot 2: Speedup vs N_cpu =====
ax2 = plt.subplot(2, 3, 2)
ax2.plot(n_cpu, speedup, 'D-', linewidth=2.5, markersize=10, color='#2ecc71', label='Measured')

# Ideal linear speedup line
ideal_speedup = np.array(n_cpu) / n_cpu[0]
ax2.plot(n_cpu, ideal_speedup, '--', linewidth=2, color='gray', alpha=0.6, label='Ideal (linear)')

ax2.set_xlabel('Number of CPUs', fontsize=12, fontweight='bold')
ax2.set_ylabel('Speedup (×)', fontsize=12, fontweight='bold')
ax2.set_title('B) Speedup vs CPU Count (Strong Scaling)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)
ax2.set_xticks(n_cpu)

# Add speedup labels
for i in range(len(n_cpu)):
    ax2.annotate(f"{speedup[i]:.1f}×", (n_cpu[i], speedup[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color='#2ecc71')

# ===== Plot 3: Parallel Efficiency vs N_cpu =====
ax3 = plt.subplot(2, 3, 3)
ax3.plot(n_cpu, efficiency, 's-', linewidth=2.5, markersize=10, color='#9b59b6')
ax3.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, label='Ideal (100%)')
ax3.axhline(y=80, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='Good (80%)')
ax3.axhline(y=50, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Acceptable (50%)')
ax3.set_xlabel('Number of CPUs', fontsize=12, fontweight='bold')
ax3.set_ylabel('Parallel Efficiency (%)', fontsize=12, fontweight='bold')
ax3.set_title('C) Parallel Efficiency vs CPU Count', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.legend(fontsize=9, loc='upper right')
ax3.set_xticks(n_cpu)

# Add efficiency labels
for i in range(len(n_cpu)):
    ax3.annotate(f"{efficiency[i]:.1f}%", (n_cpu[i], efficiency[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=9, color='#9b59b6')

# ===== Plot 4: Throughput vs N_cpu =====
ax4 = plt.subplot(2, 3, 4)
ax4.plot(n_cpu, throughput, '^-', linewidth=2.5, markersize=10, color='#e74c3c')
ax4.set_xlabel('Number of CPUs', fontsize=12, fontweight='bold')
ax4.set_ylabel('Throughput (models/s)', fontsize=12, fontweight='bold')
ax4.set_title('D) Throughput vs CPU Count', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.set_xticks(n_cpu)

# Add throughput labels
for i in range(len(n_cpu)):
    ax4.annotate(f"{throughput[i]:.0f}/s", (n_cpu[i], throughput[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=8, color='#e74c3c', fontweight='bold')

# ===== Plot 5: Speedup Efficiency (Speedup / Ideal) =====
ax5 = plt.subplot(2, 3, 5)
speedup_efficiency = (speedup / ideal_speedup) * 100
ax5.plot(n_cpu, speedup_efficiency, 'v-', linewidth=2.5, markersize=10, color='#16a085')
ax5.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, label='Ideal')
ax5.set_xlabel('Number of CPUs', fontsize=12, fontweight='bold')
ax5.set_ylabel('Scaling Efficiency (%)', fontsize=12, fontweight='bold')
ax5.set_title('E) Scaling Efficiency (Speedup/Ideal)', fontsize=13, fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.legend(fontsize=11)
ax5.set_xticks(n_cpu)

# Add labels
for i in range(len(n_cpu)):
    ax5.annotate(f"{speedup_efficiency[i]:.0f}%", (n_cpu[i], speedup_efficiency[i]),
                textcoords="offset points", xytext=(0, 10), ha='center',
                fontsize=9, color='#16a085')

# Add overall title with key results
fig.suptitle(f'CPU Scaling Benchmark: N={N_MODELS:,} models | '
             f'Peak: {speedup.max():.1f}× at {n_cpu[speedup.argmax()]} CPUs | '
             f'Max throughput: {throughput.max():.0f} models/s',
             fontsize=14, fontweight='bold', y=0.995)

plt.tight_layout(rect=[0, 0, 1, 0.99])
plt.savefig('speedup_cpu_plots.png', dpi=150, bbox_inches='tight')
print("✓ Saved: speedup_cpu_plots.png")

# ============================================================================
# Print Summary
# ============================================================================
print(f"\n{'='*80}")
print("BENCHMARK SUMMARY")
print(f"{'='*80}\n")

print(f"Problem size: {N_MODELS:,} models ({N_LAYERS} layers)\n")
print(f"{'N_cpu':>8s}  {'Time':>10s}  {'Speedup':>10s}  {'Efficiency':>12s}  {'Throughput':>14s}")
print(f"{'-'*80}")

for i in range(len(n_cpu)):
    t = times[i]
    t_str = f"{t:.2f}s" if t < 60 else f"{t/60:.2f}m"

    print(f"{n_cpu[i]:>8d}  {t_str:>10s}  {speedup[i]:>9.2f}×  {efficiency[i]:>11.1f}%  {throughput[i]:>10.0f} models/s")

print(f"\nKey Metrics:")
print(f"  Baseline time (1 CPU):    {times[0]:.2f}s")
print(f"  Fastest time ({n_cpu[-1]} CPUs):    {times[-1]:.2f}s")
print(f"  Maximum speedup:          {speedup.max():.2f}× (at {n_cpu[speedup.argmax()]} CPUs)")
print(f"  Maximum throughput:       {throughput.max():.0f} models/s")

# Find where efficiency drops below thresholds
if np.any(efficiency[1:] > 80):
    linear_up_to = n_cpu[1:][np.where(efficiency[1:] > 80)[0][-1]]
    print(f"  Linear scaling up to:     {linear_up_to} CPUs (>80% efficiency)")

if np.any(efficiency[1:] > 50):
    good_up_to = n_cpu[1:][np.where(efficiency[1:] > 50)[0][-1]]
    print(f"  Good scaling up to:       {good_up_to} CPUs (>50% efficiency)")

# Estimate serial fraction using Amdahl's Law
# speedup = 1 / (f + (1-f)/n) where f is serial fraction
# Rearranging: f = (1/speedup - 1/n) / (1 - 1/n)
if len(n_cpu) > 1:
    n_max = n_cpu[-1]
    s_max = speedup[-1]
    serial_fraction = ((1/s_max) - (1/n_max)) / (1 - 1/n_max)
    print(f"  Estimated serial fraction: {serial_fraction:.1%} (Amdahl's Law)")

print(f"\nFiles saved:")
print(f"  - speedup_cpu_results.npz  (raw data)")
print(f"  - speedup_cpu_plots.png    (6-panel visualization)")

print(f"\n{'='*80}")
print("CPU scaling benchmark complete!")
print(f"{'='*80}\n")

plt.show()
