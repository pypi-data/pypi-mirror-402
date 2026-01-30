"""
Quick plot API - single-call convenience functions for agents.

Usage:
    import hmbp
    hmbp.quick.line(y, title="My Plot", path="output.png")
"""

__all__ = [
    "line",
    "lines",
    "scatter",
    "histogram",
    "histogram_overlay",
    "bar",
    "heatmap",
    "confusion_matrix",
    "roc",
    "volcano",
    "violin",
]

from hmbp.plotting import (
    new_figure,
    set_labels,
    save,
    line_plot,
    multi_line_plot,
    scatter_plot,
    histogram as histogram_plot,
    histogram_overlay as histogram_overlay_plot,
    bar_plot,
    heatmap as heatmap_plot,
    confusion_matrix as confusion_matrix_plot,
    roc_curve,
    volcano_plot,
    violin_plot,
)


def _quick(plot_fn, args, kwargs, title, xlabel, ylabel, path):
    """Helper for quick plot functions."""
    fig, ax = new_figure()
    plot_fn(*args, ax=ax, **kwargs)
    set_labels(title, xlabel, ylabel, ax)
    if path:
        save(path, fig)
    return ax


def line(y, x=None, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a line plot in one call. Saves to path if provided."""
    return _quick(line_plot, (y, x), kw, title, xlabel, ylabel, path)


def lines(ys, x=None, labels=None, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a multi-line plot in one call. Saves to path if provided."""
    return _quick(multi_line_plot, (ys, x, labels), kw, title, xlabel, ylabel, path)


def scatter(x, y, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a scatter plot in one call. Saves to path if provided."""
    return _quick(scatter_plot, (x, y), kw, title, xlabel, ylabel, path)


def histogram(data, title="", xlabel="", ylabel="Count", path=None, **kw):
    """Create a histogram in one call. Saves to path if provided."""
    return _quick(histogram_plot, (data,), kw, title, xlabel, ylabel, path)


def histogram_overlay(datasets, labels=None, title="", xlabel="", ylabel="Count", path=None, **kw):
    """Create overlaid histograms in one call. Saves to path if provided."""
    return _quick(histogram_overlay_plot, (datasets, labels), kw, title, xlabel, ylabel, path)


def bar(values, labels, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a bar plot in one call. Saves to path if provided."""
    return _quick(bar_plot, (values, labels), kw, title, xlabel, ylabel, path)


def heatmap(data, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a heatmap in one call. Saves to path if provided."""
    return _quick(heatmap_plot, (data,), kw, title, xlabel, ylabel, path)


def confusion_matrix(cm, class_names=None, title="Confusion Matrix", path=None, **kw):
    """Create a confusion matrix in one call. Saves to path if provided."""
    return _quick(confusion_matrix_plot, (cm, class_names), kw, title, "", "", path)


def roc(fpr, tpr, auc=None, title="ROC Curve", path=None, **kw):
    """Create an ROC curve in one call. Saves to path if provided."""
    return _quick(roc_curve, (fpr, tpr, auc), kw, title, "", "", path)


def volcano(log_fc, pvalues, title="Volcano Plot", path=None, **kw):
    """Create a volcano plot in one call. Saves to path if provided."""
    return _quick(volcano_plot, (log_fc, pvalues), kw, title, "", "", path)


def violin(data, labels, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a violin plot in one call. Saves to path if provided."""
    return _quick(violin_plot, (data, labels), kw, title, xlabel, ylabel, path)
