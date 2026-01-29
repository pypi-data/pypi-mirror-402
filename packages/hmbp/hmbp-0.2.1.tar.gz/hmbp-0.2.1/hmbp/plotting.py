"""
Simple plotting module with consistent styling.

Provides line plots, scatter plots, histograms, and data science
visualizations with a clean, publication-ready aesthetic.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap, LogNorm, SymLogNorm
from typing import Optional, Union, Sequence
from pathlib import Path

from .fonts import ensure_helvetica_available


# Style configuration - auto-install Helvetica-compatible font if needed

plt.rcParams['font.family'] = ensure_helvetica_available()

LABEL_SIZE = 14
TITLE_SIZE = 15
TICK_SIZE = 13
LEGEND_SIZE = 12
DPI = 400

CMAP = plt.cm.RdPu
CMAP_ALT = plt.cm.PiYG


def _apply_style(ax: plt.Axes) -> None:
    """Apply consistent tick styling to axes."""
    ax.tick_params(axis='both', labelsize=TICK_SIZE)


def _get_colors(cmap: Colormap) -> tuple:
    """Get fill and line colors from a colormap (same color, fill uses alpha)."""
    color = cmap(0.7)
    return color, color


def _ema(y: np.ndarray, weight: float) -> np.ndarray:
    """Exponential moving average smoothing."""
    smoothed = np.zeros_like(y, dtype=float)
    smoothed[0] = y[0]
    for i in range(1, len(y)):
        smoothed[i] = weight * smoothed[i - 1] + (1 - weight) * y[i]
    return smoothed


def line_plot(
    y: np.ndarray,
    x: Optional[np.ndarray] = None,
    label: str = "",
    cmap: Colormap = CMAP,
    fill: bool = True,
    smooth: float = 0,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a line plot with optional fill underneath.

    Parameters
    ----------
    y : array-like
        The y-values to plot.
    x : array-like, optional
        The x-values. If None, uses np.arange(len(y)).
    label : str, optional
        Label for the legend.
    cmap : Colormap, optional
        Colormap to derive colors from. Default is RdPu.
    fill : bool, optional
        Whether to fill under the line. Default is True.
    smooth : float, optional
        EMA smoothing weight (0-1). 0 means no smoothing, 0.9 is heavy smoothing.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    y = np.asarray(y)
    if x is None:
        x = np.arange(len(y))
    else:
        x = np.asarray(x)

    if smooth:
        y = _ema(y, smooth)

    fill_color, line_color = _get_colors(cmap)

    if fill:
        ax.fill_between(x, y, alpha=0.5, color=fill_color)

    ax.plot(x, y, color=line_color, linewidth=1, label=label if label else None)
    ax.grid(axis="y", alpha=0.5)
    ax.set_xlim(x.min(), x.max())

    _apply_style(ax)
    return ax


def multi_line_plot(
    ys: Sequence[np.ndarray],
    x: Optional[np.ndarray] = None,
    labels: Optional[Sequence[str]] = None,
    cmap: Colormap = CMAP,
    fill: bool = False,
    smooth: float = 0,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a plot with multiple lines.

    Parameters
    ----------
    ys : sequence of array-like
        List of y-value arrays to plot.
    x : array-like, optional
        The x-values (shared). If None, uses np.arange(len(ys[0])).
    labels : sequence of str, optional
        Labels for each line.
    cmap : Colormap, optional
        Colormap to derive colors from. Default is RdPu.
    fill : bool, optional
        Whether to fill under lines. Default is False.
    smooth : float, optional
        EMA smoothing weight (0-1). 0 means no smoothing, 0.9 is heavy smoothing.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    n = len(ys)
    if labels is None:
        labels = [None] * n

    if x is None:
        x = np.arange(len(ys[0]))
    else:
        x = np.asarray(x)

    # Use distinct categorical colors for comparison
    categorical_colors = [
        '#e41a1c',  # red
        '#377eb8',  # blue
        '#4daf4a',  # green
        '#984ea3',  # purple
        '#ff7f00',  # orange
        '#a65628',  # brown
        '#f781bf',  # pink
        '#999999',  # gray
    ]
    colors = [categorical_colors[i % len(categorical_colors)] for i in range(n)]

    for y, label, color in zip(ys, labels, colors):
        y = np.asarray(y)
        if smooth:
            y = _ema(y, smooth)
        if fill:
            ax.fill_between(x, y, alpha=0.3, color=color)
        ax.plot(x, y, color=color, linewidth=1.5, label=label)

    ax.grid(axis="y", alpha=0.5)
    ax.set_xlim(x.min(), x.max())

    _apply_style(ax)
    return ax


def scatter_plot(
    x: np.ndarray,
    y: np.ndarray,
    c: Optional[np.ndarray] = None,
    label: str = "",
    cmap: Colormap = CMAP,
    size: float = 20,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a scatter plot.

    Parameters
    ----------
    x : array-like
        The x-values.
    y : array-like
        The y-values.
    c : array-like, optional
        Values for color mapping. If None, uses solid color.
    label : str, optional
        Label for the legend.
    cmap : Colormap, optional
        Colormap for coloring points. Default is RdPu.
    size : float, optional
        Marker size. Default is 20.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    x = np.asarray(x)
    y = np.asarray(y)

    if c is not None:
        scatter = ax.scatter(x, y, c=c, cmap=cmap, s=size, label=label if label else None)
    else:
        _, color = _get_colors(cmap)
        scatter = ax.scatter(x, y, color=color, s=size, label=label if label else None)

    ax.grid(axis="both", alpha=0.5)
    _apply_style(ax)
    return ax


def histogram(
    data: np.ndarray,
    bins: int = 50,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a histogram with color-mapped bars.

    Parameters
    ----------
    data : array-like
        The data to bin.
    bins : int, optional
        Number of bins. Default is 50.
    cmap : Colormap, optional
        Colormap for coloring bars by count. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    data = np.asarray(data)
    counts, bin_edges, patches = ax.hist(data, bins=bins, edgecolor='black', linewidth=0.5)

    norm = plt.Normalize(counts.min(), counts.max())
    for count, patch in zip(counts, patches):
        patch.set_facecolor(cmap(norm(count)))

    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.5)
    _apply_style(ax)
    return ax


def histogram_overlay(
    datasets: Sequence[np.ndarray],
    labels: Optional[Sequence[str]] = None,
    bins: int = 50,
    alpha: float = 0.5,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create overlaid histograms for comparing distributions.

    Parameters
    ----------
    datasets : sequence of array-like
        List of datasets to plot.
    labels : sequence of str, optional
        Labels for each dataset.
    bins : int, optional
        Number of bins. Default is 50.
    alpha : float, optional
        Transparency for overlap visibility. Default is 0.5.
    cmap : Colormap, optional
        Colormap for coloring histograms. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    n = len(datasets)
    if labels is None:
        labels = [None] * n

    # Convert all datasets to arrays
    datasets = [np.asarray(d) for d in datasets]

    # Compute shared bin edges across all data
    all_data = np.concatenate(datasets)
    bin_edges = np.histogram_bin_edges(all_data, bins=bins)

    # Use distinct categorical colors (not from sequential colormap)
    categorical_colors = [
        '#e41a1c',  # red
        '#377eb8',  # blue
        '#4daf4a',  # green
        '#984ea3',  # purple
        '#ff7f00',  # orange
        '#a65628',  # brown
        '#f781bf',  # pink
        '#999999',  # gray
    ]
    colors = [categorical_colors[i % len(categorical_colors)] for i in range(n)]

    for data, label, color in zip(datasets, labels, colors):
        ax.hist(data, bins=bin_edges, alpha=alpha, color=color,
                label=label, edgecolor='black', linewidth=0.3)

    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.5)
    _apply_style(ax)
    return ax


def bar_plot(
    values: np.ndarray,
    labels: Sequence[str],
    horizontal: bool = False,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a bar plot with color-mapped bars.

    Parameters
    ----------
    values : array-like
        The bar heights/lengths.
    labels : sequence of str
        Labels for each bar.
    horizontal : bool, optional
        If True, create horizontal bars. Default is False.
    cmap : Colormap, optional
        Colormap for coloring bars. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    values = np.asarray(values)
    x = np.arange(len(values))

    norm = plt.Normalize(values.min(), values.max())
    colors = [cmap(norm(v)) for v in values]

    if horizontal:
        ax.barh(x, values, color=colors, edgecolor='black', linewidth=0.5)
        ax.set_yticks(x)
        ax.set_yticklabels(labels)
        ax.grid(axis="x", alpha=0.5)
    else:
        ax.bar(x, values, color=colors, edgecolor='black', linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(axis="y", alpha=0.5)

    ax.set_axisbelow(True)

    _apply_style(ax)
    return ax


def heatmap(
    data: np.ndarray,
    xticklabels: Optional[Sequence[str]] = None,
    yticklabels: Optional[Sequence[str]] = None,
    cmap: Colormap = CMAP,
    colorbar_label: str = "",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    log_scale: bool = False,
    center_zero: bool = False,
    annot: bool = False,
    fmt: str = ".2f",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a heatmap from a 2D array.

    Parameters
    ----------
    data : 2D array-like
        The data to display.
    xticklabels : sequence of str, optional
        Labels for x-axis ticks.
    yticklabels : sequence of str, optional
        Labels for y-axis ticks.
    cmap : Colormap, optional
        Colormap to use. Default is RdPu.
    colorbar_label : str, optional
        Label for the colorbar.
    vmin, vmax : float, optional
        Color scale limits.
    log_scale : bool, optional
        Use logarithmic color scale. Default is False.
    center_zero : bool, optional
        Center colormap at zero (uses diverging scale). Default is False.
    annot : bool, optional
        Annotate cells with values. Default is False.
    fmt : str, optional
        Format string for annotations. Default is ".2f".
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    data = np.asarray(data)

    if log_scale:
        vmin = vmin or max(data[data > 0].min(), 1e-6)
        vmax = vmax or data.max()
        norm = LogNorm(vmin=vmin, vmax=vmax)
        im = ax.imshow(data, cmap=cmap, norm=norm, interpolation='none')
    elif center_zero:
        abs_max = max(abs(data.min()), abs(data.max()))
        vmin = vmin or -abs_max
        vmax = vmax or abs_max
        norm = SymLogNorm(linthresh=abs_max * 1e-3, vmin=vmin, vmax=vmax)
        im = ax.imshow(data, cmap=CMAP_ALT, norm=norm, interpolation='none')
    else:
        im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='none')

    cbar = plt.colorbar(im, ax=ax)
    if colorbar_label:
        cbar.set_label(colorbar_label, fontsize=LABEL_SIZE)
    cbar.ax.tick_params(labelsize=TICK_SIZE)

    if xticklabels is not None:
        ax.set_xticks(np.arange(len(xticklabels)))
        ax.set_xticklabels(xticklabels)
    if yticklabels is not None:
        ax.set_yticks(np.arange(len(yticklabels)))
        ax.set_yticklabels(yticklabels)

    if annot:
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                text = f"{val:{fmt}}" if not np.isnan(val) else ""
                ax.text(j, i, text, ha='center', va='center',
                        fontsize=TICK_SIZE - 2, color='white' if val > data.max() * 0.5 else 'black')

    _apply_style(ax)
    return ax


def box_plot(
    data: Sequence[np.ndarray],
    labels: Sequence[str],
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a box plot for comparing distributions.

    Parameters
    ----------
    data : sequence of array-like
        List of arrays, one per box.
    labels : sequence of str
        Labels for each box.
    cmap : Colormap, optional
        Colormap for box colors. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    bp = ax.boxplot(data, labels=labels, patch_artist=True)

    n = len(data)
    # Use distinct categorical colors for comparison
    categorical_colors = [
        '#e41a1c',  # red
        '#377eb8',  # blue
        '#4daf4a',  # green
        '#984ea3',  # purple
        '#ff7f00',  # orange
        '#a65628',  # brown
        '#f781bf',  # pink
        '#999999',  # gray
    ]
    colors = [categorical_colors[i % len(categorical_colors)] for i in range(n)]

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    for median in bp['medians']:
        median.set_color('black')
        median.set_linewidth(1.5)

    ax.grid(axis="y", alpha=0.5)
    _apply_style(ax)
    return ax


def violin_plot(
    data: Sequence[np.ndarray],
    labels: Sequence[str],
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a violin plot for comparing distributions.

    Parameters
    ----------
    data : sequence of array-like
        List of arrays, one per violin.
    labels : sequence of str
        Labels for each violin.
    cmap : Colormap, optional
        Colormap for violin colors. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    parts = ax.violinplot(data, showmeans=True, showmedians=True)

    n = len(data)
    # Use distinct categorical colors for comparison
    categorical_colors = [
        '#e41a1c',  # red
        '#377eb8',  # blue
        '#4daf4a',  # green
        '#984ea3',  # purple
        '#ff7f00',  # orange
        '#a65628',  # brown
        '#f781bf',  # pink
        '#999999',  # gray
    ]
    colors = [categorical_colors[i % len(categorical_colors)] for i in range(n)]

    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    for partname in ('cbars', 'cmins', 'cmaxes', 'cmeans', 'cmedians'):
        if partname in parts:
            parts[partname].set_color('black')
            parts[partname].set_linewidth(1)

    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.grid(axis="y", alpha=0.5)

    _apply_style(ax)
    return ax


def line_plot_with_error(
    y: np.ndarray,
    yerr: np.ndarray,
    x: Optional[np.ndarray] = None,
    label: str = "",
    cmap: Colormap = CMAP,
    smooth: float = 0,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a line plot with shaded error region.

    Parameters
    ----------
    y : array-like
        The y-values (mean).
    yerr : array-like
        The error values (will show y ± yerr).
    x : array-like, optional
        The x-values. If None, uses np.arange(len(y)).
    label : str, optional
        Label for the legend.
    cmap : Colormap, optional
        Colormap to derive colors from. Default is RdPu.
    smooth : float, optional
        EMA smoothing weight (0-1). 0 means no smoothing, 0.9 is heavy smoothing.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    y = np.asarray(y)
    yerr = np.asarray(yerr)
    if x is None:
        x = np.arange(len(y))
    else:
        x = np.asarray(x)

    if smooth:
        y = _ema(y, smooth)
        yerr = _ema(yerr, smooth)

    fill_color, line_color = _get_colors(cmap)

    ax.fill_between(x, y - yerr, y + yerr, alpha=0.3, color=fill_color)
    ax.plot(x, y, color=line_color, linewidth=1.5, label=label if label else None)
    ax.grid(axis="y", alpha=0.5)
    ax.set_xlim(x.min(), x.max())

    _apply_style(ax)
    return ax


def confusion_matrix(
    cm: np.ndarray,
    class_names: Optional[Sequence[str]] = None,
    normalize: bool = False,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot a confusion matrix.

    Parameters
    ----------
    cm : 2D array-like
        Confusion matrix (n_classes x n_classes).
    class_names : sequence of str, optional
        Names of the classes.
    normalize : bool, optional
        Normalize by row (true labels). Default is False.
    cmap : Colormap, optional
        Colormap to use. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    cm = np.asarray(cm)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)

    im = ax.imshow(cm, cmap=cmap, interpolation='none')
    cbar = plt.colorbar(im, ax=ax)
    cbar.ax.tick_params(labelsize=TICK_SIZE)

    n_classes = cm.shape[0]
    if class_names is None:
        class_names = [str(i) for i in range(n_classes)]

    ax.set_xticks(np.arange(n_classes))
    ax.set_yticks(np.arange(n_classes))
    ax.set_xticklabels(class_names)
    ax.set_yticklabels(class_names)

    # Annotate cells
    thresh = cm.max() / 2
    fmt = ".2f" if normalize else "d"
    for i in range(n_classes):
        for j in range(n_classes):
            val = cm[i, j]
            text = f"{val:{fmt}}" if normalize else f"{int(val)}"
            ax.text(j, i, text, ha='center', va='center',
                    fontsize=TICK_SIZE, color='white' if val > thresh else 'black')

    ax.set_xlabel("Predicted", fontsize=LABEL_SIZE)
    ax.set_ylabel("True", fontsize=LABEL_SIZE)

    _apply_style(ax)
    return ax


def roc_curve(
    fpr: np.ndarray,
    tpr: np.ndarray,
    auc: Optional[float] = None,
    label: str = "",
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot an ROC curve.

    Parameters
    ----------
    fpr : array-like
        False positive rates.
    tpr : array-like
        True positive rates.
    auc : float, optional
        Area under curve (will be shown in legend if provided).
    label : str, optional
        Label for the curve.
    cmap : Colormap, optional
        Colormap to derive colors from. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    _, line_color = _get_colors(cmap)

    if auc is not None:
        label = f"{label} (AUC = {auc:.3f})" if label else f"AUC = {auc:.3f}"

    ax.plot(fpr, tpr, color=line_color, linewidth=1.5, label=label if label else None)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=0.8, alpha=0.5)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("False Positive Rate", fontsize=LABEL_SIZE)
    ax.set_ylabel("True Positive Rate", fontsize=LABEL_SIZE)
    ax.grid(alpha=0.5)

    _apply_style(ax)
    return ax


def precision_recall_curve(
    precision: np.ndarray,
    recall: np.ndarray,
    ap: Optional[float] = None,
    label: str = "",
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot a precision-recall curve.

    Parameters
    ----------
    precision : array-like
        Precision values.
    recall : array-like
        Recall values.
    ap : float, optional
        Average precision (will be shown in legend if provided).
    label : str, optional
        Label for the curve.
    cmap : Colormap, optional
        Colormap to derive colors from. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    _, line_color = _get_colors(cmap)

    if ap is not None:
        label = f"{label} (AP = {ap:.3f})" if label else f"AP = {ap:.3f}"

    ax.plot(recall, precision, color=line_color, linewidth=1.5, label=label if label else None)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Recall", fontsize=LABEL_SIZE)
    ax.set_ylabel("Precision", fontsize=LABEL_SIZE)
    ax.grid(alpha=0.5)

    _apply_style(ax)
    return ax


def residual_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot residuals vs predicted values for regression diagnostics.

    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
    cmap : Colormap, optional
        Colormap for scatter points. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    residuals = y_true - y_pred

    _, color = _get_colors(cmap)
    ax.scatter(y_pred, residuals, color=color, s=20, alpha=0.6)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)

    ax.set_xlabel("Predicted", fontsize=LABEL_SIZE)
    ax.set_ylabel("Residual", fontsize=LABEL_SIZE)
    ax.grid(alpha=0.5)

    _apply_style(ax)
    return ax


def learning_curve(
    train_scores: np.ndarray,
    val_scores: np.ndarray,
    train_sizes: Optional[np.ndarray] = None,
    metric_name: str = "Score",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot a learning curve showing training and validation performance.

    Parameters
    ----------
    train_scores : array-like
        Training scores (can be 1D or 2D with shape [n_sizes, n_folds]).
    val_scores : array-like
        Validation scores (same shape as train_scores).
    train_sizes : array-like, optional
        Training set sizes. If None, uses indices.
    metric_name : str, optional
        Name of the metric for y-axis label. Default is "Score".
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    train_scores = np.asarray(train_scores)
    val_scores = np.asarray(val_scores)

    if train_scores.ndim == 1:
        train_mean, train_std = train_scores, np.zeros_like(train_scores)
        val_mean, val_std = val_scores, np.zeros_like(val_scores)
    else:
        train_mean = train_scores.mean(axis=1)
        train_std = train_scores.std(axis=1)
        val_mean = val_scores.mean(axis=1)
        val_std = val_scores.std(axis=1)

    if train_sizes is None:
        train_sizes = np.arange(len(train_mean))

    line_plot_with_error(train_mean, train_std, train_sizes, label="Train", cmap=CMAP, ax=ax)
    line_plot_with_error(val_mean, val_std, train_sizes, label="Validation", cmap=CMAP_ALT, ax=ax)

    ax.set_xlabel("Training Size", fontsize=LABEL_SIZE)
    ax.set_ylabel(metric_name, fontsize=LABEL_SIZE)

    return ax


def metric_comparison(
    metrics: dict[str, float],
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a horizontal bar plot comparing metrics.

    Parameters
    ----------
    metrics : dict
        Dictionary mapping metric names to values.
    cmap : Colormap, optional
        Colormap for bar colors. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    labels = list(metrics.keys())
    values = np.array(list(metrics.values()))

    return bar_plot(values, labels, horizontal=True, cmap=cmap, ax=ax)


def volcano_plot(
    log_fc: np.ndarray,
    pvalues: np.ndarray,
    fc_thresh: float = 1.0,
    p_thresh: float = 0.05,
    labels: Optional[Sequence[str]] = None,
    highlight_top: int = 0,
    cmap: Colormap = CMAP,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Create a volcano plot for differential expression/analysis.

    Parameters
    ----------
    log_fc : array-like
        Log2 fold changes.
    pvalues : array-like
        P-values (will be -log10 transformed).
    fc_thresh : float, optional
        Fold change threshold for significance. Default is 1.0.
    p_thresh : float, optional
        P-value threshold for significance. Default is 0.05.
    labels : sequence of str, optional
        Labels for each point (for annotation of top hits).
    highlight_top : int, optional
        Number of top significant points to label. Default is 0.
    cmap : Colormap, optional
        Colormap for significant points. Default is RdPu.
    ax : Axes, optional
        Axes to plot on. If None, uses current axes.

    Returns
    -------
    ax : Axes
        The matplotlib axes.
    """
    if ax is None:
        ax = plt.gca()

    log_fc = np.asarray(log_fc)
    pvalues = np.asarray(pvalues)
    neg_log_p = -np.log10(pvalues + 1e-300)  # avoid log(0)

    # Classify points
    sig_up = (log_fc >= fc_thresh) & (pvalues <= p_thresh)
    sig_down = (log_fc <= -fc_thresh) & (pvalues <= p_thresh)
    not_sig = ~(sig_up | sig_down)

    # Plot non-significant points
    ax.scatter(log_fc[not_sig], neg_log_p[not_sig],
               c='lightgray', s=15, alpha=0.6, label='Not significant')

    # Plot significant points
    _, up_color = _get_colors(cmap)
    _, down_color = _get_colors(CMAP_ALT)

    ax.scatter(log_fc[sig_up], neg_log_p[sig_up],
               c=[up_color], s=20, alpha=0.8, label=f'Up (FC ≥ {fc_thresh})')
    ax.scatter(log_fc[sig_down], neg_log_p[sig_down],
               c=[down_color], s=20, alpha=0.8, label=f'Down (FC ≤ -{fc_thresh})')

    # Add threshold lines
    ax.axhline(-np.log10(p_thresh), color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axvline(fc_thresh, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axvline(-fc_thresh, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Label top hits
    if highlight_top > 0 and labels is not None:
        sig_mask = sig_up | sig_down
        sig_indices = np.where(sig_mask)[0]
        if len(sig_indices) > 0:
            # Sort by significance (p-value)
            sorted_idx = sig_indices[np.argsort(pvalues[sig_indices])][:highlight_top]
            for idx in sorted_idx:
                ax.annotate(labels[idx], (log_fc[idx], neg_log_p[idx]),
                           fontsize=9, alpha=0.8,
                           xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel("log₂ Fold Change", fontsize=LABEL_SIZE)
    ax.set_ylabel("-log₁₀ P-value", fontsize=LABEL_SIZE)
    ax.grid(alpha=0.3)

    _apply_style(ax)
    return ax


def set_labels(
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    ax: Optional[plt.Axes] = None,
) -> None:
    """Set title and axis labels with consistent styling."""
    if ax is None:
        ax = plt.gca()

    if title:
        ax.set_title(title, fontsize=TITLE_SIZE)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=LABEL_SIZE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)


def save(
    path: Union[str, Path],
    fig: Optional[plt.Figure] = None,
    close: bool = True,
) -> None:
    """
    Save the figure with consistent styling.

    Automatically adds legend if labels are present.

    Parameters
    ----------
    path : str or Path
        Output file path.
    fig : Figure, optional
        Figure to save. If None, uses current figure.
    close : bool, optional
        Whether to close the figure after saving. Default is True.
    """
    if fig is None:
        fig = plt.gcf()

    # Add legend if any labels exist
    for ax in fig.axes:
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(
                frameon=True,
                fancybox=False,
                shadow=True,
                fontsize=LEGEND_SIZE,
            )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(path, dpi=DPI, bbox_inches="tight")

    if close:
        plt.close(fig)


def new_figure(figsize: tuple = (8, 6)) -> tuple[plt.Figure, plt.Axes]:
    """Create a new figure with a single axes."""
    return plt.subplots(figsize=figsize)


# =============================================================================
# Quick plot API - single-call convenience functions for agents
# =============================================================================


def _quick(plot_fn, args, kwargs, title, xlabel, ylabel, path):
    """Helper for quick_* functions."""
    fig, ax = new_figure()
    plot_fn(*args, ax=ax, **kwargs)
    set_labels(title, xlabel, ylabel, ax)
    if path:
        save(path, fig)
    return ax


def quick_line(y, x=None, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a line plot in one call. Saves to path if provided."""
    return _quick(line_plot, (y, x), kw, title, xlabel, ylabel, path)


def quick_lines(ys, x=None, labels=None, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a multi-line plot in one call. Saves to path if provided."""
    return _quick(multi_line_plot, (ys, x, labels), kw, title, xlabel, ylabel, path)


def quick_scatter(x, y, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a scatter plot in one call. Saves to path if provided."""
    return _quick(scatter_plot, (x, y), kw, title, xlabel, ylabel, path)


def quick_histogram(data, title="", xlabel="", ylabel="Count", path=None, **kw):
    """Create a histogram in one call. Saves to path if provided."""
    return _quick(histogram, (data,), kw, title, xlabel, ylabel, path)


def quick_histogram_overlay(datasets, labels=None, title="", xlabel="", ylabel="Count", path=None, **kw):
    """Create overlaid histograms in one call. Saves to path if provided."""
    return _quick(histogram_overlay, (datasets, labels), kw, title, xlabel, ylabel, path)


def quick_bar(values, labels, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a bar plot in one call. Saves to path if provided."""
    return _quick(bar_plot, (values, labels), kw, title, xlabel, ylabel, path)


def quick_heatmap(data, title="", xlabel="", ylabel="", path=None, **kw):
    """Create a heatmap in one call. Saves to path if provided."""
    return _quick(heatmap, (data,), kw, title, xlabel, ylabel, path)


def quick_confusion_matrix(cm, class_names=None, title="Confusion Matrix", path=None, **kw):
    """Create a confusion matrix in one call. Saves to path if provided."""
    return _quick(confusion_matrix, (cm, class_names), kw, title, "", "", path)


def quick_roc(fpr, tpr, auc=None, title="ROC Curve", path=None, **kw):
    """Create an ROC curve in one call. Saves to path if provided."""
    return _quick(roc_curve, (fpr, tpr, auc), kw, title, "", "", path)


def quick_volcano(log_fc, pvalues, title="Volcano Plot", path=None, **kw):
    """Create a volcano plot in one call. Saves to path if provided."""
    return _quick(volcano_plot, (log_fc, pvalues), kw, title, "", "", path)
