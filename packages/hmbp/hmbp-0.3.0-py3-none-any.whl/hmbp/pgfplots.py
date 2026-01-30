"""
PGFPlots figure generation module.

Generates publication-ready LaTeX figures using PGFPlots,
with an API mirroring the matplotlib module.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union, Sequence
import numpy as np


# =============================================================================
# Document Template
# =============================================================================

PREAMBLE = r"""\documentclass[border=0.2cm]{standalone}

\usepackage{pgfplots}
\usepackage[scaled]{helvet}
\renewcommand\familydefault{\sfdefault}
\usepackage[T1]{fontenc}
\pgfplotsset{compat=1.18}

\begin{document}
"""

POSTAMBLE = r"""
\end{document}
"""

# =============================================================================
# Colors (matching reference style)
# =============================================================================

# Named colors from reference files
COLORS = {
    'red': 'F9665E',
    'blue': '799FCB',
    'gold': 'F1A226',
    'purple': 'A44694',
}

# Categorical colors (matching matplotlib module)
CATEGORICAL_COLORS = [
    'E41A1C',  # red
    '377EB8',  # blue
    '4DAF4A',  # green
    '984EA3',  # purple
    'FF7F00',  # orange
    'A65628',  # brown
    'F781BF',  # pink
    '999999',  # gray
]


def _color_definitions() -> str:
    """Generate LaTeX color definition commands."""
    lines = []
    for name, hex_val in COLORS.items():
        lines.append(rf"\definecolor{{{name}1}}{{HTML}}{{{hex_val}}}")
    for i, hex_val in enumerate(CATEGORICAL_COLORS):
        lines.append(rf"\definecolor{{cat{i}}}{{HTML}}{{{hex_val}}}")
    return '\n'.join(lines)


def _get_color(color: Optional[Union[str, int]], index: int = 0) -> str:
    """Get a color name for use in PGFPlots commands."""
    if color is None:
        return f"cat{index % len(CATEGORICAL_COLORS)}"
    if isinstance(color, int):
        return f"cat{color % len(CATEGORICAL_COLORS)}"
    if color in COLORS:
        return f"{color}1"
    # Assume it's a raw color specification
    return color


# =============================================================================
# Figure State
# =============================================================================

class _FigureState:
    """Holds the current figure state."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.plots = []
        self.title = ""
        self.xlabel = ""
        self.ylabel = ""
        self.options = {}
        self.legend_entries = []
        self._plot_index = 0

    def next_color_index(self) -> int:
        idx = self._plot_index
        self._plot_index += 1
        return idx


_state = _FigureState()


# =============================================================================
# Internal Helpers
# =============================================================================

def _format_coordinates(x: np.ndarray, y: np.ndarray) -> str:
    """Format x,y data as PGFPlots coordinates."""
    lines = []
    for xi, yi in zip(x, y):
        lines.append(f"\t({xi}, {yi})")
    return '\n'.join(lines)


def _build_axis_options() -> str:
    """Build the axis options string."""
    opts = []

    # Labels
    if _state.title:
        opts.append(rf"title={{\large {_state.title}}}")
    if _state.xlabel:
        opts.append(rf"xlabel={{\large {_state.xlabel}}}")
    if _state.ylabel:
        opts.append(rf"ylabel={{\large {_state.ylabel}}}")

    # Standard styling (matching reference)
    opts.append("ymajorgrids")

    # Only add these if 'axis lines' is not set (they conflict)
    if 'axis lines' not in _state.options:
        opts.extend([
            "xtick pos=left",
            "ytick pos=left",
            "x axis line style=-",
            "y axis line style=-",
        ])

    # Custom options
    for key, val in _state.options.items():
        if val is True:
            opts.append(key)
        elif val is not False and val is not None:
            opts.append(f"{key}={val}")

    # Legend if needed
    if _state.legend_entries:
        opts.append("legend pos=north west")

    return ',\n\t'.join(opts)


def _build_document() -> str:
    """Build the complete LaTeX document."""
    parts = [
        PREAMBLE.strip(),
        "",
        _color_definitions(),
        "",
        r"\begin{tikzpicture}",
        "",
        r"\begin{axis}[",
        f"\t{_build_axis_options()}",
        "]",
        "",
    ]

    # Add all plots
    parts.extend(_state.plots)

    # Add legend entries
    for entry in _state.legend_entries:
        parts.append(rf"\addlegendentry{{{entry}}}")

    parts.extend([
        "",
        r"\end{axis}",
        "",
        r"\end{tikzpicture}",
        POSTAMBLE.strip(),
    ])

    return '\n'.join(parts)


