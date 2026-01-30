"""Gap detection and handling for time series data."""

import pandas as pd
import numpy as np
from typing import Iterator


def find_gap_indices(
    df: pd.DataFrame,
    timedelta_max_gap: pd.Timedelta
) -> pd.Series:
    """Find gaps in a DataFrame and return their locations and durations.

    Identifies gaps in the DataFrame's DatetimeIndex that are equal to or
    longer than the specified threshold.

    Args:
        df: DataFrame with DatetimeIndex.
        timedelta_max_gap: Minimum duration to consider as a gap.

    Returns:
        Series where indices are the integer positions of gap starts in the
        DataFrame, and values are the gap durations as multiples of
        timedelta_max_gap.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3]},
        ...     index=pd.to_datetime(['2024-01-01 00:00', '2024-01-01 00:01', '2024-01-01 00:10'])
        ... )
        >>> gaps = find_gap_indices(df, pd.Timedelta('5min'))
        >>> len(gaps)  # One gap found
        1
    """
    deltas = pd.Series(df.index).diff()[1:]
    gaps = deltas[deltas >= timedelta_max_gap] / timedelta_max_gap
    return gaps


def groupby_gaps(
    df: pd.DataFrame,
    timedelta_max_gap: pd.Timedelta
) -> pd.api.typing.DataFrameGroupBy:
    """Split a DataFrame at gaps and return a groupby object.

    Finds gaps in the DataFrame and returns a groupby object where each
    group is a contiguous segment between gaps.

    Args:
        df: DataFrame with DatetimeIndex.
        timedelta_max_gap: Minimum duration to consider as a gap.

    Returns:
        DataFrameGroupBy object where each group is a contiguous segment.

    Note:
        This function modifies the input DataFrame by adding a 'gap_index'
        column. Use .copy() if you need to preserve the original.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3, 4, 5]},
        ...     index=pd.to_datetime([
        ...         '2024-01-01 00:00', '2024-01-01 00:01', '2024-01-01 00:02',
        ...         '2024-01-01 00:10', '2024-01-01 00:11'
        ...     ])
        ... )
        >>> groups = groupby_gaps(df.copy(), pd.Timedelta('5min'))
        >>> len(list(groups))  # Two segments
        2
    """
    deltas = df.index.diff()[1:]
    gap_indices = (deltas >= timedelta_max_gap).cumsum()
    df['gap_index'] = [0, *gap_indices]
    dfs_out = df.groupby('gap_index')
    return dfs_out


def split_at_gaps(
    df: pd.DataFrame,
    timedelta_max_gap: pd.Timedelta
) -> list[pd.DataFrame]:
    """Split a DataFrame at gaps into a list of DataFrames.

    Finds gaps in the DataFrame and returns a list of DataFrames,
    each representing a contiguous segment between gaps.

    Args:
        df: DataFrame with DatetimeIndex.
        timedelta_max_gap: Minimum duration to consider as a gap.

    Returns:
        List of DataFrames, one for each contiguous segment.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3, 4, 5]},
        ...     index=pd.to_datetime([
        ...         '2024-01-01 00:00', '2024-01-01 00:01', '2024-01-01 00:02',
        ...         '2024-01-01 00:10', '2024-01-01 00:11'
        ...     ])
        ... )
        >>> segments = split_at_gaps(df, pd.Timedelta('5min'))
        >>> len(segments)
        2
        >>> len(segments[0])
        3
        >>> len(segments[1])
        2
    """
    df_work = df.copy()
    groups = groupby_gaps(df_work, timedelta_max_gap)
    return [group.drop(columns=['gap_index']) for _, group in groups]


def iter_segments(
    df: pd.DataFrame,
    timedelta_max_gap: pd.Timedelta,
    min_points: int = 1
) -> Iterator[pd.DataFrame]:
    """Iterate over contiguous segments in a DataFrame.

    Yields DataFrames representing contiguous segments between gaps,
    optionally filtering out segments with too few points.

    Args:
        df: DataFrame with DatetimeIndex.
        timedelta_max_gap: Minimum duration to consider as a gap.
        min_points: Minimum number of points required in a segment.

    Yields:
        DataFrames for each contiguous segment with at least min_points.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3, 4, 5]},
        ...     index=pd.to_datetime([
        ...         '2024-01-01 00:00', '2024-01-01 00:01', '2024-01-01 00:02',
        ...         '2024-01-01 00:10', '2024-01-01 00:11'
        ...     ])
        ... )
        >>> for segment in iter_segments(df, pd.Timedelta('5min'), min_points=3):
        ...     print(len(segment))
        3
    """
    df_work = df.copy()
    groups = groupby_gaps(df_work, timedelta_max_gap)

    for _, group in groups:
        segment = group.drop(columns=['gap_index'])
        if len(segment) >= min_points:
            yield segment


