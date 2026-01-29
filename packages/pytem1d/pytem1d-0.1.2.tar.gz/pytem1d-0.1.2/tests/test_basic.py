"""
Basic tests for pytem1d

These tests verify that the package can be imported and basic functionality works.
"""

import pytest
import numpy as np
from pytem1d import (
    run_tem1d,
    TEM1DModel,
    EarthModel,
    Instrument,
    TEM1DResult,
)


def test_import():
    """Test that package can be imported"""
    import pytem1d

    assert hasattr(pytem1d, "__version__")
    assert hasattr(pytem1d, "run_tem1d")
    assert hasattr(pytem1d, "TEM1DModel")


def test_simple_functional_api():
    """Test simple 2-layer model with functional API"""
    result = run_tem1d(
        resistivities=[100, 10],
        depths=[0, 50],
        tx_area=314.16,
    )

    # Check result structure
    assert isinstance(result, TEM1DResult)
    assert len(result.times) > 0
    assert len(result.responses) == len(result.times)
    assert result.derivatives is None  # No derivatives by default

    # Check values are reasonable
    assert np.all(np.isfinite(result.times))
    assert np.all(np.isfinite(result.responses))
    assert np.all(result.times > 0)


def test_class_based_api():
    """Test class-based API"""
    tem = TEM1DModel()
    tem.set_earth_model([100, 10], [0, 50])
    tem.set_instrument(tx_area=314.16)

    result = tem.run()

    assert isinstance(result, TEM1DResult)
    assert len(result.times) > 0
    assert len(result.responses) == len(result.times)


def test_with_derivatives():
    """Test derivative calculation"""
    result = run_tem1d(
        resistivities=[100, 10, 50],
        depths=[0, 30, 100],
        calculate_derivatives=True,
    )

    assert result.derivatives is not None
    assert result.derivatives.shape[0] == len(result.times)
    # Should have derivatives for: 3 conductivities + 2 thicknesses + 1 tx_height = 6
    assert result.derivatives.shape[1] > 0


def test_earth_model():
    """Test EarthModel dataclass"""
    model = EarthModel(
        resistivities=[100, 10],
        depths=[0, 50],
    )

    assert model.nlay == 2
    assert np.allclose(model.resistivities, [100, 10])
    assert np.allclose(model.depths, [0, 50])
    assert np.allclose(model.conductivities, [0.01, 0.1])


def test_instrument():
    """Test Instrument dataclass"""
    instrument = Instrument(
        tx_area=314.16,
        tx_rx_separation=40.0,
        tx_height=1.0,
        rx_height=1.0,
    )

    assert instrument.tx_area == 314.16
    assert instrument.tx_rx_separation == 40.0


def test_invalid_model():
    """Test that invalid models raise errors"""
    with pytest.raises(ValueError):
        # First depth must be 0
        run_tem1d([100, 10], [10, 50])

    with pytest.raises(ValueError):
        # Resistivities must be positive
        run_tem1d([-100, 10], [0, 50])


def test_method_chaining():
    """Test that class methods can be chained"""
    tem = TEM1DModel()
    result = (
        tem.set_earth_model([100, 10], [0, 50])
        .set_instrument(tx_area=314.16)
        .enable_derivatives(False)
        .run()
    )

    assert isinstance(result, TEM1DResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
