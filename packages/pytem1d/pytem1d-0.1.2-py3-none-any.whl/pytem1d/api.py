"""
High-level API for TEM1D forward modeling

This module provides both functional and class-based interfaces to TEM1D,
making it easy to run forward models with intuitive Python syntax.
"""

import numpy as np
from typing import Optional, Union, List, Tuple, Dict, Any
from numpy.typing import ArrayLike

from .models import (
    EarthModel,
    IPModel,
    Instrument,
    PolygonLoop,
    ResponseConfig,
    Waveform,
    TEM1DResult,
)
from .core import call_tem1d


def run_tem1d(
    resistivities: ArrayLike,
    depths: ArrayLike,
    tx_area: float = 314.16,
    tx_rx_separation: float = 0.0,
    tx_height: float = 1.0,
    rx_height: float = 1.0,
    calculate_derivatives: bool = False,
    imlm: int = 0,
    ip_params: Optional[Dict[str, ArrayLike]] = None,
    polygon_vertices: Optional[ArrayLike] = None,
    rx_position: Tuple[float, float] = (0.0, 0.0),
    response_type: str = "step",
    waveform: Optional[Dict[str, ArrayLike]] = None,
    filter_frequencies: Optional[ArrayLike] = None,
    model_repetition: bool = False,
    repetition_frequency: float = 0.0,
    **kwargs,
) -> TEM1DResult:
    """
    Run TEM1D forward modeling (functional interface)

    Parameters
    ----------
    resistivities : array-like
        Layer resistivities in Ohm-m (positive values)
    depths : array-like
        Depths to top of each layer in meters (first must be 0)
    tx_area : float, optional
        Transmitter loop area in m² (default: 314.16, radius ~10m)
    tx_rx_separation : float, optional
        TX-RX horizontal separation in meters (default: 0 = central loop)
    tx_height : float, optional
        Transmitter height in meters (default: 1.0)
    rx_height : float, optional
        Receiver height in meters (default: 1.0)
    calculate_derivatives : bool, optional
        Calculate Jacobian matrix for inversion (default: False)
    imlm : int, optional
        Model type: 0=few-layer, 1=multi-layer (default: 0)
    ip_params : dict, optional
        IP parameters with keys: 'chargeabilities', 'time_constants', 'powers'
    polygon_vertices : array-like, optional
        Nx2 array of polygon vertex coordinates (if using non-circular TX)
    rx_position : tuple, optional
        (x, y) receiver position for polygon loops (default: (0, 0))
    response_type : str, optional
        Response type: 'step', 'impulse', or 'convolved' (default: 'step')
    waveform : dict, optional
        Waveform with keys: 'times', 'amplitudes' (required for convolved)
    filter_frequencies : array-like, optional
        Low-pass filter cutoff frequencies in Hz
    model_repetition : bool, optional
        Model pulse repetition (default: False)
    repetition_frequency : float, optional
        Repetition frequency in Hz (if model_repetition=True)

    Returns
    -------
    TEM1DResult
        Results with times, responses, and optionally derivatives

    Examples
    --------
    Simple 2-layer model:

    >>> result = run_tem1d([100, 10], [0, 50])
    >>> import matplotlib.pyplot as plt
    >>> plt.loglog(result.times, abs(result.responses))

    With IP effects:

    >>> result = run_tem1d(
    ...     resistivities=[100, 10, 50],
    ...     depths=[0, 30, 100],
    ...     ip_params={
    ...         'chargeabilities': [0.1, 0.3, 0.05],
    ...         'time_constants': [0.01, 0.05, 0.001],
    ...         'powers': [0.5, 0.4, 0.6]
    ...     }
    ... )

    With derivatives for inversion:

    >>> result = run_tem1d([100, 10], [0, 50], calculate_derivatives=True)
    >>> print(result.derivatives.shape)  # (n_times, n_params)
    """
    # Build earth model
    model = EarthModel(
        resistivities=np.asarray(resistivities),
        depths=np.asarray(depths),
        imlm=imlm,
    )

    # Build instrument configuration
    instrument = Instrument(
        tx_area=tx_area,
        tx_rx_separation=tx_rx_separation,
        tx_height=tx_height,
        rx_height=rx_height,
        tx_polarity=kwargs.get("tx_polarity", 1),
        rx_polarity=kwargs.get("rx_polarity", 1),
        tx_height2=kwargs.get("tx_height2", 0.0),
        rx_height2=kwargs.get("rx_height2", 0.0),
        tx_polarity2=kwargs.get("tx_polarity2", 0),
        rx_polarity2=kwargs.get("rx_polarity2", 0),
        zero_coupled=kwargs.get("zero_coupled", False),
    )

    # Build IP model if provided
    ip_model = None
    if ip_params is not None:
        ip_model = IPModel(
            chargeabilities=np.asarray(ip_params["chargeabilities"]),
            time_constants=np.asarray(ip_params["time_constants"]),
            powers=np.asarray(ip_params["powers"]),
            enabled=True,
        )

    # Build polygon if provided
    polygon = None
    if polygon_vertices is not None:
        polygon = PolygonLoop(
            vertices=np.asarray(polygon_vertices),
            rx_position=rx_position,
        )

    # Build response configuration
    response_config = ResponseConfig(
        response_type=response_type,
        calculate_derivatives=calculate_derivatives,
        apply_filters=filter_frequencies is not None,
        filter_frequencies=np.asarray(filter_frequencies) if filter_frequencies is not None else None,
        model_repetition=model_repetition,
        repetition_frequency=repetition_frequency,
    )

    # Build waveform if provided
    waveform_obj = None
    if waveform is not None:
        waveform_obj = Waveform(
            times=np.asarray(waveform["times"]),
            amplitudes=np.asarray(waveform["amplitudes"]),
        )

    # Call core function
    return call_tem1d(
        model=model,
        instrument=instrument,
        ip_model=ip_model,
        polygon=polygon,
        response_config=response_config,
        waveform=waveform_obj,
    )


