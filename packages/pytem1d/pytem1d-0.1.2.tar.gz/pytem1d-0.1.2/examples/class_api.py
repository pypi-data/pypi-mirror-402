#!/usr/bin/env python3
"""
Advanced usage with class-based API

This example demonstrates the class-based interface, which is useful
when you need to vary parameters and run multiple models.
"""

import numpy as np
import matplotlib.pyplot as plt
from pytem1d import TEM1DModel, plot_response, plot_derivatives

# Create TEM1D model instance
print("Setting up TEM1D model...")
tem = TEM1DModel()

# Configure 3-layer earth model
tem.set_earth_model(
    resistivities=[100, 10, 50],  # Ohm-m
    depths=[0, 30, 100],  # m (interfaces at 30m and 100m)
    imlm=0,  # Few-layer model
)

# Configure instrument (central loop)
tem.set_instrument(
    tx_area=314.16,  # m² (radius ~10m)
    tx_rx_separation=0.0,  # Central loop
    tx_height=1.0,  # m
    rx_height=1.0,  # m
)

# Enable derivative calculation for inversion
tem.enable_derivatives(True)

# Run forward modeling
print("Running forward model with derivatives...")
result = tem.run()

print(f"✓ Computation complete!")
print(f"  Time gates: {result.n_times}")
print(f"  Parameters: {result.n_params}")
print(f"  Derivative matrix shape: {result.derivatives.shape}")

# Plot response
fig1 = plot_response(
    result,
    time_unit="ms",
    title="3-Layer Model Response",
    linewidth=2,
    color="darkblue",
)
plt.savefig("class_api_response.png", dpi=150)
print("\n✓ Response plot saved to 'class_api_response.png'")

# Plot derivatives (sensitivities)
fig2 = plot_derivatives(
    result,
    param_labels=["σ₁", "σ₂", "σ₃", "h₁", "h₂", "HTX"],
    plot_type="curves",
)
plt.savefig("class_api_derivatives.png", dpi=150)
print("✓ Derivatives plot saved to 'class_api_derivatives.png'")

# Now run a parameter study - vary middle layer resistivity
print("\nRunning parameter study...")
resistivities_list = [
    [100, 5, 50],
    [100, 10, 50],
    [100, 20, 50],
    [100, 50, 50],
]

fig3, ax = plt.subplots(figsize=(10, 6))

for rho in resistivities_list:
    tem.set_earth_model(rho, [0, 30, 100])
    tem.enable_derivatives(False)  # Faster without derivatives
    result = tem.run()

    ax.loglog(
        result.times * 1e3,
        np.abs(result.responses),
        linewidth=2,
        label=f"ρ₂ = {rho[1]} Ω·m",
    )

ax.set_xlabel("Time (ms)", fontsize=12)
ax.set_ylabel("|dB/dt| (V/A·m²)", fontsize=12)
ax.set_title("Parameter Study: Middle Layer Resistivity", fontsize=14)
ax.grid(True, which="both", alpha=0.3)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig("class_api_parameter_study.png", dpi=150)
print("✓ Parameter study plot saved to 'class_api_parameter_study.png'")

plt.show()
