# pytem1d - Python Interface to TEM1D

Python wrapper for the TEM1D Fortran code that computes 1D transient electromagnetic (TEM) forward responses and derivatives for layered earth models.

## Features

- **Dual API**: Functional and class-based interfaces
- **Complete TEM1D functionality**: Step/impulse responses, IP effects, polygonal loops, waveform convolution
- **Derivatives**: Jacobian matrix calculation for inversion
- **Visualization**: Built-in plotting functions
- **I/O utilities**: Save/load results, export to various formats
- **Type-safe**: Data classes with validation
- **Parallel processing**: Multiprocessing support for millions of forward models (see `examples/parallel_utils.py`)

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/tem1d/tem1d.git
cd tem1d/python

# Build the Fortran shared library
make

# Install the Python package (editable mode for development)
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python >= 3.8
- NumPy >= 1.20
- Matplotlib >= 3.3
- gfortran (or compatible Fortran compiler)
- make

## Quick Start

### Functional API (Simple)

```python
import numpy as np
import matplotlib.pyplot as plt
from pytem1d import run_tem1d

# Simple 2-layer model: 100 Ω·m over 10 Ω·m halfspace
result = run_tem1d(
    resistivities=[100, 10],
    depths=[0, 50],  # Interface at 50m depth
    tx_area=314.16   # Circular loop, radius ~10m
)

# Plot response
plt.loglog(result.times * 1e3, np.abs(result.responses))
plt.xlabel('Time (ms)')
plt.ylabel('|dB/dt| (V/A·m²)')
plt.grid(True, alpha=0.3)
plt.show()
```

### Class-Based API (Advanced)

```python
from pytem1d import TEM1DModel

# Create model instance
tem = TEM1DModel()

# Configure layered earth
tem.set_earth_model(
    resistivities=[100, 10, 50],  # 3 layers
    depths=[0, 30, 100]            # Interfaces at 30m and 100m
)

# Configure instrument
tem.set_instrument(
    tx_area=314.16,
    tx_rx_separation=0.0  # Central loop
)

# Enable derivative calculation
tem.enable_derivatives(True)

# Run forward modeling
result = tem.run()

# Access results
print(f"Number of time gates: {len(result.times)}")
print(f"Derivative shape: {result.derivatives.shape}")
```

### With IP Effects

```python
from pytem1d import run_tem1d

result = run_tem1d(
    resistivities=[100, 10, 50],
    depths=[0, 30, 100],
    tx_area=314.16,
    # Cole-Cole IP parameters
    ip_params={
        'chargeabilities': [0.1, 0.3, 0.05],
        'time_constants': [0.01, 0.05, 0.001],
        'powers': [0.5, 0.4, 0.6]
    }
)
```

### Polygonal Loop

```python
import numpy as np
from pytem1d import run_tem1d

# Square loop 100m x 100m
vertices = np.array([
    [-50, -50],
    [50, -50],
    [50, 50],
    [-50, 50]
])

result = run_tem1d(
    resistivities=[100, 10],
    depths=[0, 50],
    polygon_vertices=vertices,
    rx_position=(0, 0)  # Receiver at center
)
```

## Visualization

```python
from pytem1d import run_tem1d, plot_response, plot_derivatives

# Run with derivatives
result = run_tem1d(
    resistivities=[100, 10, 50],
    depths=[0, 30, 100],
    calculate_derivatives=True
)

# Plot response
plot_response(result)

# Plot Jacobian (sensitivities)
plot_derivatives(result, param_labels=['σ₁', 'σ₂', 'σ₃', 'h₁', 'h₂'])
```

## API Reference

### Main Functions

- `run_tem1d()` - Functional interface for forward modeling
- `TEM1DModel` - Class-based interface with state management

### Data Classes

- `EarthModel` - Layered earth parameters
- `IPModel` - Induced polarization (Cole-Cole)
- `Instrument` - TX/RX configuration
- `PolygonLoop` - Arbitrary loop geometry
- `TEM1DResult` - Computation results

### Utilities

- `plot_response()` - Plot TEM response
- `plot_derivatives()` - Plot Jacobian matrix
- `plot_comparison()` - Compare multiple responses
- `save_result()` - Save results to file
- `load_result()` - Load results from file

## Examples

See the `examples/` directory for more usage examples:

- `basic_usage.py` - Simple functional API
- `class_api.py` - Advanced class-based API
- `plotting_demo.py` - Visualization examples
- `batch_random_models.py` - Batch processing 1000 random models (compares both APIs)
- `numerical_derivatives.py` - Workaround for computing derivatives using finite differences
- `parallel_utils.py` ⚡ **NEW** - Parallel execution utilities for large-scale processing
- `batch_random_models_parallel.py` ⚡ **NEW** - Parallel benchmarking (7,000+ models/s on 128-core system)

## Building from Source

The Python package requires a compiled Fortran shared library:

```bash
cd python
make          # Build shared library
make clean    # Clean build artifacts
```

The Makefile automatically detects your platform and builds the appropriate shared library (`.so` on Linux, `.dll` on Windows, `.dylib` on macOS).

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# With coverage
pytest --cov=pytem1d tests/
```

## Troubleshooting

### Library not found

If you get "Cannot load libtem1d.so" errors:
1. Ensure you ran `make` in the `python/` directory
2. Check that `python/src/pytem1d/lib/libtem1d.so` exists
3. Try reinstalling: `pip install -e .`

### Fortran compiler issues

If `make` fails:
- Linux: Install gfortran: `sudo apt-get install gfortran`
- macOS: Install via Homebrew: `brew install gcc`
- Windows: Install MinGW-w64

### Results don't match TEMTEST

Small numerical differences are expected due to floating-point precision. Differences > 1% may indicate an issue.

## License

See LICENSE file in the root directory.

## Citation

If you use this code in publications, please cite:
- See `TEM1D_UserManual_20251219.pdf` for proper citation

## Contributing

Contributions are welcome! Please see the main repository for guidelines.

## Links

- [TEM1D Manual](../TEM1D_UserManual_20251219.pdf)
- [Examples](./examples/)
- [Tests](./tests/)

## Known Issues

### Derivative Calculation

The Python interface supports derivative (Jacobian) calculation via the `calculate_derivatives=True` parameter. However, in the current version of the TEM1D Fortran code, derivatives may return all zeros. This is not a Python wrapper issue - the same behavior occurs with the original TEMTEST program when `IDERIV=1`.

To verify if derivatives are supported in your version:
```bash
cd examples/
# Check if example2 (with derivatives) produces non-zero values
./run_example.sh example2_3layer_with_derivatives.txt
grep -v "0.0000E+00" output_example2_3layer_with_derivatives/FORWRITE | wc -l
```

If you need derivatives for inversion, you may need to:
1. Check the TEM1D user manual for derivative support status
2. Implement numerical derivatives using finite differences
3. Contact the TEM1D developers for the derivative-enabled version

The Python interface is ready and will work correctly once the Fortran code produces non-zero derivatives.
