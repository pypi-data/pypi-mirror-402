"""
I/O utilities for TEM1D results and parameters

This module provides functions to save/load results and convert between
different file formats.
"""

import json
import numpy as np
from pathlib import Path
from typing import Union, Dict, Any

from .models import TEM1DResult, EarthModel, Instrument


def save_result(
    result: TEM1DResult,
    filepath: Union[str, Path],
    format: str = "npz",
) -> None:
    """
    Save TEM1D result to file

    Parameters
    ----------
    result : TEM1DResult
        Result to save
    filepath : str or Path
        Output file path
    format : str, optional
        File format: 'npz' (NumPy), 'csv', or 'json' (default: 'npz')

    Examples
    --------
    >>> save_result(result, "output.npz")
    >>> save_result(result, "output.csv", format="csv")
    """
    filepath = Path(filepath)

    if format == "npz":
        data = {
            "times": result.times,
            "responses": result.responses,
        }
        if result.derivatives is not None:
            data["derivatives"] = result.derivatives
        if result.metadata:
            # Store metadata as separate arrays
            for key, value in result.metadata.items():
                data[f"metadata_{key}"] = np.array([value])
        np.savez(filepath, **data)

    elif format == "csv":
        # CSV format: times, responses, [derivatives...]
        if result.derivatives is not None:
            data = np.column_stack([result.times, result.responses, result.derivatives])
            header = "time,response," + ",".join(
                f"deriv_{i}" for i in range(result.n_params)
            )
        else:
            data = np.column_stack([result.times, result.responses])
            header = "time,response"
        np.savetxt(filepath, data, delimiter=",", header=header, comments="")

    elif format == "json":
        data = {
            "times": result.times.tolist(),
            "responses": result.responses.tolist(),
            "metadata": result.metadata,
        }
        if result.derivatives is not None:
            data["derivatives"] = result.derivatives.tolist()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    else:
        raise ValueError(f"Unknown format: {format}. Use 'npz', 'csv', or 'json'")


def load_result(filepath: Union[str, Path]) -> TEM1DResult:
    """
    Load TEM1D result from file

    Parameters
    ----------
    filepath : str or Path
        Input file path (must be .npz format)

    Returns
    -------
    TEM1DResult
        Loaded result

    Examples
    --------
    >>> result = load_result("output.npz")
    """
    filepath = Path(filepath)

    if filepath.suffix == ".npz":
        data = np.load(filepath)
        times = data["times"]
        responses = data["responses"]
        derivatives = data["derivatives"] if "derivatives" in data else None

        # Extract metadata
        metadata = {}
        for key in data.files:
            if key.startswith("metadata_"):
                meta_key = key.replace("metadata_", "")
                value = data[key]
                metadata[meta_key] = value.item() if value.size == 1 else value

        return TEM1DResult(
            times=times,
            responses=responses,
            derivatives=derivatives,
            metadata=metadata,
        )
    else:
        raise ValueError("Only .npz format supported for loading")


def read_forwrite(filepath: Union[str, Path] = "FORWRITE") -> TEM1DResult:
    """
    Read FORWRITE output from TEMTEST program

    This is useful for comparing Python wrapper results with the original
    Fortran TEMTEST program.

    Parameters
    ----------
    filepath : str or Path, optional
        Path to FORWRITE file (default: "FORWRITE")

    Returns
    -------
    TEM1DResult
        Parsed result

    Examples
    --------
    >>> result = read_forwrite("examples/output_example1/FORWRITE")
    """
    filepath = Path(filepath)

    with open(filepath, "r") as f:
        lines = f.readlines()

    # Parse line 1: times
    times = np.array([float(x) for x in lines[0].split()])

    # Parse line 2: responses
    responses = np.array([float(x) for x in lines[1].split()])

    # Parse remaining lines: derivatives (if present)
    derivatives = None
    if len(lines) > 2:
        deriv_lines = []
        for line in lines[2:]:
            values = [float(x) for x in line.split()]
            if values:  # Skip empty lines
                deriv_lines.append(values)
        if deriv_lines:
            derivatives = np.array(deriv_lines)  # Shape: (n_params, n_times)
            derivatives = derivatives.T  # Transpose to (n_times, n_params)

    return TEM1DResult(
        times=times,
        responses=responses,
        derivatives=derivatives,
        metadata={"source": "FORWRITE"},
    )


