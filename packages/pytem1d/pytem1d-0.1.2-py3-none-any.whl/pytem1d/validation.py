"""
Parameter validation for TEM1D inputs

This module provides validation functions to check that all input parameters
are physically reasonable and within the constraints of the TEM1D code.
"""

import numpy as np
from typing import Optional
from .models import (
    EarthModel,
    IPModel,
    Instrument,
    PolygonLoop,
    ResponseConfig,
    Waveform,
)

# Constants from ARRAYSDIMBL.INC
N_ARR = 512  # Maximum array size in Fortran code
MAX_FILTERS = 16  # Maximum number of frequency filters


def validate_earth_model(model: EarthModel) -> None:
    """
    Validate layered earth model parameters

    Parameters
    ----------
    model : EarthModel
        Earth model to validate

    Raises
    ------
    ValueError
        If model parameters are invalid
    """
    nlay = model.nlay

    # Check number of layers
    if nlay < 1:
        raise ValueError("Must have at least 1 layer")
    if nlay > N_ARR:
        raise ValueError(f"Number of layers ({nlay}) exceeds maximum ({N_ARR})")

    # Check resistivities
    if np.any(model.resistivities <= 0):
        raise ValueError("All resistivities must be positive")
    if np.any(~np.isfinite(model.resistivities)):
        raise ValueError("All resistivities must be finite")

    # Check depths
    if model.depths[0] != 0:
        raise ValueError("First depth must be 0 (surface)")
    if np.any(np.diff(model.depths) <= 0):
        raise ValueError("Depths must be monotonically increasing")
    if np.any(~np.isfinite(model.depths)):
        raise ValueError("All depths must be finite")

    # Check imlm
    if model.imlm not in [0, 1]:
        raise ValueError("imlm must be 0 or 1")


def validate_ip_model(ip_model: IPModel, nlay: int) -> None:
    """
    Validate induced polarization parameters

    Parameters
    ----------
    ip_model : IPModel
        IP model to validate
    nlay : int
        Number of layers in earth model

    Raises
    ------
    ValueError
        If IP parameters are invalid
    """
    # Check array lengths
    if len(ip_model.chargeabilities) != nlay:
        raise ValueError(f"chargeabilities length ({len(ip_model.chargeabilities)}) must match nlay ({nlay})")
    if len(ip_model.time_constants) != nlay:
        raise ValueError(f"time_constants length ({len(ip_model.time_constants)}) must match nlay ({nlay})")
    if len(ip_model.powers) != nlay:
        raise ValueError(f"powers length ({len(ip_model.powers)}) must match nlay ({nlay})")

    # Check chargeabilities
    if np.any(ip_model.chargeabilities < 0) or np.any(ip_model.chargeabilities > 1):
        raise ValueError("Chargeabilities must be between 0 and 1")

    # Check time constants
    if np.any(ip_model.time_constants <= 0):
        raise ValueError("Time constants must be positive")
    if np.any(~np.isfinite(ip_model.time_constants)):
        raise ValueError("Time constants must be finite")

    # Check powers
    if np.any(ip_model.powers < 0) or np.any(ip_model.powers > 1):
        raise ValueError("Cole-Cole powers must be between 0 and 1")


def validate_instrument(instrument: Instrument) -> None:
    """
    Validate instrument configuration

    Parameters
    ----------
    instrument : Instrument
        Instrument configuration to validate

    Raises
    ------
    ValueError
        If instrument parameters are invalid
    """
    # Check transmitter area
    if instrument.tx_area <= 0:
        raise ValueError("Transmitter area must be positive")
    if not np.isfinite(instrument.tx_area):
        raise ValueError("Transmitter area must be finite")

    # Check TX-RX separation
    if instrument.tx_rx_separation < 0:
        raise ValueError("TX-RX separation must be non-negative")
    if not np.isfinite(instrument.tx_rx_separation):
        raise ValueError("TX-RX separation must be finite")

    # Check polarities
    valid_polarities = [-1, 0, 1]
    if instrument.tx_polarity not in valid_polarities:
        raise ValueError(f"TX polarity must be one of {valid_polarities}")
    if instrument.rx_polarity not in valid_polarities:
        raise ValueError(f"RX polarity must be one of {valid_polarities}")
    if instrument.tx_polarity2 not in valid_polarities:
        raise ValueError(f"TX2 polarity must be one of {valid_polarities}")
    if instrument.rx_polarity2 not in valid_polarities:
        raise ValueError(f"RX2 polarity must be one of {valid_polarities}")

    # Check heights are finite
    heights = [
        instrument.tx_height,
        instrument.rx_height,
        instrument.tx_height2,
        instrument.rx_height2,
    ]
    if not all(np.isfinite(h) for h in heights):
        raise ValueError("All heights must be finite")


