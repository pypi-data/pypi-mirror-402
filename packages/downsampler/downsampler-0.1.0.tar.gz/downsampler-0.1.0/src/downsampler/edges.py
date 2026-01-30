"""Edge handling strategies for downsampled time series data."""

import pandas as pd
import numpy as np
from typing import Tuple

from downsampler.config import EdgeHandling


def identify_edge_points(
    df: pd.DataFrame,
    edge_window: int = 2
) -> pd.Series:
    """Identify edge points in a DataFrame.

    Edge points are the first and last few points in a DataFrame that may
    have reduced accuracy in downsampling due to boundary effects.

    Args:
        df: DataFrame with DatetimeIndex.
        edge_window: Number of points at each edge to mark as edge points.

    Returns:
        Boolean Series where True indicates an edge point.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': range(10)},
        ...     index=pd.date_range('2024-01-01', periods=10, freq='1min')
        ... )
        >>> edges = identify_edge_points(df, edge_window=2)
        >>> edges.sum()
        4
    """
    n = len(df)
    is_edge = pd.Series(False, index=df.index)

    if n <= 2 * edge_window:
        # All points are edge points
        is_edge[:] = True
    else:
        is_edge.iloc[:edge_window] = True
        is_edge.iloc[-edge_window:] = True

    return is_edge


def apply_edge_handling(
    df: pd.DataFrame,
    handling: EdgeHandling,
    edge_window: int = 2
) -> pd.DataFrame:
    """Apply edge handling strategy to a DataFrame.

    Args:
        df: DataFrame with DatetimeIndex (typically after downsampling).
        handling: Edge handling strategy to apply.
        edge_window: Number of points at each edge to consider as edge points.

    Returns:
        DataFrame with edge handling applied:
        - KEEP: Returns the DataFrame unchanged.
        - FLAG: Adds '_is_edge' column with boolean values.
        - DISCARD: Returns DataFrame with edge points removed.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': range(10)},
        ...     index=pd.date_range('2024-01-01', periods=10, freq='1min')
        ... )
        >>> flagged = apply_edge_handling(df, EdgeHandling.FLAG, edge_window=2)
        >>> '_is_edge' in flagged.columns
        True
    """
    if handling == EdgeHandling.KEEP:
        return df

    is_edge = identify_edge_points(df, edge_window)

    if handling == EdgeHandling.FLAG:
        df_result = df.copy()
        df_result['_is_edge'] = is_edge
        return df_result

    elif handling == EdgeHandling.DISCARD:
        return df[~is_edge].copy()

    return df


def compute_edge_buffer(
    target_cadence: pd.Timedelta,
    edge_window: int = 2,
    multiplier: float = 2.0
) -> pd.Timedelta:
    """Compute the time buffer needed at edges for stable downsampling.

    When fetching data for downsampling, extra data should be fetched at
    the edges to ensure that edge effects don't affect the desired output
    range.

    Args:
        target_cadence: Target cadence for downsampling.
        edge_window: Number of points at each edge to consider as edge points.
        multiplier: Safety multiplier for the buffer.

    Returns:
        Time buffer to add at each edge.

    Example:
        >>> buffer = compute_edge_buffer(pd.Timedelta('1H'), edge_window=2, multiplier=2.0)
        >>> buffer
        Timedelta('0 days 04:00:00')
    """
    return target_cadence * edge_window * multiplier


def trim_edges_by_time(
    df: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp
) -> pd.DataFrame:
    """Trim a DataFrame to a specific time range.

    Useful for removing edge data that was fetched for buffering purposes
    after downsampling is complete.

    Args:
        df: DataFrame with DatetimeIndex.
        start: Start of desired time range (inclusive).
        end: End of desired time range (exclusive).

    Returns:
        DataFrame trimmed to the specified time range.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': range(10)},
        ...     index=pd.date_range('2024-01-01', periods=10, freq='1H')
        ... )
        >>> start = pd.Timestamp('2024-01-01 02:00')
        >>> end = pd.Timestamp('2024-01-01 08:00')
        >>> trimmed = trim_edges_by_time(df, start, end)
        >>> len(trimmed)
        6
    """
    return df[(df.index >= start) & (df.index < end)].copy()


def expand_time_range(
    start: pd.Timestamp,
    end: pd.Timestamp,
    buffer: pd.Timedelta
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Expand a time range by a buffer on both ends.

    Useful for computing the fetch range needed for stable downsampling.

    Args:
        start: Original start timestamp.
        end: Original end timestamp.
        buffer: Time buffer to add at each end.

    Returns:
        Tuple of (expanded_start, expanded_end).

    Example:
        >>> start = pd.Timestamp('2024-01-01 12:00')
        >>> end = pd.Timestamp('2024-01-01 18:00')
        >>> expanded_start, expanded_end = expand_time_range(start, end, pd.Timedelta('1H'))
        >>> expanded_start
        Timestamp('2024-01-01 11:00:00')
        >>> expanded_end
        Timestamp('2024-01-01 19:00:00')
    """
    return start - buffer, end + buffer


def merge_edge_flags(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge DataFrames while preserving edge flags.

    When concatenating segments that were processed independently,
    the edge flags should be updated to reflect the combined data.

    Args:
        dfs: List of DataFrames, potentially with '_is_edge' columns.

    Returns:
        Concatenated DataFrame with merged edge information.
        Points that were internal edges (between segments) retain their
        edge flag from the original processing.
    """
    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs).sort_index()

    # If no edge flags present, just return
    if '_is_edge' not in result.columns:
        return result

    return result
