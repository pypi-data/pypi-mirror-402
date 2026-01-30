"""
Sample PGFPlots figures demonstrating the hmbp.pgfplots module.

This script generates .tex files and compiles them to PDF.
Requires a LaTeX distribution with lualatex or pdflatex.
"""

import numpy as np
from pathlib import Path

import hmbp.pgfplots as pgf

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "figures" / "pgfplots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def line_plot_example():
    """Generate a line plot with markers."""
    x = np.array([0, 1, 2, 3, 4, 5])
    y = np.array([1.2, 2.5, 1.8, 4.2, 3.5, 5.1])

    pgf.new_figure()
    pgf.line_plot(y, x=x, label="Measurements", marker="*")
    pgf.set_labels(
        title="Sample Line Plot",
        xlabel="Time (s)",
        ylabel="Value",
    )
    pdf = pgf.save(OUTPUT_DIR / "line_plot.tex")
    print(f"Line plot: {pdf or 'tex only'}")


def multi_line_example():
    """Generate a plot with multiple lines."""
    x = np.linspace(0, 10, 20)
    y1 = np.sin(x)
    y2 = np.cos(x)
    y3 = np.sin(x) * 0.5

    pgf.new_figure()
    pgf.multi_line_plot(
        [y1, y2, y3],
        x=x,
        labels=["sin(x)", "cos(x)", "0.5 sin(x)"],
        marker="*",
    )
    pgf.set_labels(
        title="Trigonometric Functions",
        xlabel="x",
        ylabel="y",
    )
    pdf = pgf.save(OUTPUT_DIR / "multi_line.tex")
    print(f"Multi-line plot: {pdf or 'tex only'}")


def bar_chart_example():
    """Generate a bar chart."""
    values = np.array([23, 45, 12, 67, 34])
    labels = ["A", "B", "C", "D", "E"]

    pgf.new_figure()
    pgf.bar_plot(values, labels, color="purple")
    pgf.set_labels(
        title="Category Comparison",
        xlabel="Category",
        ylabel="Count",
    )
    pdf = pgf.save(OUTPUT_DIR / "bar_chart.tex")
    print(f"Bar chart: {pdf or 'tex only'}")


def histogram_example():
    """Generate a histogram."""
    np.random.seed(42)
    data = np.random.normal(loc=5, scale=2, size=500)

    pgf.new_figure()
    pgf.histogram(data, bins=15, color="purple")
    pgf.set_labels(
        title="Distribution",
        xlabel="Value",
        ylabel="Count",
    )
    pdf = pgf.save(OUTPUT_DIR / "histogram.tex")
    print(f"Histogram: {pdf or 'tex only'}")


def log_scale_example():
    """Generate a line plot with logarithmic y-axis."""
    x = np.array([1, 2, 3, 4, 5, 6])
    y = np.array([10, 100, 1000, 5000, 20000, 100000])

    pgf.new_figure(ymode="log")
    pgf.line_plot(y, x=x, label="Exponential Growth", marker="square*")
    pgf.set_labels(
        title="Logarithmic Scale",
        xlabel="Step",
        ylabel="Value",
    )
    pdf = pgf.save(OUTPUT_DIR / "log_scale.tex")
    print(f"Log scale plot: {pdf or 'tex only'}")


def quick_api_example():
    """Demonstrate quick API functions."""
    # Quick line plot
    y = [1, 3, 2, 5, 4, 6]
    pdf = pgf.quick_line(
        y,
        title="Quick Line",
        xlabel="X",
        ylabel="Y",
        path=OUTPUT_DIR / "quick_line.tex",
    )
    print(f"Quick line: {pdf or 'tex only'}")

    # Quick bar chart
    pdf = pgf.quick_bar(
        [10, 25, 15, 30],
        ["Q1", "Q2", "Q3", "Q4"],
        title="Quarterly Results",
        xlabel="Quarter",
        ylabel="Revenue",
        path=OUTPUT_DIR / "quick_bar.tex",
    )
    print(f"Quick bar: {pdf or 'tex only'}")

    # Quick histogram
    np.random.seed(123)
    data = np.random.exponential(scale=2, size=300)
    pdf = pgf.quick_histogram(
        data,
        bins=12,
        title="Exponential Distribution",
        xlabel="Value",
        path=OUTPUT_DIR / "quick_histogram.tex",
    )
    print(f"Quick histogram: {pdf or 'tex only'}")


if __name__ == "__main__":
    print("Generating PGFPlots examples...\n")

    line_plot_example()
    multi_line_example()
    bar_chart_example()
    histogram_example()
    log_scale_example()
    quick_api_example()

    print(f"\nOutput directory: {OUTPUT_DIR}")
