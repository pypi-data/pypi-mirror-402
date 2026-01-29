#!/usr/bin/env python3
"""
Visualization demo with pytem1d

This example demonstrates all the plotting utilities available in pytem1d.
"""

import numpy as np
import matplotlib.pyplot as plt
from pytem1d import (
    run_tem1d,
    TEM1DModel,
    EarthModel,
    plot_response,
    plot_derivatives,
    plot_comparison,
    plot_model_schematic,
)

print("Generating TEM1D responses for visualization...")

# Create several models to compare
models = {
    "2-layer (resistive)": {
        "resistivities": [100, 10],
        "depths": [0, 50],
    },
    "2-layer (conductive)": {
        "resistivities": [10, 100],
        "depths": [0, 50],
    },
    "3-layer (H-type)": {
        "resistivities": [100, 10, 100],
        "depths": [0, 30, 80],
    },
}

# Compute responses
results = {}
for name, params in models.items():
    print(f"  Computing: {name}")
    result = run_tem1d(**params, tx_area=314.16)
    results[name] = result

# Create a multi-panel figure
fig = plt.figure(figsize=(16, 10))

# Panel 1: Response comparison
ax1 = fig.add_subplot(2, 3, 1)
for name, result in results.items():
    ax1.loglog(result.times * 1e3, np.abs(result.responses), linewidth=2, label=name)
ax1.set_xlabel("Time (ms)")
ax1.set_ylabel("|dB/dt| (V/A·m²)")
ax1.set_title("(a) Response Comparison")
ax1.grid(True, which="both", alpha=0.3)
ax1.legend(fontsize=9)

# Panel 2: Model schematic for 3-layer
ax2 = fig.add_subplot(2, 3, 2)
model_3layer = EarthModel([100, 10, 100], [0, 30, 80])
plot_model_schematic(model_3layer, ax=ax2, max_depth=150)
ax2.set_title("(b) 3-Layer Model")

# Panel 3: Response with derivatives
ax3 = fig.add_subplot(2, 3, 3)
result_deriv = run_tem1d([100, 10, 50], [0, 30, 100], calculate_derivatives=True)
ax3.loglog(result_deriv.times * 1e3, np.abs(result_deriv.responses), "b-", linewidth=2)
ax3.set_xlabel("Time (ms)")
ax3.set_ylabel("|dB/dt| (V/A·m²)")
ax3.set_title("(c) Response with Derivatives")
ax3.grid(True, which="both", alpha=0.3)

# Panel 4: Derivatives (sensitivities)
ax4 = fig.add_subplot(2, 3, 4)
for i in range(result_deriv.n_params):
    ax4.semilogx(result_deriv.times * 1e3, result_deriv.derivatives[:, i], label=f"p{i}")
ax4.set_xlabel("Time (ms)")
ax4.set_ylabel("∂(dB/dt)/∂p")
ax4.set_title("(d) Sensitivity (Jacobian)")
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=8)

# Panel 5: Decay curve (linear time for IP visualization)
ax5 = fig.add_subplot(2, 3, 5)
result_2layer = results["2-layer (resistive)"]
ax5.semilogy(result_2layer.times * 1e3, np.abs(result_2layer.responses), "b-", linewidth=2)
ax5.set_xlabel("Time (ms)")
ax5.set_ylabel("|dB/dt| (V/A·m²)")
ax5.set_title("(e) Decay Curve (Linear Time)")
ax5.grid(True, alpha=0.3)

# Panel 6: Normalized responses
ax6 = fig.add_subplot(2, 3, 6)
for name, result in results.items():
    # Normalize by peak value
    normalized = np.abs(result.responses) / np.abs(result.responses).max()
    ax6.loglog(result.times * 1e3, normalized, linewidth=2, label=name)
ax6.set_xlabel("Time (ms)")
ax6.set_ylabel("Normalized |dB/dt|")
ax6.set_title("(f) Normalized Responses")
ax6.grid(True, which="both", alpha=0.3)
ax6.legend(fontsize=9)

plt.tight_layout()
plt.savefig("plotting_demo_all.png", dpi=150)
print("\n✓ Multi-panel plot saved to 'plotting_demo_all.png'")

# Create standalone derivative heatmap
fig2, ax = plt.subplots(figsize=(10, 6))
plot_derivatives(
    result_deriv,
    param_labels=["σ₁", "σ₂", "σ₃", "h₁", "h₂", "HTX"],
    ax=ax,
    plot_type="heatmap",
)
plt.tight_layout()
plt.savefig("derivatives_heatmap.png", dpi=150)
print("✓ Derivatives heatmap saved to 'derivatives_heatmap.png'")

print("\nVisualization demo complete!")
plt.show()