def wrap_in_nans(
    df_in: pd.DataFrame,
    offset: str = 'PT0.1S',
    where: str = 'both'
) -> pd.DataFrame:
    """Add NaN boundary rows before and/or after a DataFrame.

    Returns a copy of the DataFrame with rows of NaN values added at the
    start and/or end. This is useful for creating visual breaks in plots.

    Args:
        df_in: Input DataFrame with DatetimeIndex.
        offset: Time offset for the NaN rows as ISO 8601 duration string.
        where: Where to add NaN rows: 'start', 'end', or 'both'.

    Returns:
        DataFrame with NaN boundary rows added.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3]},
        ...     index=pd.date_range('2024-01-01', periods=3, freq='1min')
        ... )
        >>> wrapped = wrap_in_nans(df, offset='PT1S')
        >>> len(wrapped)
        5
        >>> np.isnan(wrapped.iloc[0]['value'])
        True
    """
    df_out = df_in.copy()
    data_nans = {col: np.nan for col in df_out.columns}
    offset_timedelta = pd.to_timedelta(offset)

    # Add gap before start
    if where in ('start', 'both'):
        df_new_record_before = pd.DataFrame(
            data=data_nans,
            index=[df_out.index[0] - offset_timedelta]
        )
        df_out = pd.concat([df_new_record_before, df_out])

    # Add gap after end
    if where in ('end', 'both'):
        df_new_record_after = pd.DataFrame(
            data=data_nans,
            index=[df_out.index[-1] + offset_timedelta]
        )
        df_out = pd.concat([df_out, df_new_record_after])

    return df_out


def mark_gaps_in_dataframe(
    df: pd.DataFrame,
    nominal_timedelta: pd.Timedelta = pd.to_timedelta(1, 'min'),
    nominal_start_time: pd.Timestamp | None = None,
    nominal_end_time: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Insert NaN records at gaps to create visual breaks in plots.

    Looks for gaps in the DataFrame and inserts NaN records to ensure
    that plotting libraries will show breaks at gap locations.

    Args:
        df: DataFrame with DatetimeIndex.
        nominal_timedelta: Expected cadence of the time series.
        nominal_start_time: If provided, add NaN before first record if
            it's after this time.
        nominal_end_time: If provided, add NaN after last record if
            it's before this time.

    Returns:
        DataFrame with NaN records inserted at gap locations.

    Example:
        >>> df = pd.DataFrame(
        ...     {'value': [1, 2, 3]},
        ...     index=pd.to_datetime([
        ...         '2024-01-01 00:00', '2024-01-01 00:01', '2024-01-01 00:10'
        ...     ])
        ... )
        >>> marked = mark_gaps_in_dataframe(df, pd.Timedelta('1min'))
        >>> len(marked) > len(df)
        True
    """
    deltas = pd.Series(df.index).diff()[1:]
    gaps = deltas[deltas > nominal_timedelta] / nominal_timedelta

    df_gapfilled = df.copy()
    data_nans = {col: np.nan for col in df.columns}

    for i, gap in gaps.items():
        # Add a np.nan record after the start of each gap,
        # to force breaks in plotted lines
        time_gap_start = df.index[i - 1] + nominal_timedelta
        df_new_record = pd.DataFrame(data=data_nans, index=[time_gap_start])
        df_gapfilled = pd.concat([df_gapfilled, df_new_record]).sort_index()

        # For gaps longer than 1 record, also add a np.nan record before the
        # end of the gap
        if gap > 2:
            time_gap_end = df.index[i] - nominal_timedelta
            df_new_record = pd.DataFrame(data=data_nans, index=[time_gap_end])
            df_gapfilled = pd.concat([df_gapfilled, df_new_record]).sort_index()

    # Add gap before start
    if nominal_start_time is not None:
        if df.index[0] > nominal_start_time:
            df_new_record_before = pd.DataFrame(
                data=data_nans,
                index=[df.index[0] - nominal_timedelta]
            )
            df_gapfilled = pd.concat([df_new_record_before, df_gapfilled])

    # Add gap after end
    if nominal_end_time is not None:
        if df.index[-1] < nominal_end_time:
            df_new_record_after = pd.DataFrame(
                data=data_nans,
                index=[df.index[-1] + nominal_timedelta]
            )
            df_gapfilled = pd.concat([df_gapfilled, df_new_record_after])

    return df_gapfilled


def has_gaps(df: pd.DataFrame, threshold: pd.Timedelta) -> bool:
    """Check if a DataFrame has gaps larger than the threshold.

    Args:
        df: DataFrame with DatetimeIndex.
        threshold: Minimum duration to consider as a gap.

    Returns:
        True if gaps are found, False otherwise.
    """
    if len(df) < 2:
        return False
    deltas = df.index.diff()[1:]
    return (deltas >= threshold).any()


def count_gaps(df: pd.DataFrame, threshold: pd.Timedelta) -> int:
    """Count the number of gaps in a DataFrame.

    Args:
        df: DataFrame with DatetimeIndex.
        threshold: Minimum duration to consider as a gap.

    Returns:
        Number of gaps found.
    """
    if len(df) < 2:
        return 0
    deltas = df.index.diff()[1:]
    return (deltas >= threshold).sum()
