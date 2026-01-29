"""
Visualization utilities for TEM1D results

This module provides plotting functions for TEM responses, derivatives,
and model schematics.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Optional, Dict, List, Union

from .models import TEM1DResult, EarthModel


def plot_response(
    result: TEM1DResult,
    ax: Optional[Axes] = None,
    time_unit: str = "ms",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> Figure:
    """
    Plot TEM response curve

    Parameters
    ----------
    result : TEM1DResult
        Result to plot
    ax : Axes, optional
        Matplotlib axes to plot on (creates new figure if None)
    time_unit : str, optional
        Time unit for x-axis: 'ms', 's', or 'us' (default: 'ms')
    xlabel : str, optional
        X-axis label (auto-generated if None)
    ylabel : str, optional
        Y-axis label (auto-generated if None)
    title : str, optional
        Plot title
    **kwargs
        Additional keyword arguments passed to plt.loglog()

    Returns
    -------
    Figure
        Matplotlib figure

    Examples
    --------
    >>> fig = plot_response(result)
    >>> plt.show()

    >>> fig, ax = plt.subplots()
    >>> plot_response(result, ax=ax, label="Model 1")
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig = ax.figure

    # Convert times to requested unit
    time_scale = {"us": 1e6, "ms": 1e3, "s": 1.0}[time_unit]
    times = result.times * time_scale

    # Plot absolute value on log-log scale
    ax.loglog(times, np.abs(result.responses), **kwargs)

    # Set labels
    if xlabel is None:
        xlabel = f"Time ({time_unit})"
    if ylabel is None:
        ylabel = "|dB/dt| (V/A·m²)"

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if title is not None:
        ax.set_title(title)

    ax.grid(True, which="both", alpha=0.3)

    return fig


def plot_derivatives(
    result: TEM1DResult,
    param_labels: Optional[List[str]] = None,
    ax: Optional[Axes] = None,
    time_unit: str = "ms",
    cmap: str = "viridis",
    **kwargs,
) -> Figure:
    """
    Plot derivative (Jacobian) matrix as heatmap or individual curves

    Parameters
    ----------
    result : TEM1DResult
        Result with derivatives
    param_labels : list of str, optional
        Parameter labels for legend/axes
    ax : Axes, optional
        Matplotlib axes (creates new figure if None)
    time_unit : str, optional
        Time unit: 'ms', 's', or 'us' (default: 'ms')
    cmap : str, optional
        Colormap for heatmap (default: 'viridis')
    **kwargs
        Additional plotting options

    Returns
    -------
    Figure
        Matplotlib figure

    Examples
    --------
    >>> fig = plot_derivatives(result, param_labels=['σ₁', 'σ₂', 'h₁'])
    """
    if result.derivatives is None:
        raise ValueError("Result does not contain derivatives")

    plot_type = kwargs.pop("plot_type", "curves")  # 'curves' or 'heatmap'

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    time_scale = {"us": 1e6, "ms": 1e3, "s": 1.0}[time_unit]
    times = result.times * time_scale

    if plot_type == "heatmap":
        # Plot as 2D heatmap
        im = ax.imshow(
            result.derivatives.T,
            aspect="auto",
            cmap=cmap,
            extent=[times.min(), times.max(), 0, result.n_params],
            interpolation="nearest",
        )
        ax.set_xlabel(f"Time ({time_unit})")
        ax.set_ylabel("Parameter index")
        if param_labels is not None:
            ax.set_yticks(np.arange(result.n_params) + 0.5)
            ax.set_yticklabels(param_labels)
        plt.colorbar(im, ax=ax, label="∂(dB/dt)/∂p")

    else:  # curves
        # Plot individual derivative curves
        for i in range(result.n_params):
            label = param_labels[i] if param_labels is not None else f"p{i}"
            ax.semilogx(times, result.derivatives[:, i], label=label, **kwargs)

        ax.set_xlabel(f"Time ({time_unit})")
        ax.set_ylabel("∂(dB/dt)/∂p")
        ax.legend()
        ax.grid(True, alpha=0.3)

    ax.set_title("Sensitivity (Jacobian)")

    return fig


