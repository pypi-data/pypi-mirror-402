"""Tests for aggregation-based downsampling."""

import pytest
import pandas as pd
import numpy as np

from downsampler.aggregators import (
    downsample_mean,
    downsample_median,
    downsample_min,
    downsample_max,
)


class TestDownsampleMean:
    """Tests for mean downsampling."""

    def test_basic_mean(self, simple_df):
        """Test basic mean downsampling."""
        result = downsample_mean(simple_df, '10min')

        # Mean of 0-9 should be 4.5
        assert result['value'].iloc[0] == pytest.approx(4.5)

    def test_column_selection(self, multi_column_df):
        """Test column selection."""
        result = downsample_mean(
            multi_column_df,
            'PT1M',
            columns=['temperature']
        )

        assert 'temperature' in result.columns
        # Other numeric columns should not be present
        assert 'pressure' not in result.columns


class TestDownsampleMedian:
    """Tests for median downsampling."""

    def test_basic_median(self, simple_df):
        """Test basic median downsampling."""
        result = downsample_median(simple_df, '10min')

        # Median of 0-9 should be 4.5
        assert result['value'].iloc[0] == pytest.approx(4.5)


class TestDownsampleMin:
    """Tests for min downsampling."""

    def test_basic_min(self, simple_df):
        """Test basic min downsampling."""
        result = downsample_min(simple_df, '10min')

        # Min of 0-9 should be 0
        assert result['value'].iloc[0] == 0
        # Min of 10-19 should be 10
        assert result['value'].iloc[1] == 10


class TestDownsampleMax:
    """Tests for max downsampling."""

    def test_basic_max(self, simple_df):
        """Test basic max downsampling."""
        result = downsample_max(simple_df, '10min')

        # Max of 0-9 should be 9
        assert result['value'].iloc[0] == 9
        # Max of 10-19 should be 19
        assert result['value'].iloc[1] == 19

    def test_with_gaps(self, gappy_df):
        """Test max downsampling with gaps."""
        result = downsample_max(
            gappy_df,
            '10min',
            gap_threshold=pd.Timedelta('30min')
        )

        # Should handle gaps gracefully
        assert len(result) > 0
