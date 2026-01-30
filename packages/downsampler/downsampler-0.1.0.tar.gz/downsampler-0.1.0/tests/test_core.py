"""Tests for core downsampling functionality."""

import pytest
import pandas as pd
import numpy as np

from downsampler import (
    downsample,
    downsample_multi_aggregate,
    DownsampleConfig,
    AggregationMethod,
)


class TestDownsample:
    """Tests for the main downsample function."""

    def test_basic_mean_downsampling(self, simple_df):
        """Test basic mean downsampling."""
        result = downsample(simple_df, '10min')

        assert len(result) < len(simple_df)
        assert 'value' in result.columns

    def test_method_kwarg(self, simple_df):
        """Test using method as keyword argument."""
        result = downsample(simple_df, '10min', method='max')

        # Max of 0-9 should be 9, max of 10-19 should be 19, etc.
        assert result['value'].iloc[0] == 9

    def test_config_object(self, simple_df):
        """Test using DownsampleConfig object."""
        config = DownsampleConfig(method=AggregationMethod.MIN)
        result = downsample(simple_df, '10min', config=config)

        # Min of 0-9 should be 0
        assert result['value'].iloc[0] == 0

    def test_lttb_method(self, sine_df):
        """Test LTTB downsampling method."""
        config = DownsampleConfig(
            method=AggregationMethod.LTTB,
            lttb_target_column='signal'
        )
        result = downsample(sine_df, 'PT10S', config=config)

        assert len(result) < len(sine_df)
        # LTTB should preserve signal shape reasonably well
        assert 'signal' in result.columns

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(
            {'value': []},
            index=pd.DatetimeIndex([])
        )
        result = downsample(empty_df, '1min')
        assert len(result) == 0

    def test_single_point_dataframe(self):
        """Test handling of single-point DataFrame."""
        single_df = pd.DataFrame(
            {'value': [1.0]},
            index=pd.DatetimeIndex(['2024-01-01'])
        )
        result = downsample(single_df, '1min')
        # Should handle gracefully (may be empty or single point)
        assert len(result) <= 1


class TestDownsampleMultiAggregate:
    """Tests for multi-aggregate downsampling."""

    def test_basic_multi_aggregate(self, multi_column_df):
        """Test basic multi-aggregate downsampling."""
        result = downsample_multi_aggregate(
            multi_column_df,
            'PT1M',
            variables=['temperature', 'pressure'],
            aggregations=['min', 'mean', 'max']
        )

        # Check expected columns exist
        assert 'temperature_min' in result.columns
        assert 'temperature_mean' in result.columns
        assert 'temperature_max' in result.columns
        assert 'pressure_min' in result.columns
        assert 'coverage' in result.columns

    def test_coverage_column(self, multi_column_df):
        """Test that coverage column is calculated."""
        result = downsample_multi_aggregate(
            multi_column_df,
            'PT1M',
            variables=['temperature'],
            source_cadence='PT1S'
        )

        # Coverage should be between 0 and 1
        assert result['coverage'].min() >= 0
        assert result['coverage'].max() <= 1.0

    def test_min_max_ordering(self, multi_column_df):
        """Test that min <= mean <= max."""
        result = downsample_multi_aggregate(
            multi_column_df,
            'PT1M',
            variables=['temperature'],
            aggregations=['min', 'mean', 'max']
        )

        valid_rows = result.dropna()
        assert (valid_rows['temperature_min'] <= valid_rows['temperature_mean']).all()
        assert (valid_rows['temperature_mean'] <= valid_rows['temperature_max']).all()
