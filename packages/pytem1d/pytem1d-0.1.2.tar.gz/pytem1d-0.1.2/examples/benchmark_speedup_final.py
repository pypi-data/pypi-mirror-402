#!/usr/bin/env python3
"""
Comprehensive Speedup Benchmark

Documents parallel speedup across different model counts:
N = 100, 1,000, 10,000, 100,000, 1,000,000

For very large N (>10,000), sequential time is extrapolated from smaller sample.
This allows benchmarking millions of models without waiting hours for sequential execution.

Usage:
    python benchmark_speedup_final.py

Output:
    - speedup_benchmark_results.npz (raw data)
    - speedup_benchmark_plots.png (visualization)
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
# Model counts to benchmark
MODEL_COUNTS = [100, 1000, 10000, 100000, 1000000]

# For N > SEQUENTIAL_LIMIT, extrapolate sequential time from sample
SEQUENTIAL_LIMIT = 10000  # Only run sequential up to this N
SEQUENTIAL_SAMPLE = 2000  # For N > limit, compute this many sequentially

N_LAYERS = 3
N_WORKERS = cpu_count()
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

print("=" * 80)
print("TEM1D Parallel Speedup Benchmark")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Model counts: {MODEL_COUNTS}")
print(f"  CPU cores: {cpu_count()}")
print(f"  Workers: {N_WORKERS}")
print(f"  Sequential limit: {SEQUENTIAL_LIMIT:,} (larger N will be extrapolated)")

# ============================================================================
# Model generation function
# ============================================================================
def generate_models(n_models, n_layers=3):
    """Generate random N-layer models"""
    resistivities = 10 ** np.random.uniform(0, 3, size=(n_models, n_layers))
    depths = np.zeros((n_models, n_layers))

    if n_layers > 1:
        max_depth = 200.0
        for i in range(1, n_layers):
            depth_min = (i - 1) * max_depth / (n_layers - 1) + 10
            depth_max = i * max_depth / (n_layers - 1) + 20
            depths[:, i] = np.random.uniform(depth_min, depth_max, n_models)
        depths = np.sort(depths, axis=1)
        depths[:, 0] = 0

    return resistivities, depths

# ============================================================================
# Storage for results
# ============================================================================
results = {
    'n_models': [],
    'time_sequential': [],
    'time_parallel': [],
    'speedup': [],
    'efficiency': [],
    'throughput_sequential': [],
    'throughput_parallel': [],
    'chunk_size': [],
    'sequential_measured': [],  # True if actually measured, False if extrapolated
}

# ============================================================================
# Run benchmarks
# ============================================================================
for n_models in MODEL_COUNTS:
    print(f"\n{'='*80}")
    print(f"Benchmarking N = {n_models:,} models")
    print(f"{'='*80}")

    # Generate models
    print(f"Generating {n_models:,} models...")
    resistivities, depths = generate_models(n_models, N_LAYERS)
    print(f"✓ Generated")

    # ========================================================================
    # Sequential Benchmark
    # ========================================================================
    print(f"\n{'-'*70}")
    print(f"Sequential Processing")
    print(f"{'-'*70}")

    if n_models <= SEQUENTIAL_LIMIT:
        # Actually run sequential for all models
        print(f"Computing {n_models:,} models sequentially...")
        start = time.time()

        for i in range(n_models):
            if (i + 1) % 500 == 0 or (i + 1) == n_models:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (n_models - i - 1) / rate if rate > 0 else 0
                print(f"  {i+1:,}/{n_models:,} ({rate:.1f} models/s, ETA: {eta:.1f}s)")

            run_tem1d(resistivities[i], depths[i])

        time_seq = time.time() - start
        rate_seq = n_models / time_seq
        sequential_measured = True

        print(f"✓ Sequential: {time_seq:.2f}s ({rate_seq:.1f} models/s)")

    else:
        # Extrapolate from sample
        print(f"Computing {SEQUENTIAL_SAMPLE:,} sample models (will extrapolate)...")
        start = time.time()

        for i in range(SEQUENTIAL_SAMPLE):
            if (i + 1) % 500 == 0 or (i + 1) == SEQUENTIAL_SAMPLE:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"  {i+1:,}/{SEQUENTIAL_SAMPLE:,} ({rate:.1f} models/s)")

            run_tem1d(resistivities[i], depths[i])

        time_sample = time.time() - start
        rate_seq = SEQUENTIAL_SAMPLE / time_sample

        # Extrapolate
        time_seq = time_sample * (n_models / SEQUENTIAL_SAMPLE)
        sequential_measured = False

        print(f"✓ Sample: {time_sample:.2f}s ({rate_seq:.1f} models/s)")
        print(f"  Extrapolated for {n_models:,}: {time_seq:.2f}s ({time_seq/3600:.2f} hours)")

    # ========================================================================
    # Parallel Benchmark
    # ========================================================================
    print(f"\n{'-'*70}")
    print(f"Parallel Processing")
    print(f"{'-'*70}")

    chunk_size = adaptive_chunk_size(n_models, N_WORKERS)
    print(f"Chunk size: {chunk_size}")

    start = time.time()
    results_par = parallel_tem1d(
        resistivities, depths,
        n_workers=N_WORKERS,
        chunk_size=chunk_size,
        verbose=True,
    )
    time_par = time.time() - start
    rate_par = n_models / time_par

    print(f"✓ Parallel: {time_par:.2f}s ({rate_par:.1f} models/s)")

    # ========================================================================
    # Compute metrics
    # ========================================================================
    speedup = time_seq / time_par
    efficiency = speedup / N_WORKERS * 100

    print(f"\n{'-'*70}")
    print(f"Results")
    print(f"{'-'*70}")
    print(f"Sequential: {time_seq:12.2f}s ({rate_seq:8.1f} models/s) {'[measured]' if sequential_measured else '[extrapolated]'}")
    print(f"Parallel:   {time_par:12.2f}s ({rate_par:8.1f} models/s)")
    print(f"Speedup:    {speedup:12.2f}×")
    print(f"Efficiency: {efficiency:12.1f}%")

    # Store results
    results['n_models'].append(n_models)
    results['time_sequential'].append(time_seq)
    results['time_parallel'].append(time_par)
    results['speedup'].append(speedup)
    results['efficiency'].append(efficiency)
    results['throughput_sequential'].append(rate_seq)
    results['throughput_parallel'].append(rate_par)
    results['chunk_size'].append(chunk_size)
    results['sequential_measured'].append(sequential_measured)

# ============================================================================
# Save results
# ============================================================================
print(f"\n{'='*80}")
print("Saving Results")
print(f"{'='*80}")

for key in results:
    results[key] = np.array(results[key])

np.savez('speedup_benchmark_results.npz', **results, n_workers=N_WORKERS, n_layers=N_LAYERS)
print("✓ Saved: speedup_benchmark_results.npz")

# ============================================================================
# Create Visualization
# ============================================================================
print(f"\nCreating plots...")

fig = plt.figure(figsize=(16, 10))

n = results['n_models']
t_seq = results['time_sequential']
t_par = results['time_parallel']
speedup = results['speedup']
eff = results['efficiency']
tp_seq = results['throughput_sequential']
tp_par = results['throughput_parallel']

# Plot 1: Time vs N
ax1 = plt.subplot(2, 3, 1)
ax1.loglog(n, t_seq, 'o-', linewidth=2.5, markersize=10, color='#e74c3c', label='Sequential')
ax1.loglog(n, t_par, 's-', linewidth=2.5, markersize=10, color='#2ecc71', label='Parallel')
ax1.set_xlabel('Number of Models (N)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Total Time (seconds)', fontsize=12, fontweight='bold')
ax1.set_title('A) Execution Time vs Model Count', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, which='both')
ax1.legend(fontsize=11)

# Add time annotations
for i in range(len(n)):
    # Format time labels
    if t_seq[i] < 60:
        label_seq = f"{t_seq[i]:.1f}s"
    elif t_seq[i] < 3600:
        label_seq = f"{t_seq[i]/60:.0f}m"
    else:
        label_seq = f"{t_seq[i]/3600:.1f}h"

    if t_par[i] < 60:
        label_par = f"{t_par[i]:.1f}s"
    else:
        label_par = f"{t_par[i]/60:.0f}m"

    ax1.annotate(label_seq, (n[i], t_seq[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=8, color='#e74c3c')
    ax1.annotate(label_par, (n[i], t_par[i]), textcoords="offset points",
                xytext=(0, -15), ha='center', fontsize=8, color='#2ecc71', fontweight='bold')

# Plot 2: Speedup vs N
ax2 = plt.subplot(2, 3, 2)
ax2.semilogx(n, speedup, 'D-', linewidth=2.5, markersize=10, color='#3498db')
ax2.axhline(y=N_WORKERS, color='gray', linestyle='--', linewidth=1.5,
           alpha=0.6, label=f'Ideal ({N_WORKERS}×)')
ax2.set_xlabel('Number of Models (N)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Speedup (×)', fontsize=12, fontweight='bold')
ax2.set_title('B) Parallel Speedup vs Model Count', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)

# Add speedup labels
for i in range(len(n)):
    ax2.annotate(f"{speedup[i]:.1f}×", (n[i], speedup[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color='#3498db')

# Plot 3: Throughput vs N
ax3 = plt.subplot(2, 3, 3)
ax3.loglog(n, tp_par, 's-', linewidth=2.5, markersize=10, color='#2ecc71', label='Parallel')
ax3.loglog(n, tp_seq, 'o--', linewidth=1.5, markersize=7, color='#e74c3c',
          alpha=0.5, label='Sequential')
ax3.set_xlabel('Number of Models (N)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Throughput (models/s)', fontsize=12, fontweight='bold')
ax3.set_title('C) Processing Throughput', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, which='both')
ax3.legend(fontsize=11)

# Add throughput labels
for i in range(len(n)):
    ax3.annotate(f"{tp_par[i]:.0f}/s", (n[i], tp_par[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=8, color='#2ecc71', fontweight='bold')

# Plot 4: Efficiency vs N
ax4 = plt.subplot(2, 3, 4)
ax4.semilogx(n, eff, '^-', linewidth=2.5, markersize=10, color='#9b59b6')
ax4.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Ideal (100%)')
ax4.axhline(y=80, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='Good (80%)')
ax4.set_xlabel('Number of Models (N)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Parallel Efficiency (%)', fontsize=12, fontweight='bold')
ax4.set_title('D) Parallel Efficiency', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=10)

# Add efficiency labels
for i in range(len(n)):
    ax4.annotate(f"{eff[i]:.1f}%", (n[i], eff[i]), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=9, color='#9b59b6')

# Plot 5: Time Saved
ax5 = plt.subplot(2, 3, 5)
time_saved_hours = (t_seq - t_par) / 3600
ax5.loglog(n, time_saved_hours, 'v-', linewidth=2.5, markersize=10, color='#16a085')
ax5.set_xlabel('Number of Models (N)', fontsize=12, fontweight='bold')
ax5.set_ylabel('Time Saved (hours)', fontsize=12, fontweight='bold')
ax5.set_title('E) Time Saved by Parallelization', fontsize=13, fontweight='bold')
ax5.grid(True, alpha=0.3, which='both')

# Add time saved labels
for i in range(len(n)):
    t_saved = time_saved_hours[i]
    if t_saved < 0.01:
        label = f"{t_saved*3600:.0f}s"
    elif t_saved < 1:
        label = f"{t_saved*60:.0f}m"
    else:
        label = f"{t_saved:.1f}h"
    ax5.annotate(label, (n[i], t_saved), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=8, color='#16a085', fontweight='bold')

# Plot 6: Summary Table
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

summary_text = f"""
SPEEDUP BENCHMARK RESULTS
{'='*55}

