#!/usr/bin/env python3
"""
Basic usage of pytem1d functional API

This example demonstrates the simplest way to use pytem1d to compute
TEM responses for a 2-layer earth model.
"""

import numpy as np
import matplotlib.pyplot as plt
from pytem1d import run_tem1d

# Define a simple 2-layer model
# Layer 1: 100 Ohm-m from 0-50m depth
# Layer 2: 10 Ohm-m halfspace from 50m to infinity
resistivities = [100, 10]
depths = [0, 50]  # Interface at 50m

# Run forward modeling
print("Running TEM1D forward modeling...")
result = run_tem1d(
    resistivities=resistivities,
    depths=depths,
    tx_area=314.16,  # Circular loop with radius ~10m
    tx_rx_separation=0.0,  # Central loop configuration
)

print(f"✓ Computation complete!")
print(f"  Number of time gates: {len(result.times)}")
print(f"  Time range: {result.times.min():.2e} to {result.times.max():.2e} s")
print(f"  Response range: {np.abs(result.responses).min():.2e} to {np.abs(result.responses).max():.2e} V/A·m²")

# Plot results
fig, ax = plt.subplots(figsize=(10, 6))

ax.loglog(result.times * 1e3, np.abs(result.responses), "b-", linewidth=2, label="2-layer model")
ax.set_xlabel("Time (ms)", fontsize=12)
ax.set_ylabel("|dB/dt| (V/A·m²)", fontsize=12)
ax.set_title("TEM Response - 100 Ω·m over 10 Ω·m", fontsize=14)
ax.grid(True, which="both", alpha=0.3)
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig("basic_tem_response.png", dpi=150)
print("\n✓ Plot saved to 'basic_tem_response.png'")
plt.show()