def plot_comparison(
    results: Dict[str, TEM1DResult],
    ax: Optional[Axes] = None,
    time_unit: str = "ms",
    **kwargs,
) -> Figure:
    """
    Compare multiple TEM responses

    Parameters
    ----------
    results : dict
        Dictionary mapping labels to TEM1DResult objects
    ax : Axes, optional
        Matplotlib axes (creates new figure if None)
    time_unit : str, optional
        Time unit: 'ms', 's', or 'us' (default: 'ms')
    **kwargs
        Additional plotting options

    Returns
    -------
    Figure
        Matplotlib figure

    Examples
    --------
    >>> results = {
    ...     "Model 1": result1,
    ...     "Model 2": result2,
    ... }
    >>> fig = plot_comparison(results)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    time_scale = {"us": 1e6, "ms": 1e3, "s": 1.0}[time_unit]

    for label, result in results.items():
        times = result.times * time_scale
        ax.loglog(times, np.abs(result.responses), label=label, **kwargs)

    ax.set_xlabel(f"Time ({time_unit})")
    ax.set_ylabel("|dB/dt| (V/A·m²)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    ax.set_title("TEM Response Comparison")

    return fig


def plot_model_schematic(
    model: EarthModel,
    ax: Optional[Axes] = None,
    show_resistivity: bool = True,
    max_depth: Optional[float] = None,
    **kwargs,
) -> Figure:
    """
    Plot 1D layered earth model schematic

    Parameters
    ----------
    model : EarthModel
        Earth model to plot
    ax : Axes, optional
        Matplotlib axes (creates new figure if None)
    show_resistivity : bool, optional
        Show resistivity values in layers (default: True)
    max_depth : float, optional
        Maximum depth to plot (auto if None)
    **kwargs
        Additional plotting options

    Returns
    -------
    Figure
        Matplotlib figure

    Examples
    --------
    >>> model = EarthModel([100, 10, 50], [0, 30, 100])
    >>> fig = plot_model_schematic(model)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 8))
    else:
        fig = ax.figure

    # Determine depth range
    if max_depth is None:
        if model.nlay > 1:
            max_depth = model.depths[-1] * 1.5
        else:
            max_depth = 100

    # Create colormap for resistivities
    cmap = plt.get_cmap(kwargs.pop("cmap", "RdYlBu"))
    rho_log = np.log10(model.resistivities)
    rho_min, rho_max = rho_log.min(), rho_log.max()
    if rho_min == rho_max:
        rho_min, rho_max = rho_min - 1, rho_max + 1

    # Plot each layer
    for i in range(model.nlay):
        depth_top = model.depths[i]
        depth_bot = model.depths[i + 1] if i < model.nlay - 1 else max_depth

        # Normalize resistivity for color
        rho_norm = (rho_log[i] - rho_min) / (rho_max - rho_min)
        color = cmap(rho_norm)

        # Draw rectangle
        ax.add_patch(
            plt.Rectangle(
                (0, depth_top),
                1,
                depth_bot - depth_top,
                facecolor=color,
                edgecolor="black",
                linewidth=2,
            )
        )

        # Add resistivity label
        if show_resistivity:
            label_depth = (depth_top + depth_bot) / 2
            ax.text(
                0.5,
                label_depth,
                f"{model.resistivities[i]:.1f} Ω·m",
                ha="center",
                va="center",
                fontsize=10,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )

    # Set axes properties
    ax.set_xlim(0, 1)
    ax.set_ylim(max_depth, 0)  # Invert y-axis (depth increases downward)
    ax.set_ylabel("Depth (m)")
    ax.set_xticks([])
    ax.set_title("1D Earth Model")

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array(model.resistivities)
    sm.set_clim(10 ** rho_min, 10 ** rho_max)
    cbar = plt.colorbar(sm, ax=ax, label="Resistivity (Ω·m)")
    cbar.set_ticks([10 ** rho_min, 10 ** rho_max])
    cbar.set_ticklabels([f"{10**rho_min:.1f}", f"{10**rho_max:.1f}"])

    return fig


def plot_decay_curve(
    result: TEM1DResult,
    gate_times: Optional[np.ndarray] = None,
    ax: Optional[Axes] = None,
    **kwargs,
) -> Figure:
    """
    Plot decay curve (linear time scale)

    Useful for visualizing late-time behavior and IP effects.

    Parameters
    ----------
    result : TEM1DResult
        Result to plot
    gate_times : array-like, optional
        Specific gate times to highlight
    ax : Axes, optional
        Matplotlib axes
    **kwargs
        Additional plotting options

    Returns
    -------
    Figure
        Matplotlib figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    ax.semilogy(result.times * 1e3, np.abs(result.responses), **kwargs)

    if gate_times is not None:
        # Mark specific gates
        gate_times = np.asarray(gate_times)
        gate_responses = np.interp(gate_times, result.times, result.responses)
        ax.scatter(gate_times * 1e3, np.abs(gate_responses), s=50, c="red", zorder=5)

    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("|dB/dt| (V/A·m²)")
    ax.set_title("TEM Decay Curve")
    ax.grid(True, alpha=0.3)

    return fig