def write_forread(
    model: EarthModel,
    instrument: Instrument,
    filepath: Union[str, Path] = "FORREAD",
    **kwargs,
) -> None:
    """
    Write parameters in FORREAD format for TEMTEST program

    Useful for debugging and comparing with original Fortran code.

    Parameters
    ----------
    model : EarthModel
        Earth model parameters
    instrument : Instrument
        Instrument configuration
    filepath : str or Path, optional
        Output file path (default: "FORREAD")
    **kwargs
        Additional parameters (ip_model, polygon, response_config, etc.)

    Examples
    --------
    >>> model = EarthModel([100, 10], [0, 50])
    >>> instrument = Instrument(tx_area=314.16)
    >>> write_forread(model, instrument, "test_input.txt")
    """
    filepath = Path(filepath)

    ip_model = kwargs.get("ip_model")
    polygon = kwargs.get("polygon")
    response_config = kwargs.get("response_config")
    waveform = kwargs.get("waveform")

    lines = []

    # Model parameters
    lines.append("MODEL PARAMETERS")
    lines.append(str(model.imlm))
    lines.append(str(model.nlay))
    for i in range(model.nlay):
        lines.append(f"{model.resistivities[i]:.6e}   {model.depths[i]:.6e}")

    # IP parameters
    lines.append("IP PARAMETERS")
    if ip_model is not None and ip_model.enabled:
        lines.append("1")
        for i in range(model.nlay):
            lines.append(
                f"{ip_model.chargeabilities[i]:.6e}   "
                f"{ip_model.time_constants[i]:.6e}   "
                f"{ip_model.powers[i]:.6e}"
            )
    else:
        lines.append("0")

    # Instrument parameters
    lines.append("INSTRUMENT PARAMETERS")
    lines.append(f"{instrument.tx_area:.6e}")
    lines.append(str(instrument.tx_polarity))
    lines.append(str(instrument.rx_polarity))
    lines.append(str(instrument.tx_polarity2))
    lines.append(str(instrument.rx_polarity2))
    lines.append(f"{instrument.tx_height:.6e}")
    lines.append(f"{instrument.rx_height:.6e}")
    lines.append(f"{instrument.tx_height2:.6e}")
    lines.append(f"{instrument.rx_height2:.6e}")
    lines.append(f"{instrument.tx_rx_separation:.6e}")
    lines.append("1" if instrument.zero_coupled else "0")

    # Polygon parameters
    lines.append("POLYGON PARAMETERS")
    if polygon is not None:
        lines.append(str(polygon.n_vertices))
        for i in range(polygon.n_vertices):
            lines.append(f"{polygon.x_coords[i]:.6e}   {polygon.y_coords[i]:.6e}")
        lines.append(f"{polygon.rx_position[0]:.6e}")
        lines.append(f"{polygon.rx_position[1]:.6e}")
        lines.append("0.0")  # Z0RX
    else:
        lines.append("0")

    # Response parameters
    lines.append("RESPONSE PARAMETERS")
    if response_config is not None:
        lines.append(str(response_config.iresptype))
        lines.append(str(response_config.ideriv))
        lines.append("1" if waveform is not None else "0")  # IWCONV
        lines.append("1" if response_config.model_repetition else "0")
        if response_config.model_repetition:
            lines.append(f"{response_config.repetition_frequency:.6e}")
        lines.append(str(response_config.nfilt))
        if response_config.nfilt > 0:
            for freq in response_config.filter_frequencies:
                lines.append(f"{freq:.6e}")
    else:
        lines.append("0")  # IRESPTYPE
        lines.append("0")  # IDERIV
        lines.append("0")  # IWCONV
        lines.append("0")  # IREP
        lines.append("0")  # NFILT

    # Waveform parameters
    lines.append("WAVEFORM PARAMETERS")
    if waveform is not None:
        lines.append(str(waveform.nwave))
        for i in range(waveform.nwave):
            lines.append(f"{waveform.times[i]:.6e}   {waveform.amplitudes[i]:.6e}")
    else:
        lines.append("0")

    # Write to file
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


def model_to_dict(model: EarthModel) -> Dict[str, Any]:
    """
    Export earth model to dictionary

    Parameters
    ----------
    model : EarthModel
        Model to export

    Returns
    -------
    dict
        Model parameters as dictionary
    """
    return {
        "resistivities": model.resistivities.tolist(),
        "depths": model.depths.tolist(),
        "imlm": model.imlm,
        "nlay": model.nlay,
    }


def model_from_dict(data: Dict[str, Any]) -> EarthModel:
    """
    Import earth model from dictionary

    Parameters
    ----------
    data : dict
        Dictionary with model parameters

    Returns
    -------
    EarthModel
        Constructed model
    """
    return EarthModel(
        resistivities=np.array(data["resistivities"]),
        depths=np.array(data["depths"]),
        imlm=data.get("imlm", 0),
    )
