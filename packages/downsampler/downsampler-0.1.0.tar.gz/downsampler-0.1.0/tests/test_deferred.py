"""Tests for deferred/lazy data fetching API."""

import pytest
import pandas as pd
import numpy as np

from downsampler.deferred import (
    deferred_downsample,
    batch_deferred_downsample,
    LazyDownsampler,
)
from downsampler.config import DownsampleConfig, AggregationMethod


def create_test_fetcher(cadence='1s', value_func=None):
    """Create a test fetcher function."""
    def fetcher(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        index = pd.date_range(start, end, freq=cadence)
        if len(index) == 0:
            return pd.DataFrame({'value': []}, index=pd.DatetimeIndex([]))

        if value_func is None:
            # Default: sine wave
            t = np.linspace(0, 2 * np.pi, len(index))
            values = np.sin(t)
        else:
            values = value_func(index)

        return pd.DataFrame({'value': values}, index=index)

    return fetcher


class TestDeferredDownsample:
    """Tests for deferred_downsample function."""

    def test_basic_deferred(self):
        """Test basic deferred downsampling."""
        fetcher = create_test_fetcher()

        result = deferred_downsample(
            fetcher=fetcher,
            output_start=pd.Timestamp('2024-01-01 00:00'),
            output_end=pd.Timestamp('2024-01-01 01:00'),
            target_cadence='PT1M'
        )

        assert len(result) > 0
        assert result.index[0] >= pd.Timestamp('2024-01-01 00:00')
        assert result.index[-1] < pd.Timestamp('2024-01-01 01:00')

    def test_with_config(self):
        """Test deferred downsampling with config."""
        fetcher = create_test_fetcher()
        config = DownsampleConfig(method=AggregationMethod.MAX)

        result = deferred_downsample(
            fetcher=fetcher,
            output_start=pd.Timestamp('2024-01-01 00:00'),
            output_end=pd.Timestamp('2024-01-01 01:00'),
            target_cadence='PT5M',
            config=config
        )

        assert len(result) > 0

    def test_empty_fetch_result(self):
        """Test handling of empty fetch result."""
        def empty_fetcher(start, end):
            return pd.DataFrame({'value': []}, index=pd.DatetimeIndex([]))

        result = deferred_downsample(
            fetcher=empty_fetcher,
            output_start=pd.Timestamp('2024-01-01 00:00'),
            output_end=pd.Timestamp('2024-01-01 01:00'),
            target_cadence='PT1M'
        )

        assert len(result) == 0


class TestBatchDeferredDownsample:
    """Tests for batch_deferred_downsample function."""

    def test_basic_batch(self):
        """Test basic batch downsampling."""
        fetcher = create_test_fetcher()

        result = batch_deferred_downsample(
            fetcher=fetcher,
            output_start=pd.Timestamp('2024-01-01 00:00'),
            output_end=pd.Timestamp('2024-01-01 06:00'),
            target_cadence='PT10M',
            batch_size='PT1H'
        )

        assert len(result) > 0

    def test_batch_continuity(self):
        """Test that batches produce continuous results."""
        fetcher = create_test_fetcher()

        result = batch_deferred_downsample(
            fetcher=fetcher,
            output_start=pd.Timestamp('2024-01-01 00:00'),
            output_end=pd.Timestamp('2024-01-01 06:00'),
            target_cadence='PT5M',
            batch_size='PT1H'
        )

        # Check no duplicates
        assert not result.index.duplicated().any()

        # Check sorted
        assert result.index.is_monotonic_increasing


class TestLazyDownsampler:
    """Tests for LazyDownsampler class."""

    def test_caching(self):
        """Test that data is cached."""
        fetch_count = [0]

        def counting_fetcher(start, end):
            fetch_count[0] += 1
            index = pd.date_range(start, end, freq='1s')
            return pd.DataFrame({'value': np.arange(len(index))}, index=index)

        lazy = LazyDownsampler(counting_fetcher, cache_buffer='PT5M')

        # First call should fetch
        result1 = lazy.downsample(
            pd.Timestamp('2024-01-01 00:00'),
            pd.Timestamp('2024-01-01 00:30'),
            'PT1M'
        )
        assert fetch_count[0] == 1

        # Second call within cache range should not fetch
        result2 = lazy.downsample(
            pd.Timestamp('2024-01-01 00:10'),
            pd.Timestamp('2024-01-01 00:20'),
            'PT1M'
        )
        assert fetch_count[0] == 1

    def test_cache_clear(self):
        """Test cache clearing."""
        fetch_count = [0]

        def counting_fetcher(start, end):
            fetch_count[0] += 1
            index = pd.date_range(start, end, freq='1s')
            return pd.DataFrame({'value': np.arange(len(index))}, index=index)

        lazy = LazyDownsampler(counting_fetcher)

        lazy.downsample(
            pd.Timestamp('2024-01-01 00:00'),
            pd.Timestamp('2024-01-01 00:30'),
            'PT1M'
        )
        assert fetch_count[0] == 1

        lazy.clear_cache()

        lazy.downsample(
            pd.Timestamp('2024-01-01 00:00'),
            pd.Timestamp('2024-01-01 00:30'),
            'PT1M'
        )
        assert fetch_count[0] == 2