class TEM1DModel:
    """
    TEM1D forward modeling (class-based interface)

    This class provides a stateful interface for running TEM1D forward models,
    useful when you want to vary parameters and run multiple times.

    Examples
    --------
    Basic usage:

    >>> tem = TEM1DModel()
    >>> tem.set_earth_model([100, 10], [0, 50])
    >>> tem.set_instrument(tx_area=314.16)
    >>> result = tem.run()

    With IP effects:

    >>> tem = TEM1DModel()
    >>> tem.set_earth_model([100, 10, 50], [0, 30, 100])
    >>> tem.set_ip_model([0.1, 0.3, 0.05], [0.01, 0.05, 0.001], [0.5, 0.4, 0.6])
    >>> tem.set_instrument(tx_area=314.16)
    >>> result = tem.run()

    Batch processing:

    >>> tem = TEM1DModel()
    >>> tem.set_instrument(tx_area=314.16)
    >>> resistivity_sets = [[100, 10], [200, 20], [50, 5]]
    >>> results = []
    >>> for rho in resistivity_sets:
    ...     tem.set_earth_model(rho, [0, 50])
    ...     results.append(tem.run())
    """

    def __init__(self):
        """Initialize empty TEM1D model"""
        self._model: Optional[EarthModel] = None
        self._ip_model: Optional[IPModel] = None
        self._instrument: Optional[Instrument] = None
        self._polygon: Optional[PolygonLoop] = None
        self._response_config = ResponseConfig()
        self._waveform: Optional[Waveform] = None

    def set_earth_model(
        self,
        resistivities: ArrayLike,
        depths: ArrayLike,
        imlm: int = 0,
    ) -> "TEM1DModel":
        """
        Set layered earth model

        Parameters
        ----------
        resistivities : array-like
            Layer resistivities in Ohm-m
        depths : array-like
            Depths to layer tops in meters (first must be 0)
        imlm : int, optional
            Model type: 0=few-layer, 1=multi-layer

        Returns
        -------
        self
            For method chaining
        """
        self._model = EarthModel(
            resistivities=np.asarray(resistivities),
            depths=np.asarray(depths),
            imlm=imlm,
        )
        return self

    def set_ip_model(
        self,
        chargeabilities: ArrayLike,
        time_constants: ArrayLike,
        powers: ArrayLike,
    ) -> "TEM1DModel":
        """
        Enable IP effects with Cole-Cole model

        Parameters
        ----------
        chargeabilities : array-like
            Chargeability for each layer (0-1)
        time_constants : array-like
            Time constant tau for each layer in seconds
        powers : array-like
            Cole-Cole exponent c for each layer (0-1)

        Returns
        -------
        self
            For method chaining
        """
        self._ip_model = IPModel(
            chargeabilities=np.asarray(chargeabilities),
            time_constants=np.asarray(time_constants),
            powers=np.asarray(powers),
            enabled=True,
        )
        return self

    def disable_ip(self) -> "TEM1DModel":
        """Disable IP effects"""
        self._ip_model = None
        return self

    def set_instrument(
        self,
        tx_area: float,
        tx_rx_separation: float = 0.0,
        tx_height: float = 1.0,
        rx_height: float = 1.0,
        **kwargs,
    ) -> "TEM1DModel":
        """
        Configure transmitter and receiver

        Parameters
        ----------
        tx_area : float
            Transmitter loop area in m²
        tx_rx_separation : float, optional
            TX-RX separation in meters (0 = central loop)
        tx_height : float, optional
            Transmitter height in meters
        rx_height : float, optional
            Receiver height in meters
        **kwargs
            Additional instrument parameters

        Returns
        -------
        self
            For method chaining
        """
        self._instrument = Instrument(
            tx_area=tx_area,
            tx_rx_separation=tx_rx_separation,
            tx_height=tx_height,
            rx_height=rx_height,
            tx_polarity=kwargs.get("tx_polarity", 1),
            rx_polarity=kwargs.get("rx_polarity", 1),
            tx_height2=kwargs.get("tx_height2", 0.0),
            rx_height2=kwargs.get("rx_height2", 0.0),
            tx_polarity2=kwargs.get("tx_polarity2", 0),
            rx_polarity2=kwargs.get("rx_polarity2", 0),
            zero_coupled=kwargs.get("zero_coupled", False),
        )
        return self

    def set_polygon_loop(
        self,
        vertices: ArrayLike,
        rx_position: Tuple[float, float] = (0.0, 0.0),
    ) -> "TEM1DModel":
        """
        Use polygonal transmitter instead of circular

        Parameters
        ----------
        vertices : array-like
            Nx2 array of (x, y) vertex coordinates
        rx_position : tuple, optional
            (x, y) receiver position

        Returns
        -------
        self
            For method chaining
        """
        self._polygon = PolygonLoop(
            vertices=np.asarray(vertices),
            rx_position=rx_position,
        )
        return self

    def set_waveform(
        self,
        times: ArrayLike,
        amplitudes: ArrayLike,
    ) -> "TEM1DModel":
        """
        Set current waveform for convolution

        Parameters
        ----------
        times : array-like
            Time values in seconds
        amplitudes : array-like
            Current amplitude values

        Returns
        -------
        self
            For method chaining
        """
        self._waveform = Waveform(
            times=np.asarray(times),
            amplitudes=np.asarray(amplitudes),
        )
        # Automatically switch to convolved response
        self._response_config.response_type = "convolved"
        return self

    def enable_derivatives(self, enable: bool = True) -> "TEM1DModel":
        """
        Enable or disable Jacobian calculation

        Parameters
        ----------
        enable : bool
            Whether to calculate derivatives

        Returns
        -------
        self
            For method chaining
        """
        self._response_config.calculate_derivatives = enable
        return self

    def set_response_type(self, response_type: str) -> "TEM1DModel":
        """
        Set response type

        Parameters
        ----------
        response_type : str
            'step', 'impulse', or 'convolved'

        Returns
        -------
        self
            For method chaining
        """
        self._response_config.response_type = response_type
        return self

    def run(self) -> TEM1DResult:
        """
        Execute forward modeling

        Returns
        -------
        TEM1DResult
            Computed responses and derivatives

        Raises
        ------
        ValueError
            If required parameters not set
        """
        if self._model is None:
            raise ValueError("Earth model not set. Call set_earth_model() first.")
        if self._instrument is None:
            raise ValueError("Instrument not set. Call set_instrument() first.")

        return call_tem1d(
            model=self._model,
            instrument=self._instrument,
            ip_model=self._ip_model,
            polygon=self._polygon,
            response_config=self._response_config,
            waveform=self._waveform,
        )

    def run_batch(
        self,
        resistivity_sets: List[ArrayLike],
        depths_sets: Optional[List[ArrayLike]] = None,
    ) -> List[TEM1DResult]:
        """
        Run multiple models efficiently

        Parameters
        ----------
        resistivity_sets : list of array-like
            List of resistivity arrays to run
        depths_sets : list of array-like, optional
            List of depth arrays (if None, reuse current depths)

        Returns
        -------
        list of TEM1DResult
            Results for each model

        Examples
        --------
        >>> tem = TEM1DModel()
        >>> tem.set_instrument(tx_area=314.16)
        >>> resistivities = [[100, 10], [200, 20], [50, 5]]
        >>> results = tem.run_batch(resistivities, depths_sets=[[0, 50]] * 3)
        """
        if self._model is None and depths_sets is None:
            raise ValueError("Must set earth model or provide depths_sets")

        results = []
        for i, rho in enumerate(resistivity_sets):
            if depths_sets is not None:
                depths = depths_sets[i]
            else:
                depths = self._model.depths

            self.set_earth_model(rho, depths, imlm=self._model.imlm if self._model else 0)
            results.append(self.run())

        return results
