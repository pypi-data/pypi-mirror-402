"""Deferred/lazy data fetching API for downsampling.

This module provides tools for downsampling when data needs to be fetched
from an external source (e.g., API, database). It handles edge buffering
automatically to ensure stable output at the boundaries.
"""

import logging
from typing import Callable, Protocol
import pandas as pd

from downsampler.config import DownsampleConfig, EdgeHandling
from downsampler.core import downsample
from downsampler.edges import compute_edge_buffer, trim_edges_by_time, expand_time_range
from downsampler.utils import parse_cadence


class DataFetcher(Protocol):
    """Protocol for data fetching functions.

    A DataFetcher is a callable that retrieves data for a given time range.
    """
    def __call__(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp
    ) -> pd.DataFrame:
        """Fetch data for the given time range.

        Args:
            start: Start of time range (inclusive).
            end: End of time range (exclusive).

        Returns:
            DataFrame with DatetimeIndex containing data in the time range.
        """
        ...


def deferred_downsample(
    fetcher: Callable[[pd.Timestamp, pd.Timestamp], pd.DataFrame],
    output_start: pd.Timestamp,
    output_end: pd.Timestamp,
    target_cadence: str | pd.Timedelta,
    config: DownsampleConfig | None = None,
    edge_buffer_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Downsample with automatic data fetching and edge buffering.

    Automatically fetches extra data at edges for stable output. This is
    useful when downsampling data that needs to be retrieved from an
    external source (API, database, file).

    The function:
    1. Computes the required fetch range (output range + edge buffer)
    2. Calls the fetcher to retrieve data
    3. Performs downsampling
    4. Trims the result to the requested output range

    Args:
        fetcher: Function that retrieves data for a given time range.
            Signature: fetcher(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame
        output_start: Start of desired output time range.
        output_end: End of desired output time range.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        config: Downsampling configuration. If None, uses default config.
        edge_buffer_multiplier: Multiplier for edge buffer calculation.
            Higher values provide more stable edges but require fetching
            more data.

    Returns:
        Downsampled DataFrame covering the requested output range.

    Example:
        >>> def fetch_from_api(start, end):
        ...     # Simulate API call
        ...     return pd.DataFrame(
        ...         {'value': range(100)},
        ...         index=pd.date_range(start, end, periods=100)
        ...     )
        >>>
        >>> result = deferred_downsample(
        ...     fetcher=fetch_from_api,
        ...     output_start=pd.Timestamp('2024-01-01 00:00'),
        ...     output_end=pd.Timestamp('2024-01-01 12:00'),
        ...     target_cadence='1H'
        ... )
    """
    if config is None:
        config = DownsampleConfig()

    target_cadence = parse_cadence(target_cadence)

    # Compute edge buffer
    edge_buffer = compute_edge_buffer(
        target_cadence,
        config.edge_window,
        edge_buffer_multiplier
    )

    # Expand time range for fetching
    fetch_start, fetch_end = expand_time_range(
        output_start, output_end, edge_buffer
    )

    logging.debug(
        f"Fetching data from {fetch_start} to {fetch_end} "
        f"(buffer: {edge_buffer}) for output range {output_start} to {output_end}"
    )

    # Fetch data
    df = fetcher(fetch_start, fetch_end)

    if df is None or len(df) == 0:
        logging.warning(f"Fetcher returned empty DataFrame for {fetch_start} to {fetch_end}")
        return pd.DataFrame()

    # Create a config with edge handling disabled (we'll handle it via trimming)
    config_no_edges = DownsampleConfig(
        method=config.method,
        lttb_target_column=config.lttb_target_column,
        include_columns=config.include_columns,
        exclude_columns=config.exclude_columns,
        gap_handling=config.gap_handling,
        gap_threshold=config.gap_threshold,
        edge_handling=EdgeHandling.KEEP,  # Keep edges, we'll trim
        edge_window=config.edge_window,
        min_points_per_segment=config.min_points_per_segment,
    )

    # Perform downsampling
    result = downsample(df, target_cadence, config_no_edges)

    if len(result) == 0:
        return result

    # Trim to requested output range
    result = trim_edges_by_time(result, output_start, output_end)

    return result


def batch_deferred_downsample(
    fetcher: Callable[[pd.Timestamp, pd.Timestamp], pd.DataFrame],
    output_start: pd.Timestamp,
    output_end: pd.Timestamp,
    target_cadence: str | pd.Timedelta,
    batch_size: str | pd.Timedelta = 'P1D',
    config: DownsampleConfig | None = None,
    edge_buffer_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Downsample large time ranges in batches.

    Useful when the data is too large to fetch and process in one go.
    The function processes the time range in batches, fetching extra
    data at batch boundaries for stable results.

    Args:
        fetcher: Function that retrieves data for a given time range.
        output_start: Start of desired output time range.
        output_end: End of desired output time range.
        target_cadence: Target cadence as ISO duration string or Timedelta.
        batch_size: Size of each processing batch.
        config: Downsampling configuration.
        edge_buffer_multiplier: Multiplier for edge buffer calculation.

    Returns:
        Downsampled DataFrame covering the requested output range.

    Example:
        >>> result = batch_deferred_downsample(
        ...     fetcher=fetch_from_api,
        ...     output_start=pd.Timestamp('2024-01-01'),
        ...     output_end=pd.Timestamp('2024-02-01'),
        ...     target_cadence='1H',
        ...     batch_size='P1D'  # Process one day at a time
        ... )
    """
    if config is None:
        config = DownsampleConfig()

    target_cadence = parse_cadence(target_cadence)
    batch_size = parse_cadence(batch_size)

    results = []

    # Process in batches
    current_start = output_start
    while current_start < output_end:
        current_end = min(current_start + batch_size, output_end)

        logging.info(f"Processing batch: {current_start} to {current_end}")

        batch_result = deferred_downsample(
            fetcher=fetcher,
            output_start=current_start,
            output_end=current_end,
            target_cadence=target_cadence,
            config=config,
            edge_buffer_multiplier=edge_buffer_multiplier,
        )

        if len(batch_result) > 0:
            results.append(batch_result)

        current_start = current_end

    if not results:
        return pd.DataFrame()

    # Concatenate and sort
    result = pd.concat(results).sort_index()

    # Remove any duplicates that might occur at batch boundaries
    result = result[~result.index.duplicated(keep='first')]

    return result


class LazyDownsampler:
    """A lazy downsampler that caches fetched data.

    Useful when you need to downsample to multiple cadences or compare
    different methods on the same data without re-fetching.

    Example:
        >>> lazy = LazyDownsampler(fetch_from_api)
        >>> result_1h = lazy.downsample(
        ...     pd.Timestamp('2024-01-01'),
        ...     pd.Timestamp('2024-01-02'),
        ...     '1H'
        ... )
        >>> result_30min = lazy.downsample(
        ...     pd.Timestamp('2024-01-01'),
        ...     pd.Timestamp('2024-01-02'),
        ...     '30min'
        ... )  # Uses cached data if sufficient
    """

    def __init__(
        self,
        fetcher: Callable[[pd.Timestamp, pd.Timestamp], pd.DataFrame],
        cache_buffer: str | pd.Timedelta = 'PT1H'
    ):
        """Initialize the lazy downsampler.

        Args:
            fetcher: Function that retrieves data for a given time range.
            cache_buffer: Extra time to fetch beyond requested range for caching.
        """
        self.fetcher = fetcher
        self.cache_buffer = parse_cadence(cache_buffer)
        self._cache: pd.DataFrame | None = None
        self._cache_start: pd.Timestamp | None = None
        self._cache_end: pd.Timestamp | None = None

    def _ensure_cache(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Ensure data is cached for the requested range.

        Args:
            start: Start of required range.
            end: End of required range.

        Returns:
            Cached DataFrame covering at least the requested range.
        """
        # Check if current cache covers the range
        if (
            self._cache is not None
            and self._cache_start is not None
            and self._cache_end is not None
            and self._cache_start <= start
            and self._cache_end >= end
        ):
            return self._cache

        # Need to fetch (or extend cache)
        fetch_start = start - self.cache_buffer
        fetch_end = end + self.cache_buffer

        logging.info(f"LazyDownsampler: fetching {fetch_start} to {fetch_end}")
        self._cache = self.fetcher(fetch_start, fetch_end)
        self._cache_start = fetch_start
        self._cache_end = fetch_end

        return self._cache

    def downsample(
        self,
        output_start: pd.Timestamp,
        output_end: pd.Timestamp,
        target_cadence: str | pd.Timedelta,
        config: DownsampleConfig | None = None,
        edge_buffer_multiplier: float = 2.0,
    ) -> pd.DataFrame:
        """Downsample using cached data.

        Args:
            output_start: Start of desired output time range.
            output_end: End of desired output time range.
            target_cadence: Target cadence.
            config: Downsampling configuration.
            edge_buffer_multiplier: Multiplier for edge buffer.

        Returns:
            Downsampled DataFrame.
        """
        if config is None:
            config = DownsampleConfig()

        target_cadence = parse_cadence(target_cadence)

        # Compute required fetch range with edge buffer
        edge_buffer = compute_edge_buffer(
            target_cadence,
            config.edge_window,
            edge_buffer_multiplier
        )
        fetch_start = output_start - edge_buffer
        fetch_end = output_end + edge_buffer

        # Ensure cache covers the range
        df = self._ensure_cache(fetch_start, fetch_end)

        # Slice to required range
        df_slice = df[(df.index >= fetch_start) & (df.index < fetch_end)]

        if len(df_slice) == 0:
            return pd.DataFrame()

        # Create config without edge handling
        config_no_edges = DownsampleConfig(
            method=config.method,
            lttb_target_column=config.lttb_target_column,
            include_columns=config.include_columns,
            exclude_columns=config.exclude_columns,
            gap_handling=config.gap_handling,
            gap_threshold=config.gap_threshold,
            edge_handling=EdgeHandling.KEEP,
            edge_window=config.edge_window,
            min_points_per_segment=config.min_points_per_segment,
        )

        # Downsample
        result = downsample(df_slice, target_cadence, config_no_edges)

        if len(result) == 0:
            return result

        # Trim to output range
        return trim_edges_by_time(result, output_start, output_end)

    def clear_cache(self):
        """Clear the cached data."""
        self._cache = None
        self._cache_start = None
        self._cache_end = None
