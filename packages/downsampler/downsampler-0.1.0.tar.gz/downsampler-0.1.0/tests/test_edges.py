"""Tests for edge handling functionality."""

import pytest
import pandas as pd
import numpy as np

from downsampler.edges import (
    identify_edge_points,
    apply_edge_handling,
    compute_edge_buffer,
    trim_edges_by_time,
    expand_time_range,
)
from downsampler.config import EdgeHandling


class TestIdentifyEdgePoints:
    """Tests for edge point identification."""

    def test_basic_identification(self, simple_df):
        """Test basic edge point identification."""
        edges = identify_edge_points(simple_df, edge_window=2)

        # First 2 and last 2 should be edges
        assert edges.iloc[0] == True
        assert edges.iloc[1] == True
        assert edges.iloc[2] == False
        assert edges.iloc[-2] == True
        assert edges.iloc[-1] == True

    def test_small_dataframe_all_edges(self):
        """Test that small DataFrame has all edges."""
        small_df = pd.DataFrame(
            {'value': [1, 2, 3]},
            index=pd.date_range('2024-01-01', periods=3, freq='1min')
        )
        edges = identify_edge_points(small_df, edge_window=2)

        assert edges.all()


class TestApplyEdgeHandling:
    """Tests for applying edge handling strategies."""

    def test_keep_strategy(self, simple_df):
        """Test KEEP strategy returns unchanged DataFrame."""
        result = apply_edge_handling(simple_df, EdgeHandling.KEEP)

        assert len(result) == len(simple_df)
        assert '_is_edge' not in result.columns

    def test_flag_strategy(self, simple_df):
        """Test FLAG strategy adds edge column."""
        result = apply_edge_handling(simple_df, EdgeHandling.FLAG, edge_window=2)

        assert '_is_edge' in result.columns
        assert result['_is_edge'].sum() == 4  # 2 at each end

    def test_discard_strategy(self, simple_df):
        """Test DISCARD strategy removes edges."""
        result = apply_edge_handling(simple_df, EdgeHandling.DISCARD, edge_window=2)

        assert len(result) == len(simple_df) - 4
        assert '_is_edge' not in result.columns


class TestComputeEdgeBuffer:
    """Tests for edge buffer computation."""

    def test_basic_buffer(self):
        """Test basic edge buffer computation."""
        buffer = compute_edge_buffer(
            pd.Timedelta('1H'),
            edge_window=2,
            multiplier=2.0
        )

        assert buffer == pd.Timedelta('4H')

    def test_different_multiplier(self):
        """Test with different multiplier."""
        buffer = compute_edge_buffer(
            pd.Timedelta('1H'),
            edge_window=2,
            multiplier=1.5
        )

        assert buffer == pd.Timedelta('3H')


class TestTrimEdgesByTime:
    """Tests for trimming edges by time."""

    def test_basic_trim(self, simple_df):
        """Test basic time-based trimming."""
        start = pd.Timestamp('2024-01-01 00:10')
        end = pd.Timestamp('2024-01-01 00:50')

        result = trim_edges_by_time(simple_df, start, end)

        assert result.index[0] >= start
        assert result.index[-1] < end


class TestExpandTimeRange:
    """Tests for expanding time range."""

    def test_basic_expansion(self):
        """Test basic time range expansion."""
        start = pd.Timestamp('2024-01-01 12:00')
        end = pd.Timestamp('2024-01-01 18:00')
        buffer = pd.Timedelta('1H')

        exp_start, exp_end = expand_time_range(start, end, buffer)

        assert exp_start == pd.Timestamp('2024-01-01 11:00')
        assert exp_end == pd.Timestamp('2024-01-01 19:00')
