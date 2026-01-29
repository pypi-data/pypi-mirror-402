# Installation Guide for pytem1d

## Quick Install

### From PyPI (when available)

```bash
pip install pytem1d
```

On Linux/macOS, this will automatically compile the Fortran library during installation (requires `gfortran` and `make`).

On Windows, pre-compiled binaries are included.

### From Source

```bash
cd python
pip install -e .  # Automatically builds library and installs
```

Or manually:

```bash
cd python
make              # Build Fortran library manually
pip install -e .  # Install Python package
```

## Detailed Installation Steps

### Prerequisites

1. **Python 3.8 or later**
   ```bash
   python --version  # Should be >= 3.8
   ```

2. **Fortran compiler** (gfortran recommended)
   ```bash
   # Linux
   sudo apt-get install gfortran

   # macOS
   brew install gcc

   # Windows (MinGW-w64)
   # Download from: https://www.mingw-w64.org/
   ```

3. **Make** (usually pre-installed on Linux/macOS)

### Step 1: Build the Fortran Library

The Python package requires a compiled Fortran shared library.

```bash
cd python
make
```

This will create:
- Linux: `src/pytem1d/lib/libtem1d.so`
- macOS: `src/pytem1d/lib/libtem1d.dylib`
- Windows: `src/pytem1d/lib/libtem1d.dll`

**Troubleshooting**:
- If `make` fails, ensure gfortran is installed
- Check compiler version: `gfortran --version`
- Clean and rebuild: `make clean && make`

### Step 2: Install Python Dependencies

#### Option A: Using pip with requirements.txt (Recommended)

```bash
pip install -r requirements.txt
```

This installs:
- numpy >= 1.20.0
- matplotlib >= 3.3.0

#### Option B: Using pyproject.toml

```bash
pip install -e .
```

This installs the package in "editable" mode, allowing you to modify the source code without reinstalling.

### Step 3: Verify Installation

```bash
python -c "import pytem1d; print(pytem1d.__version__)"
python -c "from pytem1d import run_tem1d; print('✓ Import successful')"
```

### Step 4: Run Examples

```bash
cd examples
python basic_usage.py
```

If this runs successfully and creates `basic_tem_response.png`, your installation is complete!

## Development Installation

For contributing to pytem1d development:

```bash
# Build library
make

# Install with development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Verify dev tools
black --version
pytest --version
mypy --version
```

### Development Dependencies

- **pytest**: Unit testing framework
- **pytest-cov**: Code coverage reporting
- **black**: Code formatter
- **ruff**: Fast Python linter
- **mypy**: Static type checker
- **psutil**: Performance monitoring (optional)

## Installation Methods Comparison

| Method | Use Case | Command |
|--------|----------|---------|
| Requirements.txt | Simple installation | `pip install -r requirements.txt` |
| Editable install | Development | `pip install -e .` |
| With dev tools | Contributing | `pip install -r requirements-dev.txt && pip install -e .` |
| Specific version | Production | `pip install pytem1d==0.1.0` (when on PyPI) |

## Virtual Environment (Recommended)

Always use a virtual environment to avoid conflicts:

### Using venv (Python built-in)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install
pip install -r requirements.txt
pip install -e .

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create environment
conda create -n tem1d python=3.10

# Activate it
conda activate tem1d

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Deactivate when done
conda deactivate
```

## Platform-Specific Notes

### Linux

Usually straightforward. Just ensure gfortran is installed:

```bash
sudo apt-get install gfortran make
```

### macOS

Use Homebrew for dependencies:

```bash
brew install gcc make
```

Note: macOS may have both `gcc` and `gfortran` commands. The Makefile uses `gfortran`.

### Windows (WSL Recommended)

**Option 1: Windows Subsystem for Linux (Recommended)**

```bash
# Install WSL2 with Ubuntu
wsl --install

# Inside WSL
sudo apt-get update
sudo apt-get install gfortran make python3-pip
cd /mnt/c/path/to/tem1d/python
make
pip install -e .
```

**Option 2: Native Windows with MinGW**

1. Install MinGW-w64
2. Add to PATH: `C:\mingw64\bin`
3. Use `mingw32-make` instead of `make`
4. Proceed with standard installation

## Troubleshooting

### Library Not Found Error

```
ImportError: cannot load libtem1d.so
```

**Solution**: Ensure you ran `make` in the `python/` directory:

```bash
cd python
make clean
make
ls src/pytem1d/lib/  # Should show libtem1d.so (or .dylib, .dll)
```

### Fortran Compiler Issues

```
gfortran: command not found
```

**Solution**: Install gfortran (see Prerequisites above)

### Legacy Fortran Code Errors

```
Error: Type mismatch
```

**Solution**: The Makefile already includes `-std=legacy` flag. If you modified it, restore:

```makefile
FFLAGS = -O2 -std=legacy -fbacktrace -w
```

### Import Errors

```
ModuleNotFoundError: No module named 'pytem1d'
```

**Solution**: Install in editable mode:

```bash
cd python
pip install -e .
```

### Performance Issues

If parallel processing is slow:

1. Check CPU count: `python -c "from multiprocessing import cpu_count; print(cpu_count())"`
2. Reduce workers if >64: `n_workers=64` in parallel calls
3. See `PARALLEL_PROCESSING.md` for optimization tips

## Verifying Installation

Run the test suite (if available):

```bash
cd python
pytest tests/
```

Or run all examples:

```bash
cd examples
python basic_usage.py
python class_api.py
python batch_random_models.py
```

## Upgrading

To upgrade to the latest version:

```bash
cd python

# Rebuild Fortran library
make clean
make

# Reinstall Python package
pip install -e . --force-reinstall
```

## Uninstalling

```bash
# Uninstall Python package
pip uninstall pytem1d

# Remove build artifacts
cd python
make clean
```

## Getting Help

- **Documentation**: `README.md`, `examples/README.md`
- **Parallel processing**: `examples/PARALLEL_PROCESSING.md`
- **Benchmarks**: `examples/BENCHMARK_OVERVIEW.md`
- **Issues**: Report at https://github.com/tem1d/tem1d/issues (if applicable)

## Next Steps

After successful installation:

1. **Quick start**: Run `python examples/basic_usage.py`
2. **Learn the API**: See `examples/README.md`
3. **Try parallel processing**: Run `python examples/batch_random_models_parallel.py`
4. **Benchmark your system**: Run `python examples/benchmark_speedup_cpu.py`