def _compile_tex(tex_path: Path) -> Optional[Path]:
    """Compile .tex to .pdf using lualatex or pdflatex."""
    tex_path = Path(tex_path)
    pdf_path = tex_path.with_suffix('.pdf')

    # Remove existing PDF to ensure fresh compilation
    if pdf_path.exists():
        pdf_path.unlink()

    # Try lualatex first (better Helvetica support), then pdflatex
    for compiler in ['lualatex', 'pdflatex']:
        if shutil.which(compiler) is None:
            continue

        try:
            subprocess.run(
                [compiler, '-interaction=nonstopmode', tex_path.name],
                cwd=tex_path.parent,
                capture_output=True,
                timeout=60,
            )

            # Check if PDF was created (may succeed even with warnings)
            if pdf_path.exists():
                # Clean up auxiliary files
                for ext in ['.aux', '.log']:
                    aux_file = tex_path.with_suffix(ext)
                    if aux_file.exists():
                        aux_file.unlink()
                return pdf_path

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            continue

    return None


# =============================================================================
# Public API
# =============================================================================

def new_figure(**options) -> None:
    """
    Start a new figure context.

    Parameters
    ----------
    **options : dict
        Additional axis options (e.g., ymode='log', xmin=0).
    """
    _state.reset()
    _state.options.update(options)


def line_plot(
    y: Sequence,
    x: Optional[Sequence] = None,
    label: str = "",
    color: Optional[Union[str, int]] = None,
    marker: str = "*",
    thick: bool = True,
) -> None:
    """
    Add a line plot to the current figure.

    Parameters
    ----------
    y : array-like
        The y-values to plot.
    x : array-like, optional
        The x-values. If None, uses indices.
    label : str, optional
        Label for the legend.
    color : str or int, optional
        Color name ('red', 'blue', etc.) or categorical index.
    marker : str, optional
        Marker style ('*', 'square*', 'o', 'none'). Default is '*'.
    thick : bool, optional
        Whether to use thick lines. Default is True.
    """
    y = np.asarray(y)
    if x is None:
        x = np.arange(len(y))
    else:
        x = np.asarray(x)

    color_name = _get_color(color, _state.next_color_index())

    opts = [f"color={color_name}"]
    if marker and marker != 'none':
        opts.append(f"mark={marker}")
    if thick:
        opts.append("thick")

    opts_str = ', '.join(opts)
    coords = _format_coordinates(x, y)

    plot_cmd = rf"\addplot [{opts_str}] coordinates {{{chr(10)}{coords}{chr(10)}}};"
    _state.plots.append(plot_cmd)

    if label:
        _state.legend_entries.append(label)


def multi_line_plot(
    ys: Sequence[Sequence],
    x: Optional[Sequence] = None,
    labels: Optional[Sequence[str]] = None,
    colors: Optional[Sequence[Union[str, int]]] = None,
    marker: str = "*",
    thick: bool = True,
) -> None:
    """
    Add multiple line plots to the current figure.

    Parameters
    ----------
    ys : sequence of array-like
        List of y-value arrays to plot.
    x : array-like, optional
        Shared x-values. If None, uses indices.
    labels : sequence of str, optional
        Labels for each line.
    colors : sequence of str/int, optional
        Colors for each line.
    marker : str, optional
        Marker style. Default is '*'.
    thick : bool, optional
        Whether to use thick lines. Default is True.
    """
    n = len(ys)
    if labels is None:
        labels = [None] * n
    if colors is None:
        colors = [None] * n

    for y, label, color in zip(ys, labels, colors):
        line_plot(y, x=x, label=label or "", color=color, marker=marker, thick=thick)


def bar_plot(
    values: Sequence,
    labels: Sequence[str],
    color: Optional[Union[str, int]] = None,
    bar_width: str = "15pt",
) -> None:
    """
    Add a bar plot to the current figure.

    Parameters
    ----------
    values : array-like
        The bar heights.
    labels : sequence of str
        Labels for each bar.
    color : str or int, optional
        Bar fill color.
    bar_width : str, optional
        Width of bars. Default is "15pt".
    """
    values = np.asarray(values)
    n = len(values)
    color_name = _get_color(color, 0)

    # Use numeric x coordinates with controlled spacing (like reference)
    # Bars at positions 0, 1, 2, ... with spacing proportional to bar width
    _state.options['ybar'] = True
    _state.options['bar width'] = bar_width
    _state.options['x'] = '0.7cm'  # Tighter spacing so bars aren't too far apart
    _state.options['enlarge x limits'] = '{abs=0.5}'

    # Set up x-axis ticks at bar positions with labels
    tick_positions = ', '.join(str(i) for i in range(n))
    tick_labels = ', '.join(labels)
    _state.options['xtick'] = f'{{{tick_positions}}}'
    _state.options['xticklabels'] = f'{{{tick_labels}}}'

    # Build coordinates with numeric x positions
    coords = []
    for i, val in enumerate(values):
        coords.append(f"\t({i}, {val})")
    coords_str = '\n'.join(coords)

    plot_cmd = rf"\addplot [fill={color_name}] coordinates {{{chr(10)}{coords_str}{chr(10)}}};"
    _state.plots.append(plot_cmd)