System:  {N_WORKERS} cores, {N_LAYERS}-layer models
{'='*55}
"""

for i in range(len(n)):
    measured = "[measured]" if results['sequential_measured'][i] else "[extrap.]"

    # Format times
    if t_seq[i] < 60:
        t_seq_str = f"{t_seq[i]:.1f}s"
    elif t_seq[i] < 3600:
        t_seq_str = f"{t_seq[i]/60:.1f}m"
    else:
        t_seq_str = f"{t_seq[i]/3600:.2f}h"

    if t_par[i] < 60:
        t_par_str = f"{t_par[i]:.1f}s"
    elif t_par[i] < 3600:
        t_par_str = f"{t_par[i]/60:.1f}m"
    else:
        t_par_str = f"{t_par[i]/3600:.2f}h"

    summary_text += f"""
N = {n[i]:>10,}:
  Sequential: {t_seq_str:>7s}  {measured:>11s}
  Parallel:   {t_par_str:>7s}  ({tp_par[i]:>6.0f} models/s)
  Speedup:    {speedup[i]:>6.1f}×  Efficiency: {eff[i]:>5.1f}%
"""

summary_text += f"""
{'='*55}
Peak Performance:
  Max speedup:     {speedup.max():.1f}× at N={n[speedup.argmax()]:,}
  Max throughput:  {tp_par.max():.0f} models/s
  Max efficiency:  {eff.max():.1f}%

