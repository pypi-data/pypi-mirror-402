"""Fidelity testing and comparison tools for downsampling.

This module provides tools for evaluating the visual and statistical fidelity
of downsampled time series data compared to the original.
"""

from downsampler.fidelity.metrics import FidelityMetrics, compute_metrics
from downsampler.fidelity.comparison import FidelityComparison, ComparisonResult
from downsampler.fidelity.visualization import (
    plot_comparison,
    plot_method_comparison,
    MarimoHelper,
)

__all__ = [
    "FidelityMetrics",
    "compute_metrics",
    "FidelityComparison",
    "ComparisonResult",
    "plot_comparison",
    "plot_method_comparison",
    "MarimoHelper",
]
