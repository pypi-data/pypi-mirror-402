"""Configuration dataclasses and enums for downsampler."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Union

import pandas as pd


class AggregationMethod(str, Enum):
    """Aggregation methods for downsampling."""
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    LTTB = "lttb"


class EdgeHandling(str, Enum):
    """Strategies for handling edge points in downsampled data."""
    DISCARD = "discard"     # Remove edge points
    FLAG = "flag"           # Keep edges, add '_is_edge' column
    KEEP = "keep"           # Keep as-is


class GapHandling(str, Enum):
    """Strategies for handling gaps in time series data."""
    SEGMENT = "segment"         # Split at gaps, process independently
    INTERPOLATE = "interpolate" # Fill gaps first
    IGNORE = "ignore"           # Treat as continuous


@dataclass
class DownsampleConfig:
    """Configuration for downsampling operations.

    Attributes:
        method: The aggregation method to use for downsampling.
        lttb_target_column: For LTTB, the column to optimize visual fidelity for.
        include_columns: Columns to include in the output (empty means all).
        exclude_columns: Columns to exclude from the output.
        gap_handling: Strategy for handling gaps in the data.
        gap_threshold: Minimum duration to consider as a gap.
            "auto" means 2x the target cadence.
        edge_handling: Strategy for handling edge points.
        edge_window: Number of points at each edge to consider as edge points.
        min_points_per_segment: Minimum points required in a segment for processing.
    """
    method: AggregationMethod = AggregationMethod.MEAN
    lttb_target_column: str | None = None
    include_columns: list[str] = field(default_factory=list)
    exclude_columns: list[str] = field(default_factory=list)
    gap_handling: GapHandling = GapHandling.SEGMENT
    gap_threshold: Union[str, pd.Timedelta] = "auto"
    edge_handling: EdgeHandling = EdgeHandling.FLAG
    edge_window: int = 2
    min_points_per_segment: int = 3

    def get_gap_threshold(self, target_cadence: pd.Timedelta) -> pd.Timedelta:
        """Get the gap threshold, computing auto value if needed.

        Args:
            target_cadence: The target cadence for downsampling.

        Returns:
            The gap threshold as a Timedelta.
        """
        if self.gap_threshold == "auto":
            return 2 * target_cadence
        elif isinstance(self.gap_threshold, str):
            return pd.to_timedelta(self.gap_threshold)
        return self.gap_threshold
