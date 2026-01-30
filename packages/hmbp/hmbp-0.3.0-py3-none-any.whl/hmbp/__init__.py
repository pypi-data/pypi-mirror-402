"""
hmbp - Simple matplotlib plotting with consistent, publication-ready styling.

Provides line plots, scatter plots, histograms, and data science
visualizations with a clean aesthetic.
"""

import warnings

from hmbp.plotting import (
    # Style constants
    LABEL_SIZE,
    TITLE_SIZE,
    TICK_SIZE,
    LEGEND_SIZE,
    DPI,
    CMAP,
    CMAP_ALT,
    # Core plot functions
    line_plot,
    multi_line_plot,
    scatter_plot,
    histogram,
    histogram_overlay,
    bar_plot,
    heatmap,
    box_plot,
    violin_plot,
    line_plot_with_error,
    # Data science plots
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    residual_plot,
    learning_curve,
    metric_comparison,
    volcano_plot,
    # Helpers
    set_labels,
    save,
    new_figure,
)

# Quick API module
from hmbp import quick

# PGFPlots module (import as hmbp.pgfplots)
from hmbp import pgfplots

try:
    from hmbp._version import version as __version__
except ImportError:
    __version__ = "0.0.0.dev0"


# Deprecated aliases for quick_* functions
def quick_line(*args, **kwargs):
    """Deprecated: use hmbp.quick.line() instead."""
    warnings.warn("hmbp.quick_line is deprecated, use hmbp.quick.line", DeprecationWarning, stacklevel=2)
    return quick.line(*args, **kwargs)


def quick_lines(*args, **kwargs):
    """Deprecated: use hmbp.quick.lines() instead."""
    warnings.warn("hmbp.quick_lines is deprecated, use hmbp.quick.lines", DeprecationWarning, stacklevel=2)
    return quick.lines(*args, **kwargs)


def quick_scatter(*args, **kwargs):
    """Deprecated: use hmbp.quick.scatter() instead."""
    warnings.warn("hmbp.quick_scatter is deprecated, use hmbp.quick.scatter", DeprecationWarning, stacklevel=2)
    return quick.scatter(*args, **kwargs)


def quick_histogram(*args, **kwargs):
    """Deprecated: use hmbp.quick.histogram() instead."""
    warnings.warn("hmbp.quick_histogram is deprecated, use hmbp.quick.histogram", DeprecationWarning, stacklevel=2)
    return quick.histogram(*args, **kwargs)


def quick_histogram_overlay(*args, **kwargs):
    """Deprecated: use hmbp.quick.histogram_overlay() instead."""
    warnings.warn("hmbp.quick_histogram_overlay is deprecated, use hmbp.quick.histogram_overlay", DeprecationWarning, stacklevel=2)
    return quick.histogram_overlay(*args, **kwargs)


def quick_bar(*args, **kwargs):
    """Deprecated: use hmbp.quick.bar() instead."""
    warnings.warn("hmbp.quick_bar is deprecated, use hmbp.quick.bar", DeprecationWarning, stacklevel=2)
    return quick.bar(*args, **kwargs)


def quick_heatmap(*args, **kwargs):
    """Deprecated: use hmbp.quick.heatmap() instead."""
    warnings.warn("hmbp.quick_heatmap is deprecated, use hmbp.quick.heatmap", DeprecationWarning, stacklevel=2)
    return quick.heatmap(*args, **kwargs)


def quick_confusion_matrix(*args, **kwargs):
    """Deprecated: use hmbp.quick.confusion_matrix() instead."""
    warnings.warn("hmbp.quick_confusion_matrix is deprecated, use hmbp.quick.confusion_matrix", DeprecationWarning, stacklevel=2)
    return quick.confusion_matrix(*args, **kwargs)


def quick_roc(*args, **kwargs):
    """Deprecated: use hmbp.quick.roc() instead."""
    warnings.warn("hmbp.quick_roc is deprecated, use hmbp.quick.roc", DeprecationWarning, stacklevel=2)
    return quick.roc(*args, **kwargs)


def quick_volcano(*args, **kwargs):
    """Deprecated: use hmbp.quick.volcano() instead."""
    warnings.warn("hmbp.quick_volcano is deprecated, use hmbp.quick.volcano", DeprecationWarning, stacklevel=2)
    return quick.volcano(*args, **kwargs)


def quick_violin(*args, **kwargs):
    """Deprecated: use hmbp.quick.violin() instead."""
    warnings.warn("hmbp.quick_violin is deprecated, use hmbp.quick.violin", DeprecationWarning, stacklevel=2)
    return quick.violin(*args, **kwargs)


__all__ = [
    # Style constants
    "LABEL_SIZE",
    "TITLE_SIZE",
    "TICK_SIZE",
    "LEGEND_SIZE",
    "DPI",
    "CMAP",
    "CMAP_ALT",
    # Core plot functions
    "line_plot",
    "multi_line_plot",
    "scatter_plot",
    "histogram",
    "histogram_overlay",
    "bar_plot",
    "heatmap",
    "box_plot",
    "violin_plot",
    "line_plot_with_error",
    # Data science plots
    "confusion_matrix",
    "roc_curve",
    "precision_recall_curve",
    "residual_plot",
    "learning_curve",
    "metric_comparison",
    "volcano_plot",
    # Helpers
    "set_labels",
    "save",
    "new_figure",
    # Quick API module
    "quick",
    # Deprecated quick_* aliases (kept for discoverability)
    "quick_line",
    "quick_lines",
    "quick_scatter",
    "quick_histogram",
    "quick_histogram_overlay",
    "quick_bar",
    "quick_heatmap",
    "quick_confusion_matrix",
    "quick_roc",
    "quick_volcano",
    "quick_violin",
    # PGFPlots module
    "pgfplots",
]
