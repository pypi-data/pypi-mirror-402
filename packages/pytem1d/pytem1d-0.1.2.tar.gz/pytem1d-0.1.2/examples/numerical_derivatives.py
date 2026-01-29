#!/usr/bin/env python3
"""
Numerical derivative calculation workaround

Since analytical derivatives may not be implemented in the current Fortran code,
this example shows how to compute numerical derivatives using finite differences.
"""

import numpy as np
import matplotlib.pyplot as plt
from pytem1d import run_tem1d

def compute_numerical_jacobian(
    resistivities,
    depths,
    tx_area=314.16,
    delta_percent=1.0,
):
    """
    Compute numerical Jacobian using finite differences

    Parameters
    ----------
    resistivities : array-like
        Base model resistivities
    depths : array-like
        Layer depths
    tx_area : float
        Transmitter area
    delta_percent : float
        Perturbation size as percentage

    Returns
    -------
    times : np.ndarray
        Time gates
    jacobian : np.ndarray
        Numerical Jacobian matrix (n_times x n_params)
    param_names : list
        Parameter names
    """
    resistivities = np.array(resistivities)
    depths = np.array(depths)
    nlay = len(resistivities)

    # Base response
    print("Computing base response...")
    result_base = run_tem1d(resistivities, depths, tx_area=tx_area)
    times = result_base.times
    response_base = result_base.responses
    n_times = len(times)

    # Parameters: resistivities + thicknesses
    n_params = nlay + (nlay - 1)  # conductivities + thicknesses
    jacobian = np.zeros((n_times, n_params))
    param_names = []

    # Resistivity derivatives (converted to conductivity derivatives)
    for i in range(nlay):
        param_names.append(f"σ_{i+1}")
        rho_perturbed = resistivities.copy()
        delta = resistivities[i] * (delta_percent / 100.0)
        rho_perturbed[i] += delta

        print(f"  Computing ∂/∂ρ_{i+1} (ρ={resistivities[i]:.1f} Ω·m)...")
        result_pert = run_tem1d(rho_perturbed, depths, tx_area=tx_area)

        # Derivative w.r.t. conductivity = -derivative w.r.t. resistivity * σ²
        drho = (result_pert.responses - response_base) / delta
        sigma = 1.0 / resistivities[i]
        jacobian[:, i] = -drho * sigma ** 2

    # Thickness derivatives
    for i in range(nlay - 1):
        param_names.append(f"h_{i+1}")
        depths_perturbed = depths.copy()
        thickness_i = depths[i + 1] - depths[i]
        delta = thickness_i * (delta_percent / 100.0)
        depths_perturbed[i + 1] += delta

        print(f"  Computing ∂/∂h_{i+1} (h={thickness_i:.1f} m)...")
        result_pert = run_tem1d(resistivities, depths_perturbed, tx_area=tx_area)

        jacobian[:, nlay + i] = (result_pert.responses - response_base) / delta

    return times, jacobian, param_names


# Example: 3-layer model
print("=" * 60)
print("Numerical Jacobian Calculation Example")
print("=" * 60)

resistivities = [100, 10, 50]  # Ω·m
depths = [0, 30, 100]  # m

times, jacobian, param_names = compute_numerical_jacobian(
    resistivities, depths, delta_percent=1.0
)

print(f"\n✓ Jacobian computed: {jacobian.shape}")
print(f"  Time gates: {len(times)}")
print(f"  Parameters: {len(param_names)}")
print(f"  Parameter names: {param_names}")

# Check if we got non-zero derivatives
non_zero = np.count_nonzero(jacobian)
print(f"  Non-zero elements: {non_zero} / {jacobian.size}")

if non_zero > 0:
    print("\n✓ Numerical derivatives successfully computed!")

    # Plot derivatives
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, param_name in enumerate(param_names):
        ax = axes[i]
        ax.semilogx(times * 1e3, jacobian[:, i], linewidth=2)
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel(f"∂(dB/dt)/∂{param_name}")
        ax.set_title(f"Sensitivity to {param_name}")
        ax.grid(True, alpha=0.3)

    # Hide unused subplot
    if len(param_names) < 6:
        axes[-1].axis("off")

    plt.tight_layout()
    plt.savefig("numerical_derivatives.png", dpi=150)
    print("\n✓ Plot saved to 'numerical_derivatives.png'")
    plt.show()
else:
    print("\n⚠ Warning: All derivatives are zero!")
    print("This might indicate an issue with the forward model.")