For 1 Million Models:
  Sequential:  {t_seq[-1]/3600:.2f} hours
  Parallel:    {t_par[-1]/60:.1f} minutes
  Time saved:  {time_saved_hours[-1]:.2f} hours
"""

ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
        fontsize=9, verticalalignment='top', family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.2))

plt.tight_layout()
plt.savefig('speedup_benchmark_plots.png', dpi=150, bbox_inches='tight')
print("✓ Saved: speedup_benchmark_plots.png")

# ============================================================================
# Print Summary
# ============================================================================
print(f"\n{'='*80}")
print("BENCHMARK SUMMARY")
print(f"{'='*80}\n")

print(f"{'N':>12s}  {'Sequential':>12s}  {'Parallel':>12s}  {'Speedup':>10s}  {'Efficiency':>12s}")
print(f"{'-'*80}")

for i in range(len(n)):
    # Format times
    if t_seq[i] < 60:
        t_seq_str = f"{t_seq[i]:.2f}s"
    elif t_seq[i] < 3600:
        t_seq_str = f"{t_seq[i]/60:.2f}m"
    else:
        t_seq_str = f"{t_seq[i]/3600:.2f}h"

    if t_par[i] < 60:
        t_par_str = f"{t_par[i]:.2f}s"
    else:
        t_par_str = f"{t_par[i]/60:.2f}m"

    measured_marker = "*" if results['sequential_measured'][i] else " "

    print(f"{n[i]:>12,}  {t_seq_str:>12s}{measured_marker} {t_par_str:>12s}  {speedup[i]:>9.2f}×  {eff[i]:>11.1f}%")

print(f"\n* = measured, blank = extrapolated")
print(f"\nKey Results:")
print(f"  Maximum speedup:      {speedup.max():.2f}× (at N={n[speedup.argmax()]:,})")
print(f"  Maximum throughput:   {tp_par.max():.0f} models/s")
print(f"  Best efficiency:      {eff.max():.1f}%")

print(f"\nFiles created:")
print(f"  - speedup_benchmark_results.npz")
print(f"  - speedup_benchmark_plots.png")

print(f"\n{'='*80}")

plt.show()
