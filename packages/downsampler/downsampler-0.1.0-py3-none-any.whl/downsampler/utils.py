"""Utility functions for downsampler."""

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


def estimate_cadence(df: pd.DataFrame) -> pd.Timedelta:
    """Estimate the cadence of a time series DataFrame.

    Uses the median of time differences to be robust to gaps.

    Args:
        df: DataFrame with DatetimeIndex.

    Returns:
        Estimated cadence as a Timedelta.

    Raises:
        ValueError: If DataFrame has fewer than 2 rows.
    """
    if len(df) < 2:
        raise ValueError("DataFrame must have at least 2 rows to estimate cadence")

    deltas = pd.Series(df.index).diff().dropna()
    return deltas.median()


def parse_cadence(cadence: str | pd.Timedelta) -> pd.Timedelta:
    """Parse a cadence specification into a Timedelta.

    Args:
        cadence: Either a Timedelta or an ISO 8601 duration string
            (e.g., "PT1H", "P1D").

    Returns:
        The cadence as a Timedelta.
    """
    if isinstance(cadence, pd.Timedelta):
        return cadence
    return pd.to_timedelta(cadence)


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Get list of numeric columns in a DataFrame.

    Args:
        df: Input DataFrame.

    Returns:
        List of column names that have numeric dtype.
    """
    return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]


def filter_columns(
    df: pd.DataFrame,
    include: list[str] | None = None,
    exclude: list[str] | None = None
) -> list[str]:
    """Filter columns based on include/exclude lists.

    Args:
        df: Input DataFrame.
        include: Columns to include. If empty or None, all columns are included.
        exclude: Columns to exclude.

    Returns:
        Filtered list of column names.
    """
    columns = list(df.columns)

    if include:
        columns = [c for c in columns if c in include]

    if exclude:
        columns = [c for c in columns if c not in exclude]

    return columns


def setup_interpolator(
    dataframe: pd.DataFrame,
    field: str,
    kind: str = 'linear'
) -> callable:
    """Set up an interpolation function for a DataFrame column.

    Args:
        dataframe: Input DataFrame with DatetimeIndex.
        field: Column name to interpolate.
        kind: Type of interpolation ('linear', 'cubic', etc.).

    Returns:
        A function that takes a timestamp and returns the interpolated value.
    """
    reftime = dataframe.index[0]
    raw_interpolator = interp1d(
        x=((dataframe.index - reftime) / pd.to_timedelta(1, 'min')),
        y=dataframe[field],
        kind=kind,
        bounds_error=False,
        fill_value=np.nan
    )

    def func(t):
        result = raw_interpolator((t - reftime) / pd.to_timedelta(1, 'min'))
        if np.shape(result) == ():  # Convert to float if result is scalar
            result = float(result)
        return result

    return func


def setup_interpolators(
    dataframe: pd.DataFrame,
    kind: str = 'linear'
) -> dict[str, callable]:
    """Set up interpolation functions for all numeric columns in a DataFrame.

    Args:
        dataframe: Input DataFrame with DatetimeIndex.
        kind: Type of interpolation ('linear', 'cubic', etc.).

    Returns:
        Dictionary mapping column names to interpolation functions.
    """
    interpolators = {}
    fields = get_numeric_columns(dataframe)
    for field in fields:
        interpolators[field] = setup_interpolator(dataframe, field, kind)
    return interpolators


def compute_output_points(
    start: pd.Timestamp,
    end: pd.Timestamp,
    target_cadence: pd.Timedelta
) -> int:
    """Compute the number of output points for a given time range and cadence.

    Args:
        start: Start timestamp.
        end: End timestamp.
        target_cadence: Target cadence.

    Returns:
        Number of output points.
    """
    return int(1 + (end - start) / target_cadence)
