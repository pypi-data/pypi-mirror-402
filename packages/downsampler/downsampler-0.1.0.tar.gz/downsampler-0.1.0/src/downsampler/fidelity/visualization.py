"""Visualization helpers for fidelity comparison.

Provides functions for plotting original vs downsampled data and
comparing different methods.
"""

from typing import Any
import pandas as pd
import numpy as np

from downsampler.fidelity.comparison import ComparisonResult


def plot_comparison(
    original: pd.DataFrame,
    downsampled: pd.DataFrame,
    column: str,
    backend: str = "matplotlib",
    title: str | None = None,
    **kwargs
) -> Any:
    """Plot original and downsampled data for visual comparison.

    Args:
        original: Original DataFrame.
        downsampled: Downsampled DataFrame.
        column: Column to plot.
        backend: Plotting backend ('matplotlib' or 'altair').
        title: Optional plot title.
        **kwargs: Additional arguments passed to the plotting function.

    Returns:
        Plot object (matplotlib Figure or Altair Chart).

    Example:
        >>> fig = plot_comparison(original_df, downsampled_df, 'signal')
        >>> fig.savefig('comparison.png')
    """
    if backend == "matplotlib":
        return _plot_matplotlib(original, downsampled, column, title, **kwargs)
    elif backend == "altair":
        return _plot_altair(original, downsampled, column, title, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_matplotlib(
    original: pd.DataFrame,
    downsampled: pd.DataFrame,
    column: str,
    title: str | None = None,
    figsize: tuple = (12, 6),
    **kwargs
) -> Any:
    """Create matplotlib comparison plot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for this function. Install with: pip install matplotlib")

    fig, ax = plt.subplots(figsize=figsize)

    # Plot original
    ax.plot(
        original.index,
        original[column],
        label='Original',
        alpha=0.7,
        linewidth=0.5,
        color='blue'
    )

    # Plot downsampled
    ax.plot(
        downsampled.index,
        downsampled[column],
        label='Downsampled',
        alpha=0.9,
        linewidth=1.5,
        color='red',
        marker='.',
        markersize=3
    )

    ax.set_xlabel('Time')
    ax.set_ylabel(column)
    ax.legend()

    if title:
        ax.set_title(title)
    else:
        reduction = len(original) / len(downsampled) if len(downsampled) > 0 else float('inf')
        ax.set_title(f'Downsampling Comparison ({reduction:.1f}x reduction)')

    fig.tight_layout()
    return fig


def _plot_altair(
    original: pd.DataFrame,
    downsampled: pd.DataFrame,
    column: str,
    title: str | None = None,
    width: int = 800,
    height: int = 400,
    **kwargs
) -> Any:
    """Create Altair comparison plot."""
    try:
        import altair as alt
    except ImportError:
        raise ImportError("altair is required for this function. Install with: pip install altair")

    # Prepare data
    orig_data = original[[column]].reset_index()
    orig_data.columns = ['time', column]
    orig_data['source'] = 'Original'

    ds_data = downsampled[[column]].reset_index()
    ds_data.columns = ['time', column]
    ds_data['source'] = 'Downsampled'

    combined = pd.concat([orig_data, ds_data])

    chart = alt.Chart(combined).mark_line().encode(
        x='time:T',
        y=f'{column}:Q',
        color='source:N',
        strokeWidth=alt.condition(
            alt.datum.source == 'Downsampled',
            alt.value(2),
            alt.value(0.5)
        ),
        opacity=alt.condition(
            alt.datum.source == 'Downsampled',
            alt.value(1),
            alt.value(0.7)
        )
    ).properties(
        width=width,
        height=height,
        title=title or 'Downsampling Comparison'
    )

    return chart


def plot_method_comparison(
    results: list[ComparisonResult],
    metric: str = "rmse",
    backend: str = "matplotlib",
    **kwargs
) -> Any:
    """Plot comparison of different methods by a specific metric.

    Args:
        results: List of ComparisonResult objects.
        metric: Metric to compare ('rmse', 'mae', 'pearson_r', etc.).
        backend: Plotting backend ('matplotlib' or 'altair').
        **kwargs: Additional arguments passed to the plotting function.

    Returns:
        Plot object.
    """
    if backend == "matplotlib":
        return _plot_method_comparison_matplotlib(results, metric, **kwargs)
    elif backend == "altair":
        return _plot_method_comparison_altair(results, metric, **kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _plot_method_comparison_matplotlib(
    results: list[ComparisonResult],
    metric: str = "rmse",
    figsize: tuple = (10, 6),
    **kwargs
) -> Any:
    """Create matplotlib method comparison bar chart."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required")

    # Extract data
    methods = [r.method.value for r in results]
    values = [getattr(r.metrics, metric) for r in results]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(methods, values, color='steelblue')

    # Highlight best value
    if metric in ['rmse', 'mae', 'max_error', 'peak_error']:
        best_idx = np.argmin(values)
    else:
        best_idx = np.argmax(values)

    bars[best_idx].set_color('green')

    ax.set_xlabel('Method')
    ax.set_ylabel(metric.upper())
    ax.set_title(f'Method Comparison by {metric.upper()}')

    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()

    return fig


