"""Comparison engine for evaluating downsampling methods and cadences."""

from dataclasses import dataclass, field
from typing import Any
import pandas as pd

from downsampler.config import DownsampleConfig, AggregationMethod
from downsampler.core import downsample
from downsampler.fidelity.metrics import FidelityMetrics, compute_metrics, compute_reduction_ratio
from downsampler.utils import parse_cadence


@dataclass
class ComparisonResult:
    """Result of a single downsampling comparison.

    Attributes:
        method: The aggregation method used.
        cadence: The target cadence.
        metrics: Fidelity metrics for this result.
        reduction_ratio: Data reduction ratio (original/downsampled rows).
        config: The full configuration used.
        downsampled: The downsampled DataFrame (optional, may be None if not stored).
    """
    method: AggregationMethod
    cadence: pd.Timedelta
    metrics: FidelityMetrics
    reduction_ratio: float
    config: DownsampleConfig
    downsampled: pd.DataFrame | None = None

    def to_dict(self) -> dict:
        """Convert result to a dictionary."""
        return {
            'method': self.method.value,
            'cadence': str(self.cadence),
            'reduction_ratio': self.reduction_ratio,
            **self.metrics.to_dict(),
        }


class FidelityComparison:
    """Engine for comparing downsampling methods and cadences.

    Example:
        >>> original = pd.DataFrame(
        ...     {'signal': np.sin(np.linspace(0, 10*np.pi, 10000))},
        ...     index=pd.date_range('2024-01-01', periods=10000, freq='1s')
        ... )
        >>> comp = FidelityComparison(original, 'signal')
        >>> results = comp.compare_methods('1min')
        >>> for r in results:
        ...     print(f"{r.method.value}: RMSE={r.metrics.rmse:.4f}")
    """

    def __init__(
        self,
        original_df: pd.DataFrame,
        column: str,
        peak_prominence: float | None = None
    ):
        """Initialize the comparison engine.

        Args:
            original_df: The original high-cadence DataFrame.
            column: The column to use for comparisons.
            peak_prominence: Minimum prominence for peak detection.
        """
        self.original_df = original_df
        self.column = column
        self.peak_prominence = peak_prominence
        self._results: list[ComparisonResult] = []

    def compare_methods(
        self,
        target_cadence: str | pd.Timedelta,
        methods: list[AggregationMethod] | None = None,
        lttb_target_column: str | None = None,
        store_downsampled: bool = False
    ) -> list[ComparisonResult]:
        """Compare different downsampling methods at a fixed cadence.

        Args:
            target_cadence: Target cadence for all comparisons.
            methods: List of methods to compare. If None, compares all methods.
            lttb_target_column: Column to optimize for LTTB. Defaults to
                the comparison column.
            store_downsampled: Whether to store downsampled DataFrames in results.

        Returns:
            List of ComparisonResult objects.
        """
        target_cadence = parse_cadence(target_cadence)

        if methods is None:
            methods = list(AggregationMethod)

        if lttb_target_column is None:
            lttb_target_column = self.column

        results = []
        for method in methods:
            config = DownsampleConfig(
                method=method,
                lttb_target_column=lttb_target_column if method == AggregationMethod.LTTB else None,
            )

            try:
                downsampled = downsample(self.original_df, target_cadence, config)
            except Exception as e:
                # Log and skip failed methods
                print(f"Warning: {method.value} failed: {e}")
                continue

            if len(downsampled) == 0:
                continue

            metrics = compute_metrics(
                self.original_df,
                downsampled,
                self.column,
                self.peak_prominence
            )

            reduction_ratio = compute_reduction_ratio(self.original_df, downsampled)

            result = ComparisonResult(
                method=method,
                cadence=target_cadence,
                metrics=metrics,
                reduction_ratio=reduction_ratio,
                config=config,
                downsampled=downsampled if store_downsampled else None,
            )
            results.append(result)

        self._results.extend(results)
        return results

    def compare_cadences(
        self,
        cadences: list[str | pd.Timedelta],
        method: AggregationMethod = AggregationMethod.MEAN,
        lttb_target_column: str | None = None,
        store_downsampled: bool = False
    ) -> list[ComparisonResult]:
        """Compare different cadences using a fixed method.

        Args:
            cadences: List of target cadences to compare.
            method: Downsampling method to use.
            lttb_target_column: Column to optimize for LTTB.
            store_downsampled: Whether to store downsampled DataFrames.

        Returns:
            List of ComparisonResult objects.
        """
        if lttb_target_column is None:
            lttb_target_column = self.column

        results = []
        for cadence in cadences:
            cadence = parse_cadence(cadence)

            config = DownsampleConfig(
                method=method,
                lttb_target_column=lttb_target_column if method == AggregationMethod.LTTB else None,
            )

            try:
                downsampled = downsample(self.original_df, cadence, config)
            except Exception as e:
                print(f"Warning: cadence {cadence} failed: {e}")
                continue

            if len(downsampled) == 0:
                continue

            metrics = compute_metrics(
                self.original_df,
                downsampled,
                self.column,
                self.peak_prominence
            )

            reduction_ratio = compute_reduction_ratio(self.original_df, downsampled)

            result = ComparisonResult(
                method=method,
                cadence=cadence,
                metrics=metrics,
                reduction_ratio=reduction_ratio,
                config=config,
                downsampled=downsampled if store_downsampled else None,
            )
            results.append(result)

        self._results.extend(results)
        return results

    def compare_grid(
        self,
        cadences: list[str | pd.Timedelta],
        methods: list[AggregationMethod] | None = None,
        lttb_target_column: str | None = None,
        store_downsampled: bool = False
    ) -> list[ComparisonResult]:
        """Compare all combinations of cadences and methods.

        Args:
            cadences: List of target cadences.
            methods: List of methods. If None, uses all methods.
            lttb_target_column: Column to optimize for LTTB.
            store_downsampled: Whether to store downsampled DataFrames.

        Returns:
            List of ComparisonResult objects.
        """
        if methods is None:
            methods = list(AggregationMethod)

        if lttb_target_column is None:
            lttb_target_column = self.column

        results = []
        for cadence in cadences:
            for method in methods:
                cadence_parsed = parse_cadence(cadence)

                config = DownsampleConfig(
                    method=method,
                    lttb_target_column=lttb_target_column if method == AggregationMethod.LTTB else None,
                )

                try:
                    downsampled = downsample(self.original_df, cadence_parsed, config)
                except Exception:
                    continue

                if len(downsampled) == 0:
                    continue

                metrics = compute_metrics(
                    self.original_df,
                    downsampled,
                    self.column,
                    self.peak_prominence
                )

                reduction_ratio = compute_reduction_ratio(self.original_df, downsampled)

                result = ComparisonResult(
                    method=method,
                    cadence=cadence_parsed,
                    metrics=metrics,
                    reduction_ratio=reduction_ratio,
                    config=config,
                    downsampled=downsampled if store_downsampled else None,
                )
                results.append(result)

        self._results.extend(results)
        return results

    def summary_table(self, results: list[ComparisonResult] | None = None) -> pd.DataFrame:
        """Generate a summary table from comparison results.

        Args:
            results: List of results to summarize. If None, uses all
                results from this comparison engine.

        Returns:
            DataFrame with metrics for each method/cadence combination.
        """
        if results is None:
            results = self._results

        if not results:
            return pd.DataFrame()

        rows = [r.to_dict() for r in results]
        return pd.DataFrame(rows)

    def recommend_settings(
        self,
        target_cadence: str | pd.Timedelta,
        priority: str = "visual"
    ) -> DownsampleConfig:
        """Recommend downsampling settings based on comparison results.

        Args:
            target_cadence: Target cadence for the recommendation.
            priority: Optimization priority:
                - "visual": Minimize visual error (RMSE + peak_error)
                - "peaks": Prioritize peak preservation
                - "correlation": Maximize correlation
                - "speed": Prefer simple aggregation methods

        Returns:
            Recommended DownsampleConfig.
        """
        target_cadence = parse_cadence(target_cadence)

        # Run comparison if we don't have results for this cadence
        relevant_results = [r for r in self._results if r.cadence == target_cadence]
        if not relevant_results:
            relevant_results = self.compare_methods(target_cadence)

        if not relevant_results:
            # Return default config if no results
            return DownsampleConfig()

        # Score each result based on priority
        def score(r: ComparisonResult) -> float:
            m = r.metrics
            if priority == "visual":
                # Lower is better for RMSE and peak_error
                return m.rmse + 0.5 * m.peak_error
            elif priority == "peaks":
                # Closer to 1.0 is better for peak_count_ratio
                return abs(1.0 - m.peak_count_ratio) + 0.1 * m.peak_error
            elif priority == "correlation":
                # Higher is better for pearson_r
                return -m.pearson_r
            elif priority == "speed":
                # Prefer simple methods
                method_penalty = {
                    AggregationMethod.MEAN: 0,
                    AggregationMethod.MIN: 0,
                    AggregationMethod.MAX: 0,
                    AggregationMethod.MEDIAN: 0.1,
                    AggregationMethod.LTTB: 0.2,
                }
                return m.rmse + method_penalty.get(r.method, 0)
            else:
                return m.rmse

        best = min(relevant_results, key=score)
        return best.config

    def clear_results(self):
        """Clear stored comparison results."""
        self._results = []
