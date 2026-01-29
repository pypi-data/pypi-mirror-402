"""
pytem1d - Python interface to TEM1D Fortran code

This package provides a Python wrapper for the TEM1D Fortran code that computes
1D transient electromagnetic (TEM) forward responses and derivatives.

Simple usage::

    from pytem1d import run_tem1d
    result = run_tem1d([100, 10], [0, 50])

Advanced usage::

    from pytem1d import TEM1DModel
    tem = TEM1DModel()
    tem.set_earth_model([100, 10], [0, 50])
    tem.set_instrument(tx_area=314.16)
    result = tem.run()
"""

from ._version import __version__

# High-level API
from .api import run_tem1d, TEM1DModel

# Data models
from .models import (
    EarthModel,
    IPModel,
    Instrument,
    PolygonLoop,
    ResponseConfig,
    Waveform,
    TEM1DResult,
)

# Utilities
from .plotting import (
    plot_response,
    plot_derivatives,
    plot_comparison,
    plot_model_schematic,
    plot_decay_curve,
)
from .io import (
    save_result,
    load_result,
    write_forread,
    read_forwrite,
    model_to_dict,
    model_from_dict,
)

__all__ = [
    # Version
    "__version__",
    # High-level API
    "run_tem1d",
    "TEM1DModel",
    # Data models
    "EarthModel",
    "IPModel",
    "Instrument",
    "PolygonLoop",
    "ResponseConfig",
    "Waveform",
    "TEM1DResult",
    # Plotting
    "plot_response",
    "plot_derivatives",
    "plot_comparison",
    "plot_model_schematic",
    "plot_decay_curve",
    # I/O
    "save_result",
    "load_result",
    "write_forread",
    "read_forwrite",
    "model_to_dict",
    "model_from_dict",
]
