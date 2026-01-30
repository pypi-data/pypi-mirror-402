"""Aggregation-based downsampling methods."""

import pandas as pd
import numpy as np

from downsampler.config import DownsampleConfig, GapHandling, EdgeHandling, AggregationMethod
from downsampler.gaps import split_at_gaps, mark_gaps_in_dataframe
from downsampler.edges import apply_edge_handling
from downsampler.utils import parse_cadence, get_numeric_columns


def _apply_aggregation(
    df: pd.DataFrame,
    target_cadence: pd.Timedelta,
    method: str,
    columns: list[str] | None = None
) -> pd.DataFrame:
    """Apply an aggregation method to downsample a DataFrame.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence for resampling.
        method: Aggregation method ('mean', 'median', 'min', 'max').
        columns: Columns to aggregate. If None, all numeric columns.

    Returns:
        Aggregated DataFrame.
    """
    if columns is None:
        columns = get_numeric_columns(df)

    resampler = df[columns].resample(target_cadence, origin='epoch')

    if method == 'mean':
        return resampler.mean()
    elif method == 'median':
        return resampler.median()
    elif method == 'min':
        return resampler.min()
    elif method == 'max':
        return resampler.max()
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def downsample_mean(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    mark_gaps: bool = True
) -> pd.DataFrame:
    """Downsample using mean aggregation.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        columns: Columns to include. If None, all numeric columns.
        gap_threshold: Minimum duration to consider as a gap.
        mark_gaps: Whether to insert NaN markers at gaps.

    Returns:
        Downsampled DataFrame.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': range(100)},
        ...     index=pd.date_range('2024-01-01', periods=100, freq='1min')
        ... )
        >>> result = downsample_mean(df, '10min')
        >>> len(result)
        10
    """
    return _downsample_with_aggregation(
        df, target_cadence, 'mean', columns, gap_threshold, mark_gaps
    )


def downsample_median(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    mark_gaps: bool = True
) -> pd.DataFrame:
    """Downsample using median aggregation.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        columns: Columns to include. If None, all numeric columns.
        gap_threshold: Minimum duration to consider as a gap.
        mark_gaps: Whether to insert NaN markers at gaps.

    Returns:
        Downsampled DataFrame.
    """
    return _downsample_with_aggregation(
        df, target_cadence, 'median', columns, gap_threshold, mark_gaps
    )


def downsample_min(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    mark_gaps: bool = True
) -> pd.DataFrame:
    """Downsample using minimum aggregation.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        columns: Columns to include. If None, all numeric columns.
        gap_threshold: Minimum duration to consider as a gap.
        mark_gaps: Whether to insert NaN markers at gaps.

    Returns:
        Downsampled DataFrame.
    """
    return _downsample_with_aggregation(
        df, target_cadence, 'min', columns, gap_threshold, mark_gaps
    )


def downsample_max(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    mark_gaps: bool = True
) -> pd.DataFrame:
    """Downsample using maximum aggregation.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        columns: Columns to include. If None, all numeric columns.
        gap_threshold: Minimum duration to consider as a gap.
        mark_gaps: Whether to insert NaN markers at gaps.

    Returns:
        Downsampled DataFrame.
    """
    return _downsample_with_aggregation(
        df, target_cadence, 'max', columns, gap_threshold, mark_gaps
    )


def _downsample_with_aggregation(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    method: str,
    columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    mark_gaps: bool = True
) -> pd.DataFrame:
    """Internal function for aggregation-based downsampling.

    Args:
        df: Input DataFrame.
        target_cadence: Target cadence.
        method: Aggregation method.
        columns: Columns to include.
        gap_threshold: Gap threshold.
        mark_gaps: Whether to mark gaps.

    Returns:
        Downsampled DataFrame.
    """
    target_cadence = parse_cadence(target_cadence)

    if gap_threshold is None:
        gap_threshold = 2 * target_cadence

    # Apply aggregation
    result = _apply_aggregation(df, target_cadence, method, columns)

    # Mark gaps if requested
    if mark_gaps:
        result = mark_gaps_in_dataframe(
            result,
            nominal_timedelta=target_cadence,
            nominal_start_time=df.index[0] if len(df) > 0 else None,
            nominal_end_time=df.index[-1] + target_cadence if len(df) > 0 else None
        )

    return result


