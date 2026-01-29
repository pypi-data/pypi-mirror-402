"""
Data models for TEM1D parameters and results

This module defines dataclasses for organizing TEM1D input parameters
and output results in a type-safe manner.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np


@dataclass
class EarthModel:
    """
    Layered earth model parameters

    Attributes
    ----------
    resistivities : np.ndarray
        Layer resistivities in Ohm-m (positive values)
    depths : np.ndarray
        Depths to top of each layer in meters (first must be 0)
    imlm : int
        Model type: 0=few-layer (only conductivity derivatives),
                   1=multi-layer (conductivity + thickness derivatives)
    """

    resistivities: np.ndarray
    depths: np.ndarray
    imlm: int = 0

    def __post_init__(self):
        self.resistivities = np.asarray(self.resistivities, dtype=np.float64)
        self.depths = np.asarray(self.depths, dtype=np.float64)

    @property
    def nlay(self) -> int:
        """Number of layers"""
        return len(self.resistivities)

    @property
    def conductivities(self) -> np.ndarray:
        """Layer conductivities (1/resistivity) in S/m"""
        return 1.0 / self.resistivities


@dataclass
class IPModel:
    """
    Induced polarization (Cole-Cole) model parameters

    Attributes
    ----------
    chargeabilities : np.ndarray
        Chargeability for each layer (dimensionless, 0-1)
    time_constants : np.ndarray
        Time constant tau for each layer in seconds (positive)
    powers : np.ndarray
        Cole-Cole exponent c for each layer (dimensionless, 0-1)
    enabled : bool
        Whether IP effects are enabled
    """

    chargeabilities: np.ndarray
    time_constants: np.ndarray
    powers: np.ndarray
    enabled: bool = True

    def __post_init__(self):
        self.chargeabilities = np.asarray(self.chargeabilities, dtype=np.float64)
        self.time_constants = np.asarray(self.time_constants, dtype=np.float64)
        self.powers = np.asarray(self.powers, dtype=np.float64)


@dataclass
class Instrument:
    """
    Transmitter and receiver configuration

    Attributes
    ----------
    tx_area : float
        Transmitter loop area in m² (positive)
    tx_rx_separation : float
        TX-RX horizontal separation in meters (0 = central loop)
    tx_height : float
        Transmitter height in meters (positive = above surface)
    rx_height : float
        Receiver height in meters
    tx_height2 : float
        Second transmitter height (for multi-height configurations)
    rx_height2 : float
        Second receiver height
    tx_polarity : int
        Transmitter polarity: -1, 0, or 1
    rx_polarity : int
        Receiver polarity: -1, 0, or 1
    tx_polarity2 : int
        Second transmitter polarity
    rx_polarity2 : int
        Second receiver polarity
    zero_coupled : bool
        Calculate equivalent zero-coupled position
    """

    tx_area: float
    tx_rx_separation: float = 0.0
    tx_height: float = 1.0
    rx_height: float = 1.0
    tx_height2: float = 0.0
    rx_height2: float = 0.0
    tx_polarity: int = 1
    rx_polarity: int = 1
    tx_polarity2: int = 0
    rx_polarity2: int = 0
    zero_coupled: bool = False


@dataclass
class PolygonLoop:
    """
    Polygonal transmitter loop configuration

    Attributes
    ----------
    vertices : np.ndarray
        Nx2 array of (x, y) coordinates of polygon vertices in meters
        Vertices should be ordered counterclockwise
    rx_position : Tuple[float, float]
        (x, y) position of receiver in loop plane, in meters
    """

    vertices: np.ndarray
    rx_position: Tuple[float, float] = (0.0, 0.0)

    def __post_init__(self):
        self.vertices = np.asarray(self.vertices, dtype=np.float64)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 2:
            raise ValueError("vertices must be Nx2 array")

    @property
    def n_vertices(self) -> int:
        """Number of polygon vertices"""
        return len(self.vertices)

    @property
    def x_coords(self) -> np.ndarray:
        """X coordinates of vertices"""
        return self.vertices[:, 0]

    @property
    def y_coords(self) -> np.ndarray:
        """Y coordinates of vertices"""
        return self.vertices[:, 1]


@dataclass
class ResponseConfig:
    """
    Response calculation configuration

    Attributes
    ----------
    response_type : str
        Type of response: 'step', 'impulse', or 'convolved'
    calculate_derivatives : bool
        Whether to calculate Jacobian matrix
    apply_filters : bool
        Whether to apply frequency filters
    filter_frequencies : Optional[np.ndarray]
        Filter cutoff frequencies in Hz (if apply_filters=True)
    model_repetition : bool
        Whether to model pulse repetition
    repetition_frequency : float
        Repetition frequency in Hz (if model_repetition=True)
    """

    response_type: str = "step"
    calculate_derivatives: bool = False
    apply_filters: bool = False
    filter_frequencies: Optional[np.ndarray] = None
    model_repetition: bool = False
    repetition_frequency: float = 0.0

    def __post_init__(self):
        valid_types = ["step", "impulse", "convolved"]
        if self.response_type not in valid_types:
            raise ValueError(f"response_type must be one of {valid_types}")
        if self.filter_frequencies is not None:
            self.filter_frequencies = np.asarray(self.filter_frequencies, dtype=np.float64)

    @property
    def iresptype(self) -> int:
        """Convert response type to integer code"""
        return {"step": 0, "impulse": 1, "convolved": 2}[self.response_type]

    @property
    def ideriv(self) -> int:
        """Derivative flag as integer"""
        return 1 if self.calculate_derivatives else 0

    @property
    def nfilt(self) -> int:
        """Number of filters"""
        if not self.apply_filters or self.filter_frequencies is None:
            return 0
        return len(self.filter_frequencies)


@dataclass
class Waveform:
    """
    Current waveform for convolution

    Attributes
    ----------
    times : np.ndarray
        Time values in seconds (should span turn-off period)
    amplitudes : np.ndarray
        Current amplitude values (normalized, typically 0-1)
    """

    times: np.ndarray
    amplitudes: np.ndarray

    def __post_init__(self):
        self.times = np.asarray(self.times, dtype=np.float64)
        self.amplitudes = np.asarray(self.amplitudes, dtype=np.float64)
        if len(self.times) != len(self.amplitudes):
            raise ValueError("times and amplitudes must have same length")

    @property
    def nwave(self) -> int:
        """Number of waveform points"""
        return len(self.times)


@dataclass
class TEM1DResult:
    """
    Results from TEM1D forward modeling

    Attributes
    ----------
    times : np.ndarray
        Time gate values in seconds
    responses : np.ndarray
        dB/dt responses in V/(A·m²)
    derivatives : Optional[np.ndarray]
        Jacobian matrix (n_times x n_params) if calculated, None otherwise
        Parameters ordered as: conductivities (all layers), thicknesses (n_layers-1), tx_height
    metadata : dict
        Additional metadata about the computation
    """

    times: np.ndarray
    responses: np.ndarray
    derivatives: Optional[np.ndarray] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.times = np.asarray(self.times, dtype=np.float64)
        self.responses = np.asarray(self.responses, dtype=np.float64)
        if self.derivatives is not None:
            self.derivatives = np.asarray(self.derivatives, dtype=np.float64)

    @property
    def n_times(self) -> int:
        """Number of time gates"""
        return len(self.times)

    @property
    def n_params(self) -> int:
        """Number of model parameters (if derivatives computed)"""
        if self.derivatives is None:
            return 0
        return self.derivatives.shape[1]

    def __repr__(self) -> str:
        result = f"TEM1DResult(n_times={self.n_times}"
        if self.derivatives is not None:
            result += f", n_params={self.n_params}"
        result += ")"
        return result
