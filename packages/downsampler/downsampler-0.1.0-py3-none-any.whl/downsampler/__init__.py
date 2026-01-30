"""downsampler - Timeseries DataFrame downsampling with LTTB, aggregation methods, and fidelity testing.

This package provides tools for downsampling time series data in pandas DataFrames,
with support for:
- LTTB (Largest Triangle Three Buckets) algorithm for visual fidelity
- Multiple aggregation methods (mean, median, min, max)
- Gap-aware processing
- Edge handling strategies
- Deferred/lazy data fetching
- Fidelity testing and comparison

Example:
    >>> import pandas as pd
    >>> from downsampler import downsample, DownsampleConfig, AggregationMethod
    >>>
    >>> # Create sample data
    >>> df = pd.DataFrame(
    ...     {'value': [1, 2, 3, 4, 5]},
    ...     index=pd.date_range('2024-01-01', periods=5, freq='1min')
    ... )
    >>>
    >>> # Downsample using mean
    >>> result = downsample(df, target_cadence='5min')
    >>>
    >>> # Downsample using LTTB
    >>> config = DownsampleConfig(
    ...     method=AggregationMethod.LTTB,
    ...     lttb_target_column='value'
    ... )
    >>> result = downsample(df, target_cadence='5min', config=config)
"""

from downsampler.config import (
    AggregationMethod,
    EdgeHandling,
    GapHandling,
    DownsampleConfig,
)
from downsampler.core import downsample, downsample_multi_aggregate
from downsampler.gaps import (
    find_gap_indices,
    groupby_gaps,
    wrap_in_nans,
    mark_gaps_in_dataframe,
)
from downsampler.lttb import downsample_lttb
from downsampler.aggregators import (
    downsample_mean,
    downsample_median,
    downsample_min,
    downsample_max,
)
from downsampler.deferred import deferred_downsample

__version__ = "0.1.0"

__all__ = [
    # Config
    "AggregationMethod",
    "EdgeHandling",
    "GapHandling",
    "DownsampleConfig",
    # Core
    "downsample",
    "downsample_multi_aggregate",
    # Gaps
    "find_gap_indices",
    "groupby_gaps",
    "wrap_in_nans",
    "mark_gaps_in_dataframe",
    # LTTB
    "downsample_lttb",
    # Aggregators
    "downsample_mean",
    "downsample_median",
    "downsample_min",
    "downsample_max",
    # Deferred
    "deferred_downsample",
]
