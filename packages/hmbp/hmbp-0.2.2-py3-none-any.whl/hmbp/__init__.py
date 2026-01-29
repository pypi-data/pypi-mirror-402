"""
hmbp - Simple matplotlib plotting with consistent, publication-ready styling.

Provides line plots, scatter plots, histograms, and data science
visualizations with a clean aesthetic.
"""

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
    # Quick API
    quick_line,
    quick_lines,
    quick_scatter,
    quick_histogram,
    quick_histogram_overlay,
    quick_bar,
    quick_heatmap,
    quick_confusion_matrix,
    quick_roc,
    quick_volcano,
)

# PGFPlots module (import as hmbp.pgfplots)
from hmbp import pgfplots

try:
    from hmbp._version import version as __version__
except ImportError:
    __version__ = "0.0.0.dev0"
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
    # Quick API
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
    # PGFPlots module
    "pgfplots",
]
