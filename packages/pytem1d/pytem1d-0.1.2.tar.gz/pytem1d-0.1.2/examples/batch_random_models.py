#!/usr/bin/env python3
"""
Batch processing: 1000 random N-layer models

This example demonstrates:
1. Generating random earth models (configurable number of layers)
2. Batch processing with both functional and class-based APIs
3. Performance comparison between the two approaches
4. Ensemble visualization and statistics
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from pytem1d import run_tem1d, TEM1DModel

# ============================================================================
# CONFIGURATION - Modify these parameters as needed
# ============================================================================
N_MODELS = 1000      # Number of random models to generate
                     # Tip: Start with 100 for quick tests, use 1000+ for production

N_LAYERS = 8         # Number of layers (can be any value >= 1)
                     # Examples:
                     #   N_LAYERS = 2  ->  2-layer models (1 interface)
                     #   N_LAYERS = 3  ->  3-layer models (2 interfaces) [DEFAULT]
                     #   N_LAYERS = 4  ->  4-layer models (3 interfaces)
                     #   N_LAYERS = 5  ->  5-layer models (4 interfaces)

RANDOM_SEED = 42     # For reproducibility (use None for different random models each run)

# Set random seed
np.random.seed(RANDOM_SEED)

# ============================================================================
# Generate random N-layer models
# ============================================================================
print("=" * 70)
print(f"Batch Processing: {N_MODELS} Random {N_LAYERS}-Layer Models")
print("=" * 70)

print(f"\nGenerating {N_MODELS} random {N_LAYERS}-layer models...")

# Resistivity ranges (Ohm-m) - log-uniform distribution
rho_min, rho_max = 1, 1000
resistivities_all = 10 ** np.random.uniform(
    np.log10(rho_min), np.log10(rho_max), size=(N_MODELS, N_LAYERS)
)

# Layer depths (m) - top layer is always at 0
depths_all = np.zeros((N_MODELS, N_LAYERS))

# Generate increasing depths for each layer interface
# Strategy: divide depth range into N_LAYERS-1 intervals with some randomness
if N_LAYERS > 1:
    # Maximum depth for deepest interface
    max_depth = 200.0

    # Generate random cumulative depths that are monotonically increasing
    for i in range(1, N_LAYERS):
        # Each layer interface at progressively greater depth
        depth_min = (i - 1) * max_depth / (N_LAYERS - 1) + 10
        depth_max = i * max_depth / (N_LAYERS - 1) + 20
        depths_all[:, i] = np.random.uniform(depth_min, depth_max, N_MODELS)

    # Ensure depths are strictly increasing for each model
    depths_all = np.sort(depths_all, axis=1)
    depths_all[:, 0] = 0  # First layer always at surface

print(f"✓ Generated {N_MODELS} models")
print(f"  Resistivity range: {rho_min}-{rho_max} Ω·m (log-uniform)")
print(f"  Number of layers: {N_LAYERS}")
print(f"  Layer depths:")
for i in range(N_LAYERS):
    if i == 0:
        print(f"    Layer {i+1}: 0 m (surface)")
    elif i == N_LAYERS - 1:
        depth_range = f"{depths_all[:, i].min():.1f}-{depths_all[:, i].max():.1f}"
        print(f"    Layer {i+1}: {depth_range} m (halfspace)")
    else:
        depth_range = f"{depths_all[:, i].min():.1f}-{depths_all[:, i].max():.1f}"
        print(f"    Layer {i+1}: {depth_range} m")

# ============================================================================
# Method 1: Functional API
# ============================================================================
print("\n" + "-" * 70)
print("Method 1: Functional API (run_tem1d)")
print("-" * 70)

results_functional = []
start_time = time.time()

for i in range(N_MODELS):
    if (i + 1) % 100 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed
        eta = (N_MODELS - i - 1) / rate
        print(f"  Progress: {i+1}/{N_MODELS} ({rate:.1f} models/s, ETA: {eta:.1f}s)")

    result = run_tem1d(
        resistivities=resistivities_all[i],
        depths=depths_all[i],
        tx_area=314.16,
    )
    results_functional.append(result)

time_functional = time.time() - start_time
print(f"\n✓ Functional API completed in {time_functional:.2f} seconds")
print(f"  Average: {time_functional / N_MODELS * 1000:.2f} ms per model")
print(f"  Rate: {N_MODELS / time_functional:.1f} models/second")

# ============================================================================
# Method 2: Class-Based API
# ============================================================================
print("\n" + "-" * 70)
print("Method 2: Class-Based API (TEM1DModel)")
print("-" * 70)

results_class = []
start_time = time.time()

# Create single TEM1DModel instance and reuse it
tem = TEM1DModel()
tem.set_instrument(tx_area=314.16)

for i in range(N_MODELS):
    if (i + 1) % 100 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed
        eta = (N_MODELS - i - 1) / rate
        print(f"  Progress: {i+1}/{N_MODELS} ({rate:.1f} models/s, ETA: {eta:.1f}s)")

    tem.set_earth_model(resistivities_all[i], depths_all[i])
    result = tem.run()
    results_class.append(result)

time_class = time.time() - start_time
print(f"\n✓ Class-based API completed in {time_class:.2f} seconds")
print(f"  Average: {time_class / N_MODELS * 1000:.2f} ms per model")
print(f"  Rate: {N_MODELS / time_class:.1f} models/second")

# ============================================================================
# Validation: Compare results from both methods
# ============================================================================
print("\n" + "-" * 70)
print("Validation: Comparing Results")
print("-" * 70)

# Check that both methods give identical results
max_diff = 0
for i in range(N_MODELS):
    diff = np.abs(results_functional[i].responses - results_class[i].responses)
    max_diff = max(max_diff, diff.max())

print(f"Maximum difference between methods: {max_diff:.2e}")
if max_diff < 1e-10:
    print("✓ Both methods produce IDENTICAL results!")
else:
    print("⚠ Methods produce different results (unexpected!)")

# Performance comparison
speedup = time_functional / time_class
if speedup > 1:
    print(f"✓ Class-based API is {speedup:.2f}x FASTER")
else:
    print(f"✓ Functional API is {1/speedup:.2f}x FASTER")

# ============================================================================
# Visualization: Ensemble of responses
# ============================================================================
print("\n" + "-" * 70)
print("Creating Visualizations")
print("-" * 70)

# Use functional API results for plotting (they're identical)
results = results_functional

# Extract common time base (same for all models)
times = results[0].times

# Create response matrix (n_models x n_times)
responses_matrix = np.array([r.responses for r in results])

# Compute statistics
response_median = np.median(np.abs(responses_matrix), axis=0)
response_mean = np.mean(np.abs(responses_matrix), axis=0)
response_p10 = np.percentile(np.abs(responses_matrix), 10, axis=0)
response_p90 = np.percentile(np.abs(responses_matrix), 90, axis=0)
response_min = np.min(np.abs(responses_matrix), axis=0)
response_max = np.max(np.abs(responses_matrix), axis=0)

# Create comprehensive plot
fig = plt.figure(figsize=(16, 12))

# ============================================================================
# Panel 1: All responses with statistics
# ============================================================================
ax1 = plt.subplot(2, 2, 1)

# Plot all individual responses (faded)
for i in range(min(N_MODELS, 500)):  # Plot first 500 to avoid overcrowding
    ax1.loglog(times * 1e3, np.abs(responses_matrix[i]),
               color='lightblue', alpha=0.1, linewidth=0.5)

# Plot statistics
ax1.loglog(times * 1e3, response_median, 'b-', linewidth=2.5, label='Median')
ax1.loglog(times * 1e3, response_mean, 'r--', linewidth=2, label='Mean')
ax1.fill_between(times * 1e3, response_p10, response_p90,
                  color='blue', alpha=0.2, label='10-90 percentile')

ax1.set_xlabel('Time (ms)', fontsize=11)
ax1.set_ylabel('|dB/dt| (V/A·m²)', fontsize=11)
ax1.set_title(f'(a) Ensemble of {N_MODELS} Random Models', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', alpha=0.3)
ax1.legend(fontsize=10)

# ============================================================================
# Panel 2: Statistics only (clearer view)
# ============================================================================
ax2 = plt.subplot(2, 2, 2)

ax2.loglog(times * 1e3, response_median, 'b-', linewidth=2.5, label='Median')
ax2.loglog(times * 1e3, response_mean, 'r-', linewidth=2, label='Mean')
ax2.loglog(times * 1e3, response_p10, 'g--', linewidth=1.5, label='10th percentile')
ax2.loglog(times * 1e3, response_p90, 'm--', linewidth=1.5, label='90th percentile')
ax2.loglog(times * 1e3, response_min, 'k:', linewidth=1, label='Min/Max', alpha=0.5)
ax2.loglog(times * 1e3, response_max, 'k:', linewidth=1, alpha=0.5)

ax2.set_xlabel('Time (ms)', fontsize=11)
ax2.set_ylabel('|dB/dt| (V/A·m²)', fontsize=11)
ax2.set_title('(b) Ensemble Statistics', fontsize=12, fontweight='bold')
ax2.grid(True, which='both', alpha=0.3)
ax2.legend(fontsize=9)

# ============================================================================
# Panel 3: Response variability (coefficient of variation)
# ============================================================================
ax3 = plt.subplot(2, 2, 3)

# Coefficient of variation (std/mean)
response_std = np.std(np.abs(responses_matrix), axis=0)
cv = response_std / response_mean

ax3.semilogx(times * 1e3, cv * 100, 'b-', linewidth=2)
ax3.set_xlabel('Time (ms)', fontsize=11)
ax3.set_ylabel('Coefficient of Variation (%)', fontsize=11)
ax3.set_title('(c) Response Variability vs Time', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.axhline(100, color='r', linestyle='--', linewidth=1, alpha=0.5, label='100%')
ax3.legend(fontsize=9)

# ============================================================================
# Panel 4: Histogram at specific time gates
# ============================================================================
ax4 = plt.subplot(2, 2, 4)

# Select 3 representative time gates (early, middle, late)
time_indices = [10, 35, 60]
time_labels = ['Early', 'Middle', 'Late']
colors = ['red', 'green', 'blue']

for idx, label, color in zip(time_indices, time_labels, colors):
    responses_at_time = np.abs(responses_matrix[:, idx])
    ax4.hist(np.log10(responses_at_time), bins=30, alpha=0.5,
             color=color, label=f'{label} (t={times[idx]*1e3:.2f} ms)')

ax4.set_xlabel('log₁₀(|dB/dt|)', fontsize=11)
ax4.set_ylabel('Count', fontsize=11)
ax4.set_title('(d) Response Distribution at Different Times', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('batch_random_models_ensemble.png', dpi=150, bbox_inches='tight')
print("✓ Saved: batch_random_models_ensemble.png")

# ============================================================================
# Additional plot: Model parameter distributions
# ============================================================================
# Calculate number of rows and columns needed
n_resistivity_plots = N_LAYERS
n_thickness_plots = N_LAYERS - 1
n_param_plots = n_resistivity_plots + n_thickness_plots + 1  # +1 for performance
n_cols = min(4, max(3, N_LAYERS))  # At least 3, at most 4 columns
n_rows = int(np.ceil(n_param_plots / n_cols))

fig2, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
axes = np.array(axes).flatten()  # Flatten for easier indexing

plot_idx = 0

# Resistivities
for i in range(N_LAYERS):
    ax = axes[plot_idx]
    ax.hist(np.log10(resistivities_all[:, i]), bins=30, color=f'C{i}', alpha=0.7, edgecolor='black')
    ax.set_xlabel('log₁₀(ρ) [log₁₀(Ω·m)]', fontsize=10)
    ax.set_ylabel('Count', fontsize=10)
    ax.set_title(f'Layer {i+1} Resistivity', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add statistics
    median_rho = np.median(resistivities_all[:, i])
    ax.axvline(np.log10(median_rho), color='red', linestyle='--', linewidth=2,
               label=f'Median={median_rho:.1f} Ω·m')
    ax.legend(fontsize=8)
    plot_idx += 1

# Layer thicknesses
thicknesses = np.diff(depths_all, axis=1)
for i in range(N_LAYERS - 1):
    ax = axes[plot_idx]
    ax.hist(thicknesses[:, i], bins=30, color=f'C{i+N_LAYERS}', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Thickness (m)', fontsize=10)
    ax.set_ylabel('Count', fontsize=10)
    ax.set_title(f'Layer {i+1} Thickness', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add statistics
    median_thick = np.median(thicknesses[:, i])
    ax.axvline(median_thick, color='red', linestyle='--', linewidth=2,
               label=f'Median={median_thick:.1f} m')
    ax.legend(fontsize=8)
    plot_idx += 1

# Performance comparison
ax = axes[plot_idx]
methods = ['Functional\nAPI', 'Class-based\nAPI']
times_comparison = [time_functional, time_class]
bars = ax.bar(methods, times_comparison, color=['#3498db', '#e74c3c'], alpha=0.7, edgecolor='black')
ax.set_ylabel('Total Time (seconds)', fontsize=10)
ax.set_title('Performance Comparison', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, t in zip(bars, times_comparison):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{t:.2f}s\n({N_MODELS/t:.1f} models/s)',
            ha='center', va='bottom', fontsize=9, fontweight='bold')

# Add speedup annotation
if speedup != 1.0:
    faster_method = 'Class-based' if speedup > 1 else 'Functional'
    ax.text(0.5, max(times_comparison) * 0.5,
            f'{faster_method}\n{abs(speedup):.2f}x faster',
            ha='center', va='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
plot_idx += 1

# Hide unused subplots
for i in range(plot_idx, len(axes)):
    axes[i].axis('off')

plt.tight_layout()
plt.savefig('batch_random_models_parameters.png', dpi=150, bbox_inches='tight')
print("✓ Saved: batch_random_models_parameters.png")

# ============================================================================
# Summary Statistics
# ============================================================================
print("\n" + "=" * 70)
print("Summary Statistics")
print("=" * 70)

print(f"\nModel Parameters:")
print(f"  Resistivities (Ω·m):")
for i in range(N_LAYERS):
    rho_med = np.median(resistivities_all[:, i])
    rho_std = np.std(resistivities_all[:, i])
    print(f"    Layer {i+1}: median={rho_med:.1f}, std={rho_std:.1f}")

print(f"\n  Layer Thicknesses (m):")
for i in range(N_LAYERS - 1):
    thick_med = np.median(thicknesses[:, i])
    thick_std = np.std(thicknesses[:, i])
    print(f"    Layer {i+1}: median={thick_med:.1f}, std={thick_std:.1f}")

print(f"\nResponse Statistics (at t=1ms):")
idx_1ms = np.argmin(np.abs(times - 1e-3))
responses_1ms = np.abs(responses_matrix[:, idx_1ms])
print(f"  Median: {np.median(responses_1ms):.2e} V/A·m²")
print(f"  Range: {responses_1ms.min():.2e} to {responses_1ms.max():.2e}")
print(f"  Spread: {responses_1ms.max() / responses_1ms.min():.1f}x")

print(f"\nComputational Performance:")
print(f"  Total models: {N_MODELS}")
print(f"  Functional API: {time_functional:.2f}s ({N_MODELS/time_functional:.1f} models/s)")
print(f"  Class API: {time_class:.2f}s ({N_MODELS/time_class:.1f} models/s)")
print(f"  Results identical: {'✓ YES' if max_diff < 1e-10 else '✗ NO'}")

print("\n" + "=" * 70)
print("Batch processing complete!")
print("=" * 70)
print("\nGenerated files:")
print("  - batch_random_models_ensemble.png")
print("  - batch_random_models_parameters.png")

plt.show()
