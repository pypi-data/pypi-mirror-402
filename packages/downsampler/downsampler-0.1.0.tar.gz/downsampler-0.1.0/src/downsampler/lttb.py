"""LTTB (Largest Triangle Three Buckets) downsampling with gap handling."""

import logging
import pandas as pd
import numpy as np
import lttb

from downsampler.config import DownsampleConfig, GapHandling, EdgeHandling
from downsampler.gaps import split_at_gaps
from downsampler.edges import apply_edge_handling
from downsampler.utils import parse_cadence, get_numeric_columns, compute_output_points


def downsample_lttb(
    df_in: pd.DataFrame,
    target_column: str,
    target_cadence: str | pd.Timedelta,
    include_columns: list[str] | None = None,
    gap_threshold: pd.Timedelta | None = None,
    min_points_per_segment: int = 3
) -> pd.DataFrame:
    """Perform LTTB downsampling on a pandas DataFrame.

    LTTB (Largest Triangle Three Buckets) is a downsampling algorithm that
    preserves visual characteristics of the data by selecting points that
    maximize the area of triangles formed with adjacent buckets.

    Args:
        df_in: Input DataFrame with DatetimeIndex.
        target_column: Column to optimize visual fidelity for.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        include_columns: Additional columns to include in output (interpolated
            to LTTB-selected time points). If None, includes all numeric columns.
        gap_threshold: Minimum duration to consider as a gap. If None, uses
            2x target_cadence.
        min_points_per_segment: Minimum points required per segment.

    Returns:
        DataFrame downsampled using LTTB algorithm.

    Example:
        >>> df = pd.DataFrame(
        ...     {'signal': np.sin(np.linspace(0, 10*np.pi, 1000))},
        ...     index=pd.date_range('2024-01-01', periods=1000, freq='1s')
        ... )
        >>> result = downsample_lttb(df, 'signal', 'PT10S')
        >>> len(result) < len(df)
        True
    """
    target_cadence = parse_cadence(target_cadence)

    if gap_threshold is None:
        gap_threshold = 2 * target_cadence

    # Split at gaps and process each segment
    segments = split_at_gaps(df_in, gap_threshold)

    resampled_segments = []
    for segment in segments:
        if len(segment) < min_points_per_segment:
            continue

        resampled = _lttb_single_segment(
            segment,
            target_column,
            target_cadence,
            include_columns
        )
        if resampled is not None and len(resampled) > 0:
            resampled_segments.append(resampled)

    if not resampled_segments:
        return pd.DataFrame(columns=df_in.columns)

    return pd.concat(resampled_segments, axis=0).sort_index()


def _lttb_single_segment(
    df: pd.DataFrame,
    target_column: str,
    target_cadence: pd.Timedelta,
    include_columns: list[str] | None = None
) -> pd.DataFrame | None:
    """Apply LTTB to a single contiguous segment.

    Args:
        df: Input DataFrame (no gaps).
        target_column: Column to optimize for.
        target_cadence: Target cadence.
        include_columns: Additional columns to include.

    Returns:
        Downsampled DataFrame or None if cannot process.
    """
    # Compute number of output points
    n_out = compute_output_points(df.index[0], df.index[-1], target_cadence)

    if n_out < 3:
        logging.warning("Cannot perform LTTB downsampling on less than 3 points")
        return None

    # Set up the data - convert time to numeric for LTTB algorithm
    df_work = df.copy()
    timeref = df.index[0]
    timeunit = '1min'
    df_work['time_num'] = (df_work.index - timeref) / pd.to_timedelta(timeunit)

    # Prepare data for LTTB (time_num, target_column)
    data = df_work[['time_num', target_column]].dropna().values

    if len(data) < 3:
        logging.warning("Insufficient non-NaN data points for LTTB")
        return None

    # Apply LTTB downsampling
    result = lttb.downsample(data, n_out)
    df_resampled = pd.DataFrame(
        result,
        columns=['time_num', target_column]
    )

    # Reconstruct the datetime index
    df_resampled.index = (
        timeref +
        pd.to_timedelta(df_resampled['time_num'], unit='min')
    )

    # Determine which columns to interpolate
    if include_columns is None:
        cols_to_interp = get_numeric_columns(df)
    else:
        cols_to_interp = include_columns

    # Interpolate other columns to LTTB-selected time points
    for col in df.columns:
        if col in ['time', 'time_num', target_column]:
            continue
        if include_columns is not None and col not in include_columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        df_resampled[col] = np.interp(
            x=df_resampled['time_num'].values,
            xp=df_work['time_num'].values,
            fp=df_work[col].values
        )

    # Clean up
    df_resampled = df_resampled.drop(['time_num'], axis=1)

    return df_resampled


def downsample_lttb_with_config(
    df: pd.DataFrame,
    target_cadence: str | pd.Timedelta,
    config: DownsampleConfig
) -> pd.DataFrame:
    """Apply LTTB downsampling with full configuration.

    Args:
        df: Input DataFrame with DatetimeIndex.
        target_cadence: Target cadence.
        config: Downsampling configuration.

    Returns:
        Downsampled DataFrame.

    Raises:
        ValueError: If lttb_target_column is not specified in config.
    """
    target_cadence = parse_cadence(target_cadence)

    if config.lttb_target_column is None:
        raise ValueError("lttb_target_column must be specified for LTTB method")

    # Determine gap threshold
    gap_threshold = config.get_gap_threshold(target_cadence)

    # Determine include columns
    include_columns = config.include_columns if config.include_columns else None

    # Apply LTTB
    result = downsample_lttb(
        df_in=df,
        target_column=config.lttb_target_column,
        target_cadence=target_cadence,
        include_columns=include_columns,
        gap_threshold=gap_threshold,
        min_points_per_segment=config.min_points_per_segment
    )

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
