"""Core downsampling functions."""

import pandas as pd

from downsampler.config import DownsampleConfig, AggregationMethod
from downsampler.utils import parse_cadence
from downsampler.lttb import downsample_lttb_with_config
from downsampler.aggregators import downsample_with_config as aggregate_with_config
from downsampler.aggregators import downsample_multi_aggregate as _downsample_multi_aggregate


def downsample(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    config: DownsampleConfig | None = None,
    **kwargs
) -> pd.DataFrame:
    """Downsample a DataFrame to a lower cadence.

    This is the main entry point for downsampling operations. It supports
    multiple methods including LTTB and various aggregation methods.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string (e.g., "PT1H")
            or pandas Timedelta.
        config: Downsampling configuration. If None, uses default config
            with mean aggregation.
        **kwargs: Additional keyword arguments that override config settings.
            Supported kwargs:
            - method: AggregationMethod or string ('mean', 'lttb', etc.)
            - lttb_target_column: Column to optimize for LTTB
            - include_columns: Columns to include
            - exclude_columns: Columns to exclude
            - gap_threshold: Gap threshold
            - edge_handling: Edge handling strategy
            - edge_window: Edge window size

    Returns:
        Downsampled DataFrame.

    Examples:
        Basic mean downsampling:
        >>> df = pd.DataFrame(
        ...     {'value': range(100)},
        ...     index=pd.date_range('2024-01-01', periods=100, freq='1min')
        ... )
        >>> result = downsample(df, '10min')
        >>> len(result)
        10

        LTTB downsampling:
        >>> from downsampler import AggregationMethod, DownsampleConfig
        >>> config = DownsampleConfig(
        ...     method=AggregationMethod.LTTB,
        ...     lttb_target_column='value'
        ... )
        >>> result = downsample(df, '10min', config=config)

        Using kwargs:
        >>> result = downsample(df, '10min', method='max')
    """
    # Create config if not provided
    if config is None:
        config = DownsampleConfig()

    # Apply kwargs overrides
    if kwargs:
        config = _apply_kwargs_to_config(config, kwargs)

    target_cadence = parse_cadence(target_cadence)

    # Route to appropriate implementation
    if config.method == AggregationMethod.LTTB:
        return downsample_lttb_with_config(df, target_cadence, config)
    else:
        return aggregate_with_config(df, target_cadence, config)


def downsample_multi_aggregate(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    variables: list[str],
    aggregations: list[str] = ["min", "mean", "max"],
    config: DownsampleConfig | None = None,
    **kwargs
) -> pd.DataFrame:
    """Create columns like 'input_min', 'input_mean', 'input_max'.

    This function creates multiple aggregated columns from each input
    variable, useful for showing data ranges in visualizations.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        variables: List of column names to aggregate.
        aggregations: List of aggregation methods to apply.
            Default: ["min", "mean", "max"]
        config: Downsampling configuration (used for min_completeness if
            specified in a future version).
        **kwargs: Additional keyword arguments:
            - min_completeness: Minimum fraction of expected points (0.0-1.0)
            - source_cadence: Original cadence for completeness calculation

    Returns:
        DataFrame with aggregated columns named {variable}_{aggregation}.

    Example:
        >>> import numpy as np
        >>> df = pd.DataFrame(
        ...     {'density': np.random.randn(1000), 'velocity': np.random.randn(1000)},
        ...     index=pd.date_range('2024-01-01', periods=1000, freq='1s')
        ... )
        >>> result = downsample_multi_aggregate(
        ...     df, '1min', ['density', 'velocity']
        ... )
        >>> 'density_min' in result.columns
        True
        >>> 'density_mean' in result.columns
        True
        >>> 'density_max' in result.columns
        True
    """
    min_completeness = kwargs.get('min_completeness', 0.9)
    source_cadence = kwargs.get('source_cadence', None)

    return _downsample_multi_aggregate(
        df=df,
        target_cadence=target_cadence,
        variables=variables,
        aggregations=aggregations,
        min_completeness=min_completeness,
        source_cadence=source_cadence
    )


def _apply_kwargs_to_config(
    config: DownsampleConfig,
    kwargs: dict
) -> DownsampleConfig:
    """Apply keyword arguments to a config, creating a new config.

    Args:
        config: Base configuration.
        kwargs: Keyword arguments to apply.

    Returns:
        New configuration with kwargs applied.
    """
    from dataclasses import replace

    # Map string method names to enum values
    if 'method' in kwargs:
        method = kwargs['method']
        if isinstance(method, str):
            kwargs['method'] = AggregationMethod(method)

    # Filter to only valid config fields
    valid_fields = {
        'method', 'lttb_target_column', 'include_columns', 'exclude_columns',
        'gap_handling', 'gap_threshold', 'edge_handling', 'edge_window',
        'min_points_per_segment'
    }
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}

    return replace(config, **filtered_kwargs)
