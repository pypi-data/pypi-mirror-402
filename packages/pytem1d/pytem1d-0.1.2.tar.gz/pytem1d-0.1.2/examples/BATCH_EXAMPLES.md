# Batch Random Models - Usage Guide

The `batch_random_models.py` script is a comprehensive example demonstrating batch processing with configurable model complexity.

## Quick Start

```bash
# Run with defaults (1000 models, 3 layers)
python batch_random_models.py
```

## Configuration

Edit these parameters at the top of `batch_random_models.py`:

```python
N_MODELS = 1000      # Number of random models to generate
N_LAYERS = 3         # Number of layers (2, 3, 4, 5, etc.)
RANDOM_SEED = 42     # For reproducibility
```

## Use Cases by Layer Count

### 2-Layer Models (`N_LAYERS = 2`)
**Use for**: Basic resistivity contrasts, simple overburden-bedrock scenarios

```python
N_LAYERS = 2
```

**Output**:
- 2 resistivity distributions
- 1 thickness distribution
- Performance comparison

**Example models**:
- Soil over bedrock
- Sediment over basement
- Weathered zone over fresh rock

### 3-Layer Models (`N_LAYERS = 3`) [DEFAULT]
**Use for**: Standard TEM surveys, aquifer detection, layered stratigraphy

```python
N_LAYERS = 3
```

**Output**:
- 3 resistivity distributions
- 2 thickness distributions
- Performance comparison

**Example models**:
- Soil-aquifer-bedrock
- Top layer-conductive layer-basement
- Vadose zone-saturated zone-bedrock

### 4-Layer Models (`N_LAYERS = 4`)
**Use for**: Complex stratigraphy, multiple aquifer systems

```python
N_LAYERS = 4
```

**Output**:
- 4 resistivity distributions
- 3 thickness distributions
- Performance comparison

### 5+ Layer Models (`N_LAYERS = 5` or more)
**Use for**: Detailed stratigraphic interpretation, complex geology

```python
N_LAYERS = 5  # or 6, 7, 8, ...
```

**Note**: Runtime increases slightly with more layers, but throughput remains >100 models/s

## Runtime Examples

| Configuration | Runtime | Throughput |
|---------------|---------|------------|
| 100 models, 2 layers | ~0.6s | ~170 models/s |
| 100 models, 3 layers | ~0.6s | ~165 models/s |
| 100 models, 5 layers | ~0.7s | ~140 models/s |
| 1000 models, 2 layers | ~6s | ~170 models/s |
| 1000 models, 3 layers | ~7s | ~145 models/s |
| 1000 models, 5 layers | ~8s | ~125 models/s |
| 10000 models, 3 layers | ~70s | ~140 models/s |

## Output Files

### batch_random_models_ensemble.png
4-panel figure showing:
1. All responses with statistics overlay
2. Ensemble statistics (median, percentiles)
3. Response variability vs time
4. Distribution histograms at key times

### batch_random_models_parameters.png
Adaptive multi-panel figure showing:
- N_LAYERS resistivity histograms (one per layer)
- N_LAYERS-1 thickness histograms (one per interface)
- Performance comparison bar chart

**Layout adapts automatically**:
- 2 layers: 2x2 grid (2 resistivities, 1 thickness, 1 performance)
- 3 layers: 2x3 grid (3 resistivities, 2 thicknesses, 1 performance)
- 4 layers: 2x4 grid (4 resistivities, 3 thicknesses, 1 performance)
- 5+ layers: Adjusts rows/columns automatically

## Customization Examples

### Quick Test (10 models)
```python
N_MODELS = 10
N_LAYERS = 3
```
**Runtime**: <1 second

### Standard Run (1000 models)
```python
N_MODELS = 1000
N_LAYERS = 3
```
**Runtime**: ~7 seconds

### Large Study (10,000 models)
```python
N_MODELS = 10000
N_LAYERS = 3
```
**Runtime**: ~70 seconds

### Complex Stratigraphy (7 layers)
```python
N_MODELS = 1000
N_LAYERS = 7
```
**Runtime**: ~10 seconds

## Random Model Generation Details

### Resistivities
- Distribution: Log-uniform
- Range: 1 to 1000 Ω·m
- Independent for each layer

### Depths
- Top layer: Always at 0 m (surface)
- Interfaces: Automatically generated to be monotonically increasing
- Range: 10 to 200+ m depth
- Spacing adapts to number of layers:
  - 2 layers: Single interface anywhere 10-200m
  - 3 layers: Two interfaces spaced throughout depth range
  - 5 layers: Four interfaces evenly distributed with randomness

### Algorithm
```python
for layer i from 1 to N_LAYERS-1:
    depth_min = (i-1) * max_depth / (N_LAYERS-1) + 10
    depth_max = i * max_depth / (N_LAYERS-1) + 20
    depths[i] = random_uniform(depth_min, depth_max)
depths = sort(depths)  # Ensure strictly increasing
```

This ensures:
- Valid models (depths always increase)
- Reasonable layer spacing
- Natural variability

## Validation

The script performs comprehensive validation:

1. **Correctness**: Verifies functional and class APIs produce identical results
2. **Numerical precision**: Checks maximum difference < 1e-10
3. **Performance**: Compares timing between API approaches
4. **Statistics**: Computes ensemble statistics for all parameters

## Tips

1. **Start small**: Test with `N_MODELS = 10` first
2. **Increase gradually**: Move to 100, then 1000
3. **Reproducibility**: Keep `RANDOM_SEED = 42` for consistent results
4. **Randomize**: Set `RANDOM_SEED = None` for different models each run
5. **Save results**: Figures are automatically saved as PNG files
6. **Modify resistivity range**: Edit `rho_min` and `rho_max` in the script
7. **Adjust depth range**: Edit `max_depth = 200.0` in the script

## Integration

Use this script as a template for:
- Uncertainty quantification
- Monte Carlo inversion studies
- Synthetic data generation
- Algorithm benchmarking
- Performance testing

## Examples in Research

### Uncertainty Analysis
```python
N_MODELS = 5000
N_LAYERS = 3
# Analyze response variability for parameter uncertainty
```

### Inversion Testing
```python
N_MODELS = 1000
N_LAYERS = 4
# Generate synthetic data for inversion algorithm validation
```

### Computational Benchmarking
```python
N_MODELS = 10000
N_LAYERS = 3
# Test computational performance at scale
```

## Troubleshooting

**Issue**: Script takes too long
- **Solution**: Reduce `N_MODELS` (try 100 or 10)

**Issue**: Want different resistivity range
- **Solution**: Edit `rho_min` and `rho_max` in script (line ~37)

**Issue**: Need shallower or deeper models
- **Solution**: Edit `max_depth` variable (line ~49)

**Issue**: Plots are crowded with many layers
- **Solution**: Script automatically adjusts layout, or modify figure size

**Issue**: Want to save models to file
- **Solution**: Add save code after model generation:
```python
np.savez('models.npz', resistivities=resistivities_all, depths=depths_all)
```
