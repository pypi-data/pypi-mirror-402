"""Tests for fidelity testing functionality."""

import pytest
import pandas as pd
import numpy as np

from downsampler.fidelity.metrics import (
    FidelityMetrics,
    compute_metrics,
    compute_reduction_ratio,
    compute_storage_savings,
)
from downsampler.fidelity.comparison import FidelityComparison, ComparisonResult
from downsampler.config import AggregationMethod


class TestFidelityMetrics:
    """Tests for FidelityMetrics dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = FidelityMetrics(
            mae=0.1,
            rmse=0.15,
            max_error=0.5,
            pearson_r=0.99,
            peak_error=0.2,
            peak_count_ratio=0.9,
            coverage=1.0
        )

        d = metrics.to_dict()
        assert d['mae'] == 0.1
        assert d['rmse'] == 0.15
        assert 'pearson_r' in d


class TestComputeMetrics:
    """Tests for compute_metrics function."""

    def test_identical_data(self, sine_df):
        """Test metrics for identical data."""
        metrics = compute_metrics(sine_df, sine_df, 'signal')

        assert metrics.mae == pytest.approx(0, abs=1e-10)
        assert metrics.rmse == pytest.approx(0, abs=1e-10)
        assert metrics.pearson_r == pytest.approx(1.0, abs=1e-10)

    def test_downsampled_data(self, sine_df):
        """Test metrics for downsampled data."""
        downsampled = sine_df.resample('10s').mean()  # Use pandas format, not ISO 8601

        metrics = compute_metrics(sine_df, downsampled, 'signal')

        # Should have some error but high correlation
        assert metrics.mae > 0
        assert metrics.pearson_r > 0.9
        assert metrics.coverage > 0

    def test_empty_data(self):
        """Test metrics for empty data."""
        empty = pd.DataFrame({'value': []}, index=pd.DatetimeIndex([]))
        metrics = compute_metrics(empty, empty, 'value')

        assert np.isnan(metrics.mae)
        assert metrics.coverage == 0


class TestComputeReductionRatio:
    """Tests for compute_reduction_ratio function."""

    def test_basic_ratio(self, sine_df):
        """Test basic reduction ratio calculation."""
        downsampled = sine_df.resample('10s').mean()  # Use pandas format, not ISO 8601

        ratio = compute_reduction_ratio(sine_df, downsampled)

        # 1000 points at 1s -> ~100 points at 10s
        assert ratio == pytest.approx(10, rel=0.2)

    def test_empty_downsampled(self, sine_df):
        """Test ratio with empty downsampled data."""
        empty = pd.DataFrame({'signal': []}, index=pd.DatetimeIndex([]))

        ratio = compute_reduction_ratio(sine_df, empty)

        assert ratio == float('inf')


class TestComputeStorageSavings:
    """Tests for compute_storage_savings function."""

    def test_basic_savings(self, sine_df):
        """Test basic storage savings calculation."""
        downsampled = sine_df.resample('10s').mean()  # Use pandas format, not ISO 8601

        savings = compute_storage_savings(sine_df, downsampled)

        # ~90% savings with 10x reduction
        assert 85 < savings < 95


class TestFidelityComparison:
    """Tests for FidelityComparison class."""

    def test_compare_methods(self, sine_df):
        """Test comparing different methods."""
        comp = FidelityComparison(sine_df, 'signal')
        results = comp.compare_methods('PT10S')

        # Should have results for multiple methods
        assert len(results) >= 2

        # All results should have valid metrics
        for r in results:
            assert not np.isnan(r.metrics.rmse)

    def test_compare_cadences(self, sine_df):
        """Test comparing different cadences."""
        comp = FidelityComparison(sine_df, 'signal')
        results = comp.compare_cadences(
            ['PT5S', 'PT10S', 'PT30S'],
            method=AggregationMethod.MEAN
        )

        assert len(results) == 3

        # Higher cadence should generally have lower error
        rmses = [r.metrics.rmse for r in results]
        assert rmses[0] <= rmses[2]  # 5s should have lower error than 30s

    def test_summary_table(self, sine_df):
        """Test summary table generation."""
        comp = FidelityComparison(sine_df, 'signal')
        comp.compare_methods('PT10S')

        table = comp.summary_table()

        assert isinstance(table, pd.DataFrame)
        assert 'method' in table.columns
        assert 'rmse' in table.columns

    def test_recommend_settings(self, sine_df):
        """Test settings recommendation."""
        comp = FidelityComparison(sine_df, 'signal')

        config = comp.recommend_settings('PT10S', priority='visual')

        assert config.method in AggregationMethod