def validate_polygon_loop(polygon: PolygonLoop) -> None:
    """
    Validate polygonal loop configuration

    Parameters
    ----------
    polygon : PolygonLoop
        Polygon configuration to validate

    Raises
    ------
    ValueError
        If polygon parameters are invalid
    """
    nvert = polygon.n_vertices

    # Check number of vertices
    if nvert < 3:
        raise ValueError(f"Polygon must have at least 3 vertices (got {nvert})")
    if nvert > N_ARR:
        raise ValueError(f"Number of vertices ({nvert}) exceeds maximum ({N_ARR})")

    # Check vertices are finite
    if not np.all(np.isfinite(polygon.vertices)):
        raise ValueError("All polygon vertices must be finite")

    # Check receiver position is finite
    if not all(np.isfinite(x) for x in polygon.rx_position):
        raise ValueError("Receiver position must be finite")


def validate_response_config(config: ResponseConfig) -> None:
    """
    Validate response calculation configuration

    Parameters
    ----------
    config : ResponseConfig
        Response configuration to validate

    Raises
    ------
    ValueError
        If configuration is invalid
    """
    # Response type already validated in __post_init__

    # Check filters
    if config.apply_filters:
        if config.filter_frequencies is None:
            raise ValueError("filter_frequencies required when apply_filters=True")
        if len(config.filter_frequencies) > MAX_FILTERS:
            raise ValueError(
                f"Number of filters ({len(config.filter_frequencies)}) "
                f"exceeds maximum ({MAX_FILTERS})"
            )
        if np.any(config.filter_frequencies <= 0):
            raise ValueError("All filter frequencies must be positive")
        if not np.all(np.isfinite(config.filter_frequencies)):
            raise ValueError("All filter frequencies must be finite")

    # Check repetition settings
    if config.model_repetition:
        if config.repetition_frequency <= 0:
            raise ValueError("Repetition frequency must be positive")
        if not np.isfinite(config.repetition_frequency):
            raise ValueError("Repetition frequency must be finite")


def validate_waveform(waveform: Waveform) -> None:
    """
    Validate current waveform

    Parameters
    ----------
    waveform : Waveform
        Waveform to validate

    Raises
    ------
    ValueError
        If waveform is invalid
    """
    nwave = waveform.nwave

    # Check number of points
    if nwave < 2:
        raise ValueError(f"Waveform must have at least 2 points (got {nwave})")
    if nwave > N_ARR:
        raise ValueError(f"Number of waveform points ({nwave}) exceeds maximum ({N_ARR})")

    # Check times and amplitudes are finite
    if not np.all(np.isfinite(waveform.times)):
        raise ValueError("All waveform times must be finite")
    if not np.all(np.isfinite(waveform.amplitudes)):
        raise ValueError("All waveform amplitudes must be finite")

    # Check times are strictly increasing
    if np.any(np.diff(waveform.times) <= 0):
        raise ValueError("Waveform times must be strictly increasing")


def validate_all(
    model: EarthModel,
    instrument: Instrument,
    ip_model: Optional[IPModel] = None,
    polygon: Optional[PolygonLoop] = None,
    response_config: Optional[ResponseConfig] = None,
    waveform: Optional[Waveform] = None,
) -> None:
    """
    Validate all input parameters

    Parameters
    ----------
    model : EarthModel
        Earth model
    instrument : Instrument
        Instrument configuration
    ip_model : Optional[IPModel]
        IP model (if IP effects enabled)
    polygon : Optional[PolygonLoop]
        Polygon loop (if using polygonal TX)
    response_config : Optional[ResponseConfig]
        Response configuration
    waveform : Optional[Waveform]
        Current waveform (if using convolution)

    Raises
    ------
    ValueError
        If any parameters are invalid
    """
    validate_earth_model(model)
    validate_instrument(instrument)

    if ip_model is not None and ip_model.enabled:
        validate_ip_model(ip_model, model.nlay)

    if polygon is not None:
        validate_polygon_loop(polygon)

    if response_config is not None:
        validate_response_config(response_config)

    if waveform is not None:
        validate_waveform(waveform)

    # Cross-validation
    if response_config is not None:
        if response_config.response_type == "convolved" and waveform is None:
            raise ValueError("Waveform required for convolved response type")