def _plot_method_comparison_altair(
    results: list[ComparisonResult],
    metric: str = "rmse",
    width: int = 400,
    height: int = 300,
    **kwargs
) -> Any:
    """Create Altair method comparison bar chart."""
    try:
        import altair as alt
    except ImportError:
        raise ImportError("altair is required")

    data = pd.DataFrame([
        {'method': r.method.value, metric: getattr(r.metrics, metric)}
        for r in results
    ])

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('method:N', sort='-y'),
        y=f'{metric}:Q',
        color=alt.Color('method:N', legend=None)
    ).properties(
        width=width,
        height=height,
        title=f'Method Comparison by {metric.upper()}'
    )

    return chart


class MarimoHelper:
    """Helper class for creating interactive Marimo notebook comparisons.

    Example usage in a Marimo notebook:
        >>> from downsampler.fidelity import MarimoHelper
        >>> helper = MarimoHelper()
        >>> ui, output = helper.interactive_comparison(
        ...     original_df, 'signal',
        ...     cadences=['1min', '5min', '10min'],
        ...     methods=['mean', 'lttb']
        ... )
        >>> # Display ui and output in separate cells
    """

    @staticmethod
    def interactive_comparison(
        original: pd.DataFrame,
        column: str,
        cadences: list[str],
        methods: list[str] | None = None
    ) -> tuple[Any, Any]:
        """Create interactive comparison UI for Marimo notebooks.

        Args:
            original: Original DataFrame.
            column: Column to compare.
            cadences: List of cadence options.
            methods: List of method options. If None, uses all methods.

        Returns:
            Tuple of (ui_element, output_function) for Marimo.
        """
        try:
            import marimo as mo
        except ImportError:
            raise ImportError(
                "marimo is required for interactive comparisons. "
                "Install with: pip install marimo"
            )

        from downsampler.config import AggregationMethod
        from downsampler.core import downsample
        from downsampler.fidelity.metrics import compute_metrics

        if methods is None:
            methods = [m.value for m in AggregationMethod]

        # Create UI elements
        cadence_select = mo.ui.dropdown(
            options=cadences,
            value=cadences[0],
            label="Target Cadence"
        )

        method_select = mo.ui.dropdown(
            options=methods,
            value=methods[0],
            label="Method"
        )

        ui = mo.vstack([cadence_select, method_select])

        def compute_output():
            cadence = cadence_select.value
            method = AggregationMethod(method_select.value)

            from downsampler.config import DownsampleConfig

            config = DownsampleConfig(
                method=method,
                lttb_target_column=column if method == AggregationMethod.LTTB else None
            )

            downsampled = downsample(original, cadence, config)
            metrics = compute_metrics(original, downsampled, column)

            # Create plot
            fig = plot_comparison(original, downsampled, column, backend="matplotlib")

            return mo.vstack([
                mo.md(f"### Results for {method.value} at {cadence}"),
                mo.md(f"**Reduction:** {len(original)/len(downsampled):.1f}x"),
                mo.md(f"**RMSE:** {metrics.rmse:.6f}"),
                mo.md(f"**Correlation:** {metrics.pearson_r:.4f}"),
                fig
            ])

        return ui, compute_output

    @staticmethod
    def comparison_table(
        original: pd.DataFrame,
        column: str,
        cadences: list[str],
        methods: list[str] | None = None
    ) -> pd.DataFrame:
        """Generate a comparison table for multiple cadences and methods.

        Args:
            original: Original DataFrame.
            column: Column to compare.
            cadences: List of cadences to compare.
            methods: List of methods. If None, uses all methods.

        Returns:
            DataFrame with comparison metrics.
        """
        from downsampler.fidelity.comparison import FidelityComparison
        from downsampler.config import AggregationMethod

        if methods is None:
            method_enums = list(AggregationMethod)
        else:
            method_enums = [AggregationMethod(m) for m in methods]

        comp = FidelityComparison(original, column)
        results = comp.compare_grid(cadences, method_enums)

        return comp.summary_table(results)
