# downsampler

A Python package for time series DataFrame downsampling with LTTB, multiple aggregation methods, gap handling, and fidelity testing.

## Features

- **Multiple downsampling methods**: LTTB (visual fidelity), mean, median, min, max
- **Gap-aware processing**: Automatically detects and handles gaps in time series
- **Edge handling**: Flag, discard, or keep edge points
- **Multi-aggregate output**: Generate min/mean/max columns in a single call
- **Deferred fetching**: Lazy data loading with automatic edge buffering
- **Fidelity testing**: Compare methods and measure visual accuracy

## Installation

```bash
pip install downsampler
```

Or with visualization support:

```bash
pip install downsampler[viz]
```

## Quick Start

### Basic Downsampling

```python
import pandas as pd
from downsampler import downsample

# Create sample data
df = pd.DataFrame(
    {'temperature': range(1000)},
    index=pd.date_range('2024-01-01', periods=1000, freq='1s')
)

# Downsample to 1-minute cadence (default: mean)
result = downsample(df, target_cadence='PT1M')
```

### Using Different Methods

```python
from downsampler import downsample, DownsampleConfig, AggregationMethod

# Mean (default)
result = downsample(df, '10min')

# Maximum
result = downsample(df, '10min', method='max')

# LTTB for visual fidelity
config = DownsampleConfig(
    method=AggregationMethod.LTTB,
    lttb_target_column='temperature'
)
result = downsample(df, '10min', config=config)
```

### Multi-Aggregate Downsampling

Create min/mean/max columns for visualization with error bands:

```python
from downsampler import downsample_multi_aggregate

result = downsample_multi_aggregate(
    df,
    target_cadence='1min',
    variables=['temperature', 'pressure'],
    aggregations=['min', 'mean', 'max']
)
# Result has columns: temperature_min, temperature_mean, temperature_max, etc.
```

### Handling Gaps

```python
from downsampler import DownsampleConfig, GapHandling

config = DownsampleConfig(
    gap_handling=GapHandling.SEGMENT,  # Process segments independently
    gap_threshold='5min'  # Gaps > 5 min trigger segmentation
)
result = downsample(df, '1min', config=config)
```

### Deferred Data Fetching

For data that needs to be fetched from an external source:

```python
from downsampler.deferred import deferred_downsample

def fetch_from_api(start, end):
    # Your data fetching logic here
    return pd.DataFrame(...)

result = deferred_downsample(
    fetcher=fetch_from_api,
    output_start=pd.Timestamp('2024-01-01'),
    output_end=pd.Timestamp('2024-01-02'),
    target_cadence='1H'
)
```

### Fidelity Comparison

Compare different methods to find the best one for your data:

```python
from downsampler.fidelity import FidelityComparison

comp = FidelityComparison(original_df, 'signal')
results = comp.compare_methods('10s')

for r in results:
    print(f"{r.method.value}: RMSE={r.metrics.rmse:.4f}")

# Get recommendation
config = comp.recommend_settings('10s', priority='visual')
```

## Configuration Options

### DownsampleConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | AggregationMethod | MEAN | Downsampling method |
| `lttb_target_column` | str | None | Column to optimize for LTTB |
| `include_columns` | list[str] | [] | Columns to include (empty = all) |
| `exclude_columns` | list[str] | [] | Columns to exclude |
| `gap_handling` | GapHandling | SEGMENT | How to handle gaps |
| `gap_threshold` | str/Timedelta | "auto" | Min duration for gaps |
| `edge_handling` | EdgeHandling | FLAG | How to handle edges |
| `edge_window` | int | 2 | Points at each edge |
| `min_points_per_segment` | int | 3 | Min points for processing |

### Aggregation Methods

- `MEAN`: Arithmetic mean (best for general use)
- `MEDIAN`: Median (robust to outliers)
- `MIN`: Minimum value (preserves lows)
- `MAX`: Maximum value (preserves highs)
- `LTTB`: Largest Triangle Three Buckets (best visual fidelity)

### Gap Handling

- `SEGMENT`: Split at gaps, process independently (recommended)
- `INTERPOLATE`: Fill gaps before processing
- `IGNORE`: Treat as continuous data

### Edge Handling

- `KEEP`: Keep edge points as-is
- `FLAG`: Add `_is_edge` column
- `DISCARD`: Remove edge points

## Examples

See the `examples/` directory for complete examples:

- `basic_downsampling.py`: Core downsampling features
- `multi_aggregate.py`: Creating min/mean/max columns
- `deferred_fetch.py`: Lazy data loading
- `fidelity_comparison.marimo.py`: Interactive comparison notebook

## API Reference

### Core Functions

```python
downsample(df, target_cadence, config=None, **kwargs) -> DataFrame
downsample_multi_aggregate(df, target_cadence, variables, aggregations, ...) -> DataFrame
```

### Gap Functions

```python
find_gap_indices(df, timedelta_max_gap) -> Series
groupby_gaps(df, timedelta_max_gap) -> DataFrameGroupBy
split_at_gaps(df, timedelta_max_gap) -> list[DataFrame]
mark_gaps_in_dataframe(df, nominal_timedelta, ...) -> DataFrame
```

### Deferred Functions

```python
deferred_downsample(fetcher, output_start, output_end, target_cadence, ...) -> DataFrame
batch_deferred_downsample(fetcher, ..., batch_size) -> DataFrame
LazyDownsampler(fetcher, cache_buffer) -> LazyDownsampler
```

### Fidelity Functions

```python
compute_metrics(original, downsampled, column) -> FidelityMetrics
FidelityComparison(original_df, column) -> FidelityComparison
plot_comparison(original, downsampled, column, backend) -> Figure
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
