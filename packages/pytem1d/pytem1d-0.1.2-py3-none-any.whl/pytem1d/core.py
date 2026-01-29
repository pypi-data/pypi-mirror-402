"""
Low-level ctypes interface to TEM1D Fortran library

This module handles the direct interface with the compiled Fortran shared library
using ctypes. It manages type conversion, array allocation, and calling conventions.
"""

import ctypes
import os
import platform
import numpy as np
from pathlib import Path
from typing import Optional

from .models import (
    EarthModel,
    IPModel,
    Instrument,
    PolygonLoop,
    ResponseConfig,
    Waveform,
    TEM1DResult,
)
from .validation import validate_all

# Constants from ARRAYSDIMBL.INC
N_ARR = 512  # Maximum array size in Fortran


def _get_library_path() -> Path:
    """
    Get path to the TEM1D shared library

    Returns
    -------
    Path
        Path to shared library file

    Raises
    ------
    FileNotFoundError
        If library file not found
    """
    # Get directory containing this module
    module_dir = Path(__file__).parent
    lib_dir = module_dir / "lib"

    # Determine library name based on platform
    system = platform.system()
    if system == "Linux":
        lib_name = "libtem1d.so"
    elif system == "Darwin":
        lib_name = "libtem1d.dylib"
    elif system == "Windows":
        lib_name = "libtem1d.dll"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    lib_path = lib_dir / lib_name

    if not lib_path.exists():
        raise FileNotFoundError(
            f"TEM1D shared library not found at {lib_path}\n"
            f"Please run 'make' in the python/ directory to build it."
        )

    return lib_path


# Global library handle (loaded once)
_lib = None


def load_library() -> ctypes.CDLL:
    """
    Load the TEM1D shared library

    Returns
    -------
    ctypes.CDLL
        Loaded library handle

    Raises
    ------
    FileNotFoundError
        If library not found
    OSError
        If library cannot be loaded
    """
    global _lib
    if _lib is not None:
        return _lib

    lib_path = _get_library_path()

    try:
        _lib = ctypes.CDLL(str(lib_path))
    except OSError as e:
        raise OSError(f"Failed to load TEM1D library from {lib_path}: {e}")

    # Configure the TEM1D function interface
    _setup_tem1d_interface(_lib)

    return _lib


def _setup_tem1d_interface(lib: ctypes.CDLL) -> None:
    """
    Configure ctypes argument and return types for TEM1D subroutine

    Parameters
    ----------
    lib : ctypes.CDLL
        Loaded library handle
    """
    # Fortran subroutine name (with trailing underscore for gfortran)
    tem1d_func = lib.tem1d_

    # All arguments passed by reference (Fortran convention)
    # Order matches the TEM1D.for subroutine signature
    tem1d_func.argtypes = [
        # Model parameters
        ctypes.POINTER(ctypes.c_int32),  # IMLMi
        ctypes.POINTER(ctypes.c_int32),  # NLAYi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # RHONi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # DEPNi
        # IP parameters
        ctypes.POINTER(ctypes.c_int32),  # IMODIPi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # CHAIPi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # TAUIPi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # POWIPi
        # Instrument parameters
        ctypes.POINTER(ctypes.c_double),  # TXAREAi
        ctypes.POINTER(ctypes.c_double),  # RTXRXi
        ctypes.POINTER(ctypes.c_int32),  # IZEROPOSi
        ctypes.POINTER(ctypes.c_int32),  # ISHTX1i
        ctypes.POINTER(ctypes.c_int32),  # ISHTX2i
        ctypes.POINTER(ctypes.c_int32),  # ISHRX1i
        ctypes.POINTER(ctypes.c_int32),  # ISHRX2i
        ctypes.POINTER(ctypes.c_double),  # HTX1i
        ctypes.POINTER(ctypes.c_double),  # HTX2i
        ctypes.POINTER(ctypes.c_double),  # HRX1i
        ctypes.POINTER(ctypes.c_double),  # HRX2i
        # Polygon parameters
        ctypes.POINTER(ctypes.c_int32),  # NPOLYi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # XPOLYi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # YPOLYi
        ctypes.POINTER(ctypes.c_double),  # X0RXi
        ctypes.POINTER(ctypes.c_double),  # Y0RXi
        # Response parameters
        ctypes.POINTER(ctypes.c_int32),  # IRESPTYPEi
        ctypes.POINTER(ctypes.c_int32),  # IDERIVi
        ctypes.POINTER(ctypes.c_int32),  # IREPi
        ctypes.POINTER(ctypes.c_int32),  # IWCONVi
        ctypes.POINTER(ctypes.c_int32),  # NFILTi
        ctypes.POINTER(ctypes.c_double),  # REPFREQi
        ctypes.POINTER(ctypes.c_double * 16),  # FILTFREQi
        # Waveform parameters
        ctypes.POINTER(ctypes.c_int32),  # NWAVEi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # TWAVEi
        ctypes.POINTER(ctypes.c_double * N_ARR),  # AWAVEi
        # Outputs
        ctypes.POINTER(ctypes.c_int32),  # NTOUT
        ctypes.POINTER(ctypes.c_double * N_ARR),  # TIMESOUT
        ctypes.POINTER(ctypes.c_double * N_ARR),  # RESPOUT
        ctypes.POINTER((ctypes.c_double * N_ARR) * N_ARR),  # DRESPOUT
    ]

    # Subroutine has no return value
    tem1d_func.restype = None