def downsample_multi_aggregate(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    variables: list[str],
    aggregations: list[str] = ["min", "mean", "max"],
    min_completeness: float = 0.9,
    source_cadence: str | pd.Timedelta | None = None
) -> pd.DataFrame:
    """Create multiple aggregation columns for specified variables.

    Produces columns like 'density_min', 'density_mean', 'density_max'
    from a single 'density' column.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        variables: List of column names to aggregate.
        aggregations: List of aggregation methods to apply.
        min_completeness: Minimum fraction of expected points required
            for valid output (0.0 to 1.0).
        source_cadence: Original cadence of the data for completeness
            calculation. If None, estimated from data.

    Returns:
        DataFrame with aggregated columns named {variable}_{aggregation}.

    Example:
        >>> df = pd.DataFrame(
        ...     {'density': np.random.randn(1000), 'velocity': np.random.randn(1000)},
        ...     index=pd.date_range('2024-01-01', periods=1000, freq='1s')
        ... )
        >>> result = downsample_multi_aggregate(
        ...     df, '1min', ['density', 'velocity'], ['min', 'mean', 'max']
        ... )
        >>> list(result.columns)
        ['density_min', 'density_mean', 'density_max', 'velocity_min', 'velocity_mean', 'velocity_max', 'coverage']
    """
    target_cadence = parse_cadence(target_cadence)

    # Estimate source cadence if not provided
    if source_cadence is None:
        from downsampler.utils import estimate_cadence
        source_cadence = estimate_cadence(df)
    else:
        source_cadence = parse_cadence(source_cadence)

    # Compute statistics with count
    aggstats = [*aggregations, 'count']
    df_agg = df[variables].resample(
        target_cadence, label='left', origin='epoch'
    ).agg(aggstats)

    # Adjust index to middle of cadence (for proper time representation)
    df_agg.index = df_agg.index + 0.5 * target_cadence

    # Compute completeness/coverage
    maxcount = target_cadence / source_cadence
    coverage = df_agg[[(v, 'count') for v in variables]].apply(max, axis=1) / maxcount

    # Set data to NaN if statistics are based on limited observations
    for var in variables:
        for aggstat in aggregations:
            df_agg.loc[:, (var, aggstat)] = (
                df_agg.loc[:, (var, aggstat)].where(
                    df_agg.loc[:, (var, 'count')] > min_completeness * maxcount
                )
            )

    # Remove count columns
    for var in variables:
        df_agg.drop((var, "count"), axis=1, inplace=True)

    # Flatten multi-index columns to single index (e.g., "density_min")
    df_agg.columns = ["_".join(col_name) for col_name in df_agg.columns.to_flat_index()]

    # Add coverage column
    df_agg['coverage'] = coverage

    return df_agg


def downsample_with_config(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    config: DownsampleConfig
) -> pd.DataFrame:
    """Apply aggregation-based downsampling with full configuration.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence.
        config: Downsampling configuration.

    Returns:
        Downsampled DataFrame.
    """
    target_cadence = parse_cadence(target_cadence)
    gap_threshold = config.get_gap_threshold(target_cadence)

    # Determine columns to process
    columns = config.include_columns if config.include_columns else None

    # Map method to function
    method_map = {
        AggregationMethod.MEAN: 'mean',
        AggregationMethod.MEDIAN: 'median',
        AggregationMethod.MIN: 'min',
        AggregationMethod.MAX: 'max',
    }

    method_str = method_map.get(config.method)
    if method_str is None:
        raise ValueError(f"Method {config.method} is not an aggregation method")

    # Process based on gap handling
    if config.gap_handling == GapHandling.SEGMENT:
        segments = split_at_gaps(df, gap_threshold)
        results = []
        for segment in segments:
            if len(segment) < config.min_points_per_segment:
                continue
            result = _apply_aggregation(segment, target_cadence, method_str, columns)
            results.append(result)

        if not results:
            return pd.DataFrame(columns=df.columns if columns is None else columns)

        result = pd.concat(results).sort_index()
        result = mark_gaps_in_dataframe(result, nominal_timedelta=target_cadence)
    else:
        result = _apply_aggregation(df, target_cadence, method_str, columns)
        result = mark_gaps_in_dataframe(result, nominal_timedelta=target_cadence)

    # Apply edge handling
    if len(result) > 0:
        result = apply_edge_handling(
            result,
            config.edge_handling,
            config.edge_window
        )

    # Filter out excluded columns
    if config.exclude_columns:
        cols_to_drop = [c for c in config.exclude_columns if c in result.columns]
        result = result.drop(columns=cols_to_drop)

    return result