def histogram(
    data: Sequence,
    bins: int = 10,
    color: Optional[Union[str, int]] = None,
    density: bool = False,
) -> None:
    """
    Add a histogram to the current figure.

    Parameters
    ----------
    data : array-like
        The data to bin.
    bins : int, optional
        Number of bins. Default is 10.
    color : str or int, optional
        Bar fill color.
    density : bool, optional
        If True, normalize to density. Default is False.
    """
    data = np.asarray(data)
    counts, bin_edges = np.histogram(data, bins=bins, density=density)

    color_name = _get_color(color, 0)

    # Set histogram-specific axis options (matching reference style)
    _state.options['axis lines'] = 'left'
    _state.options['enlarge x limits'] = '0.05'
    # Add headroom above tallest bar to prevent clipping
    _state.options['ymax'] = float(counts.max()) * 1.1

    # Build coordinates for ybar interval
    coords = []
    for i, count in enumerate(counts):
        coords.append(f"({bin_edges[i]},{count})")
    # Add final edge with 0 height to close the interval
    coords.append(f"({bin_edges[-1]},{0})")
    coords_str = '\n'.join(coords)

    plot_cmd = rf"\addplot+[ybar interval, mark=no, fill={color_name}!50, draw=black, thin] plot coordinates{{{chr(10)}{coords_str}{chr(10)}}};"
    _state.plots.append(plot_cmd)


def set_labels(
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
) -> None:
    """
    Set title and axis labels.

    Parameters
    ----------
    title : str, optional
        Figure title.
    xlabel : str, optional
        X-axis label.
    ylabel : str, optional
        Y-axis label.
    """
    if title:
        _state.title = title
    if xlabel:
        _state.xlabel = xlabel
    if ylabel:
        _state.ylabel = ylabel


def set_options(**options) -> None:
    """
    Set additional axis options.

    Parameters
    ----------
    **options : dict
        PGFPlots axis options (e.g., ymode='log', ymin=0).
    """
    _state.options.update(options)


def save(
    path: Union[str, Path],
    compile: bool = True,
) -> Optional[Path]:
    """
    Save the figure as .tex and optionally compile to PDF.

    Parameters
    ----------
    path : str or Path
        Output path (should end with .tex).
    compile : bool, optional
        Whether to compile to PDF. Default is True.

    Returns
    -------
    pdf_path : Path or None
        Path to compiled PDF if successful, None otherwise.
    """
    path = Path(path)
    if path.suffix != '.tex':
        path = path.with_suffix('.tex')

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and write LaTeX
    content = _build_document()
    path.write_text(content)

    # Compile if requested
    pdf_path = None
    if compile:
        pdf_path = _compile_tex(path)

    return pdf_path


# =============================================================================
# Quick API
# =============================================================================

def _quick(plot_fn, args, kwargs, title, xlabel, ylabel, path, fig_options):
    """Helper for quick_* functions."""
    new_figure(**fig_options)
    plot_fn(*args, **kwargs)
    set_labels(title, xlabel, ylabel)
    if path:
        return save(path)
    return None


def quick_line(
    y,
    x=None,
    title="",
    xlabel="",
    ylabel="",
    path=None,
    **kw
):
    """Create a line plot in one call. Saves to path if provided."""
    return _quick(line_plot, (y,), {'x': x, **kw}, title, xlabel, ylabel, path, {})


def quick_lines(
    ys,
    x=None,
    labels=None,
    title="",
    xlabel="",
    ylabel="",
    path=None,
    **kw
):
    """Create a multi-line plot in one call. Saves to path if provided."""
    return _quick(multi_line_plot, (ys,), {'x': x, 'labels': labels, **kw}, title, xlabel, ylabel, path, {})


def quick_bar(
    values,
    labels,
    title="",
    xlabel="",
    ylabel="",
    path=None,
    **kw
):
    """Create a bar plot in one call. Saves to path if provided."""
    return _quick(bar_plot, (values, labels), kw, title, xlabel, ylabel, path, {})


def quick_histogram(
    data,
    title="",
    xlabel="",
    ylabel="Count",
    path=None,
    **kw
):
    """Create a histogram in one call. Saves to path if provided."""
    return _quick(histogram, (data,), kw, title, xlabel, ylabel, path, {})
