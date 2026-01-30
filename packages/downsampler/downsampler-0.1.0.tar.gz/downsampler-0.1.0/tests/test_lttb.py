"""Tests for LTTB downsampling."""

import pytest
import pandas as pd
import numpy as np

from downsampler.lttb import downsample_lttb, downsample_lttb_with_config
from downsampler.config import DownsampleConfig, AggregationMethod


class TestDownsampleLttb:
    """Tests for LTTB downsampling function."""

    def test_basic_lttb(self, sine_df):
        """Test basic LTTB downsampling."""
        result = downsample_lttb(
            sine_df,
            target_column='signal',
            target_cadence='PT10S'
        )

        assert len(result) < len(sine_df)
        assert 'signal' in result.columns

    def test_preserves_extreme_values(self, sine_df):
        """Test that LTTB preserves extreme values reasonably well."""
        result = downsample_lttb(
            sine_df,
            target_column='signal',
            target_cadence='PT10S'
        )

        # Check that max/min are close to original
        orig_max = sine_df['signal'].max()
        orig_min = sine_df['signal'].min()
        result_max = result['signal'].max()
        result_min = result['signal'].min()

        # Allow 10% tolerance
        assert abs(result_max - orig_max) < 0.1 * abs(orig_max)
        assert abs(result_min - orig_min) < 0.1 * abs(orig_min - orig_max)

    def test_include_columns(self, sine_df):
        """Test including additional columns."""
        result = downsample_lttb(
            sine_df,
            target_column='signal',
            target_cadence='PT10S',
            include_columns=['signal', 'noise']
        )

        assert 'signal' in result.columns
        assert 'noise' in result.columns

    def test_gap_handling(self, gappy_df):
        """Test LTTB with gappy data."""
        # Add a target column
        gappy_df['signal'] = np.sin(np.linspace(0, 4 * np.pi, len(gappy_df)))

        result = downsample_lttb(
            gappy_df,
            target_column='signal',
            target_cadence='PT5M',
            gap_threshold=pd.Timedelta('30min')
        )

        # Should produce output from both segments
        assert len(result) > 0

    def test_insufficient_points(self):
        """Test handling of insufficient points."""
        small_df = pd.DataFrame(
            {'value': [1, 2]},
            index=pd.date_range('2024-01-01', periods=2, freq='1s')
        )

        result = downsample_lttb(
            small_df,
            target_column='value',
            target_cadence='PT10S',
            min_points_per_segment=3
        )

        # Should return empty or minimal result
        assert len(result) == 0


class TestDownsampleLttbWithConfig:
    """Tests for LTTB downsampling with config."""

    def test_with_config(self, sine_df):
        """Test LTTB with full configuration."""
        config = DownsampleConfig(
            method=AggregationMethod.LTTB,
            lttb_target_column='signal',
            min_points_per_segment=5
        )

        result = downsample_lttb_with_config(
            sine_df,
            'PT10S',
            config
        )

        assert len(result) > 0

    def test_missing_target_column_raises(self, sine_df):
        """Test that missing target column raises error."""
        config = DownsampleConfig(method=AggregationMethod.LTTB)

        with pytest.raises(ValueError, match="lttb_target_column"):
            downsample_lttb_with_config(sine_df, 'PT10S', config)
