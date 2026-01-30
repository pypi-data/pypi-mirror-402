"""Statistical metrics for evaluating downsampling fidelity."""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks


@dataclass
class FidelityMetrics:
    """Metrics for evaluating the fidelity of downsampled data.

    Attributes:
        mae: Mean Absolute Error between original and interpolated downsampled.
        rmse: Root Mean Square Error.
        max_error: Maximum absolute error.
        pearson_r: Pearson correlation coefficient.
        peak_error: Mean absolute error at detected peaks.
        peak_count_ratio: Ratio of peaks preserved (downsampled / original).
        coverage: Fraction of original points that could be compared.
    """
    mae: float
    rmse: float
    max_error: float
    pearson_r: float
    peak_error: float
    peak_count_ratio: float
    coverage: float

    def to_dict(self) -> dict:
        """Convert metrics to a dictionary."""
        return {
            'mae': self.mae,
            'rmse': self.rmse,
            'max_error': self.max_error,
            'pearson_r': self.pearson_r,
            'peak_error': self.peak_error,
            'peak_count_ratio': self.peak_count_ratio,
            'coverage': self.coverage,
        }

    def __str__(self) -> str:
        """Format metrics as a readable string."""
        return (
            f"FidelityMetrics(\n"
            f"  MAE: {self.mae:.6f}\n"
            f"  RMSE: {self.rmse:.6f}\n"
            f"  Max Error: {self.max_error:.6f}\n"
            f"  Pearson r: {self.pearson_r:.4f}\n"
            f"  Peak Error: {self.peak_error:.6f}\n"
            f"  Peak Count Ratio: {self.peak_count_ratio:.2%}\n"
            f"  Coverage: {self.coverage:.2%}\n"
            f")"
        )


def compute_metrics(
    original: pd.DataFrame,
    downsampled: pd.DataFrame,
    column: str,
    peak_prominence: float | None = None
) -> FidelityMetrics:
    """Compute fidelity metrics comparing original and downsampled data.

    The downsampled data is interpolated back to the original timestamps
    for comparison.

    Args:
        original: Original high-cadence DataFrame.
        downsampled: Downsampled DataFrame.
        column: Column name to compare.
        peak_prominence: Minimum prominence for peak detection.
            If None, auto-calculated as 10% of data range.

    Returns:
        FidelityMetrics containing various comparison metrics.

    Example:
        >>> original = pd.DataFrame(
        ...     {'value': np.sin(np.linspace(0, 10*np.pi, 1000))},
        ...     index=pd.date_range('2024-01-01', periods=1000, freq='1s')
        ... )
        >>> downsampled = original.resample('10s').mean()
        >>> metrics = compute_metrics(original, downsampled, 'value')
        >>> metrics.pearson_r > 0.9
        True
    """
    # Get original values
    orig_values = original[column].dropna()
    if len(orig_values) == 0:
        return _empty_metrics()

    # Interpolate downsampled to original timestamps
    ds_values = downsampled[column].dropna()
    if len(ds_values) < 2:
        return _empty_metrics()

    # Create interpolated values at original timestamps
    orig_times_numeric = (orig_values.index - orig_values.index[0]) / pd.Timedelta('1s')
    ds_times_numeric = (ds_values.index - orig_values.index[0]) / pd.Timedelta('1s')

    # Only interpolate within the range of downsampled data
    mask = (orig_values.index >= ds_values.index[0]) & (orig_values.index <= ds_values.index[-1])
    orig_in_range = orig_values[mask]
    orig_times_in_range = orig_times_numeric[mask]

    if len(orig_in_range) == 0:
        return _empty_metrics()

    interpolated = np.interp(
        orig_times_in_range.values,
        ds_times_numeric.values,
        ds_values.values
    )

    # Compute basic metrics
    errors = orig_in_range.values - interpolated
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    max_error = np.max(np.abs(errors))

    # Pearson correlation
    if len(orig_in_range) > 1 and np.std(orig_in_range.values) > 0 and np.std(interpolated) > 0:
        pearson_r, _ = stats.pearsonr(orig_in_range.values, interpolated)
    else:
        pearson_r = 1.0 if np.allclose(orig_in_range.values, interpolated) else 0.0

    # Peak analysis
    if peak_prominence is None:
        data_range = np.max(orig_values.values) - np.min(orig_values.values)
        peak_prominence = 0.1 * data_range if data_range > 0 else 0.1

    orig_peaks, _ = find_peaks(orig_values.values, prominence=peak_prominence)
    ds_peaks, _ = find_peaks(ds_values.values, prominence=peak_prominence)

    # Peak count ratio
    if len(orig_peaks) > 0:
        peak_count_ratio = len(ds_peaks) / len(orig_peaks)
    else:
        peak_count_ratio = 1.0 if len(ds_peaks) == 0 else float('inf')

    # Peak error (error at original peak locations)
    if len(orig_peaks) > 0:
        peak_times_numeric = orig_times_numeric.values[orig_peaks]
        peak_interpolated = np.interp(peak_times_numeric, ds_times_numeric.values, ds_values.values)
        peak_errors = orig_values.values[orig_peaks] - peak_interpolated
        peak_error = np.mean(np.abs(peak_errors))
    else:
        peak_error = 0.0

    # Coverage
    coverage = len(orig_in_range) / len(orig_values)

    return FidelityMetrics(
        mae=mae,
        rmse=rmse,
        max_error=max_error,
        pearson_r=pearson_r,
        peak_error=peak_error,
        peak_count_ratio=peak_count_ratio,
        coverage=coverage,
    )


def _empty_metrics() -> FidelityMetrics:
    """Return empty/NaN metrics when comparison isn't possible."""
    return FidelityMetrics(
        mae=np.nan,
        rmse=np.nan,
        max_error=np.nan,
        pearson_r=np.nan,
        peak_error=np.nan,
        peak_count_ratio=np.nan,
        coverage=0.0,
    )


def compute_reduction_ratio(
    original: pd.DataFrame,
    downsampled: pd.DataFrame
) -> float:
    """Compute the data reduction ratio.

    Args:
        original: Original DataFrame.
        downsampled: Downsampled DataFrame.

    Returns:
        Ratio of original rows to downsampled rows.
    """
    if len(downsampled) == 0:
        return float('inf')
    return len(original) / len(downsampled)


def compute_storage_savings(
    original: pd.DataFrame,
    downsampled: pd.DataFrame
) -> float:
    """Compute storage savings as a percentage.

    Args:
        original: Original DataFrame.
        downsampled: Downsampled DataFrame.

    Returns:
        Percentage of storage saved (0-100).
    """
    if len(original) == 0:
        return 0.0
    return 100 * (1 - len(downsampled) / len(original))
