"""Tests for gap detection and handling."""

import pytest
import pandas as pd
import numpy as np

from downsampler.gaps import (
    find_gap_indices,
    groupby_gaps,
    split_at_gaps,
    iter_segments,
    wrap_in_nans,
    mark_gaps_in_dataframe,
    has_gaps,
    count_gaps,
)


class TestFindGapIndices:
    """Tests for find_gap_indices function."""

    def test_no_gaps(self, simple_df):
        """Test DataFrame with no gaps."""
        gaps = find_gap_indices(simple_df, pd.Timedelta('5min'))
        assert len(gaps) == 0

    def test_single_gap(self, gappy_df):
        """Test DataFrame with a single gap."""
        gaps = find_gap_indices(gappy_df, pd.Timedelta('5min'))
        assert len(gaps) == 1

    def test_gap_threshold(self, gappy_df):
        """Test that gap threshold is respected."""
        # Should find gap with 5 min threshold
        gaps_5min = find_gap_indices(gappy_df, pd.Timedelta('5min'))
        assert len(gaps_5min) == 1

        # Should not find gap with 2 hour threshold
        gaps_2hr = find_gap_indices(gappy_df, pd.Timedelta('2H'))
        assert len(gaps_2hr) == 0


class TestSplitAtGaps:
    """Tests for split_at_gaps function."""

    def test_split_gappy_df(self, gappy_df):
        """Test splitting DataFrame at gaps."""
        segments = split_at_gaps(gappy_df, pd.Timedelta('5min'))

        assert len(segments) == 2
        assert len(segments[0]) == 50
        assert len(segments[1]) == 50

    def test_split_continuous_df(self, simple_df):
        """Test splitting continuous DataFrame (no split)."""
        segments = split_at_gaps(simple_df, pd.Timedelta('5min'))

        assert len(segments) == 1
        assert len(segments[0]) == len(simple_df)


class TestIterSegments:
    """Tests for iter_segments function."""

    def test_min_points_filter(self, gappy_df):
        """Test minimum points filtering."""
        # Both segments have 50 points each
        segments = list(iter_segments(gappy_df, pd.Timedelta('5min'), min_points=10))
        assert len(segments) == 2

        # Require more points than available
        segments = list(iter_segments(gappy_df, pd.Timedelta('5min'), min_points=100))
        assert len(segments) == 0


class TestWrapInNans:
    """Tests for wrap_in_nans function."""

    def test_wrap_both(self, simple_df):
        """Test wrapping with NaNs on both ends."""
        wrapped = wrap_in_nans(simple_df, offset='PT1S', where='both')

        assert len(wrapped) == len(simple_df) + 2
        assert np.isnan(wrapped.iloc[0]['value'])
        assert np.isnan(wrapped.iloc[-1]['value'])

    def test_wrap_start_only(self, simple_df):
        """Test wrapping with NaN at start only."""
        wrapped = wrap_in_nans(simple_df, offset='PT1S', where='start')

        assert len(wrapped) == len(simple_df) + 1
        assert np.isnan(wrapped.iloc[0]['value'])
        assert not np.isnan(wrapped.iloc[-1]['value'])


class TestMarkGapsInDataframe:
    """Tests for mark_gaps_in_dataframe function."""

    def test_mark_gaps(self, gappy_df):
        """Test marking gaps in DataFrame."""
        marked = mark_gaps_in_dataframe(
            gappy_df,
            nominal_timedelta=pd.Timedelta('1min')
        )

        # Should have more rows due to NaN markers
        assert len(marked) > len(gappy_df)

        # Should have NaN values at gap
        assert marked['value'].isna().sum() > 0

    def test_no_gaps_unchanged(self, simple_df):
        """Test that DataFrame without gaps is unchanged."""
        marked = mark_gaps_in_dataframe(
            simple_df,
            nominal_timedelta=pd.Timedelta('1min')
        )

        # No NaN markers needed
        assert marked['value'].isna().sum() == 0


class TestHasGaps:
    """Tests for has_gaps function."""

    def test_gappy_df(self, gappy_df):
        """Test detection of gaps."""
        assert has_gaps(gappy_df, pd.Timedelta('5min'))
        assert not has_gaps(gappy_df, pd.Timedelta('2H'))

    def test_continuous_df(self, simple_df):
        """Test continuous DataFrame."""
        assert not has_gaps(simple_df, pd.Timedelta('5min'))


class TestCountGaps:
    """Tests for count_gaps function."""

    def test_count_single_gap(self, gappy_df):
        """Test counting single gap."""
        assert count_gaps(gappy_df, pd.Timedelta('5min')) == 1

    def test_count_no_gaps(self, simple_df):
        """Test counting no gaps."""
        assert count_gaps(simple_df, pd.Timedelta('5min')) == 0