def call_tem1d(
    model: EarthModel,
    instrument: Instrument,
    ip_model: Optional[IPModel] = None,
    polygon: Optional[PolygonLoop] = None,
    response_config: Optional[ResponseConfig] = None,
    waveform: Optional[Waveform] = None,
) -> TEM1DResult:
    """
    Call TEM1D Fortran subroutine

    Parameters
    ----------
    model : EarthModel
        Layered earth model
    instrument : Instrument
        Transmitter/receiver configuration
    ip_model : Optional[IPModel]
        Induced polarization model
    polygon : Optional[PolygonLoop]
        Polygonal transmitter loop
    response_config : Optional[ResponseConfig]
        Response calculation settings
    waveform : Optional[Waveform]
        Current waveform for convolution

    Returns
    -------
    TEM1DResult
        Computed TEM responses and derivatives

    Raises
    ------
    ValueError
        If input parameters are invalid
    RuntimeError
        If Fortran computation fails
    """
    # Validate all inputs
    validate_all(model, instrument, ip_model, polygon, response_config, waveform)

    # Load library
    lib = load_library()

    # Set defaults for optional parameters
    if response_config is None:
        response_config = ResponseConfig()
    if ip_model is None:
        ip_model = IPModel(
            chargeabilities=np.zeros(model.nlay),
            time_constants=np.ones(model.nlay),
            powers=np.ones(model.nlay) * 0.5,
            enabled=False,
        )

    # Prepare input arrays (all size N_ARR)
    # Model arrays
    rhon = (ctypes.c_double * N_ARR)()
    depn = (ctypes.c_double * N_ARR)()
    for i in range(model.nlay):
        rhon[i] = model.resistivities[i]
        depn[i] = model.depths[i]

    # IP arrays
    chaip = (ctypes.c_double * N_ARR)()
    tauip = (ctypes.c_double * N_ARR)()
    powip = (ctypes.c_double * N_ARR)()
    if ip_model.enabled:
        for i in range(model.nlay):
            chaip[i] = ip_model.chargeabilities[i]
            tauip[i] = ip_model.time_constants[i]
            powip[i] = ip_model.powers[i]

    # Polygon arrays
    xpoly = (ctypes.c_double * N_ARR)()
    ypoly = (ctypes.c_double * N_ARR)()
    npoly = 0
    x0rx = ctypes.c_double(0.0)
    y0rx = ctypes.c_double(0.0)
    if polygon is not None:
        npoly = polygon.n_vertices
        for i in range(npoly):
            xpoly[i] = polygon.x_coords[i]
            ypoly[i] = polygon.y_coords[i]
        x0rx = ctypes.c_double(polygon.rx_position[0])
        y0rx = ctypes.c_double(polygon.rx_position[1])

    # Filter arrays
    filtfreq = (ctypes.c_double * 16)()
    if response_config.apply_filters and response_config.filter_frequencies is not None:
        for i in range(response_config.nfilt):
            filtfreq[i] = response_config.filter_frequencies[i]

    # Waveform arrays
    twave = (ctypes.c_double * N_ARR)()
    awave = (ctypes.c_double * N_ARR)()
    nwave = 0
    if waveform is not None:
        nwave = waveform.nwave
        for i in range(nwave):
            twave[i] = waveform.times[i]
            awave[i] = waveform.amplitudes[i]

    # Prepare output arrays
    ntout = ctypes.c_int32(0)
    timesout = (ctypes.c_double * N_ARR)()
    respout = (ctypes.c_double * N_ARR)()
    drespout = ((ctypes.c_double * N_ARR) * N_ARR)()

    # Call Fortran subroutine
    try:
        lib.tem1d_(
            # Model parameters
            ctypes.byref(ctypes.c_int32(model.imlm)),
            ctypes.byref(ctypes.c_int32(model.nlay)),
            ctypes.byref(rhon),
            ctypes.byref(depn),
            # IP parameters
            ctypes.byref(ctypes.c_int32(1 if ip_model.enabled else 0)),
            ctypes.byref(chaip),
            ctypes.byref(tauip),
            ctypes.byref(powip),
            # Instrument parameters
            ctypes.byref(ctypes.c_double(instrument.tx_area)),
            ctypes.byref(ctypes.c_double(instrument.tx_rx_separation)),
            ctypes.byref(ctypes.c_int32(1 if instrument.zero_coupled else 0)),
            ctypes.byref(ctypes.c_int32(instrument.tx_polarity)),
            ctypes.byref(ctypes.c_int32(instrument.tx_polarity2)),
            ctypes.byref(ctypes.c_int32(instrument.rx_polarity)),
            ctypes.byref(ctypes.c_int32(instrument.rx_polarity2)),
            ctypes.byref(ctypes.c_double(instrument.tx_height)),
            ctypes.byref(ctypes.c_double(instrument.tx_height2)),
            ctypes.byref(ctypes.c_double(instrument.rx_height)),
            ctypes.byref(ctypes.c_double(instrument.rx_height2)),
            # Polygon parameters
            ctypes.byref(ctypes.c_int32(npoly)),
            ctypes.byref(xpoly),
            ctypes.byref(ypoly),
            ctypes.byref(x0rx),
            ctypes.byref(y0rx),
            # Response parameters
            ctypes.byref(ctypes.c_int32(response_config.iresptype)),
            ctypes.byref(ctypes.c_int32(response_config.ideriv)),
            ctypes.byref(ctypes.c_int32(1 if response_config.model_repetition else 0)),
            ctypes.byref(ctypes.c_int32(1 if response_config.response_type == "convolved" else 0)),
            ctypes.byref(ctypes.c_int32(response_config.nfilt)),
            ctypes.byref(ctypes.c_double(response_config.repetition_frequency)),
            ctypes.byref(filtfreq),
            # Waveform parameters
            ctypes.byref(ctypes.c_int32(nwave)),
            ctypes.byref(twave),
            ctypes.byref(awave),
            # Outputs
            ctypes.byref(ntout),
            ctypes.byref(timesout),
            ctypes.byref(respout),
            ctypes.byref(drespout),
        )
    except Exception as e:
        raise RuntimeError(f"TEM1D Fortran call failed: {e}")

    # Extract results (only used portion up to ntout)
    n = ntout.value
    if n <= 0:
        raise RuntimeError("TEM1D returned no data points")

    times = np.array([timesout[i] for i in range(n)])
    responses = np.array([respout[i] for i in range(n)])

    # Extract derivatives if calculated
    derivatives = None
    if response_config.calculate_derivatives:
        # Determine number of parameters
        if model.imlm == 0:
            # Few-layer: conductivities + thicknesses + tx_height
            n_params = model.nlay + (model.nlay - 1) + 1
        else:
            # Multi-layer: only conductivities + tx_height
            n_params = model.nlay + 1

        # Extract derivative matrix (ntout x n_params)
        # Note: Fortran stores column-major, need to transpose
        derivatives = np.zeros((n, n_params))
        for i in range(n):
            for j in range(n_params):
                derivatives[i, j] = drespout[j][i]  # Transpose

    # Create result object
    metadata = {
        "nlay": model.nlay,
        "imlm": model.imlm,
        "has_ip": ip_model.enabled,
        "has_polygon": polygon is not None,
        "response_type": response_config.response_type,
    }

    return TEM1DResult(
        times=times, responses=responses, derivatives=derivatives, metadata=metadata
    )
