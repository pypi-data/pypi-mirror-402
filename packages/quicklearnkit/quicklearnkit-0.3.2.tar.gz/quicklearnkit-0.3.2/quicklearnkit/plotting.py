import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


# ---------------- INTERNAL HELPERS ---------------- #

def _show_flag(val):
    """Normalize truthy string/boolean flags."""
    return str(val).lower() in ("yes", "y", "true", "1")


def _add_value_labels(ax, fmt="{:.2f}", offset=(0, 3)):
    """
    Attach value labels to bars, line points, and scatter points.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes object containing the plot
    fmt : str
        Format string for values
    offset : tuple
        (x, y) pixel offset for annotations
    """
    # Bars (barplot, countplot, histogram bars)
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, padding=3)

    # Lines / scatter points
    for line in ax.lines:
        x_data = line.get_xdata()
        y_data = line.get_ydata()

        for x, y in zip(x_data, y_data):
            if y is None or (isinstance(y, float) and np.isnan(y)):
                continue

            ax.annotate(
                fmt.format(y),
                (x, y),
                textcoords="offset points",
                xytext=offset,
                ha="center"
            )


# ---------------- PUBLIC API ---------------- #

def bar_plot(
    data,
    x,
    y,
    title=None,
    show_values="no",
    fmt="{:.1f}",
    show=True,
    **kwargs
):
    """
    Draw a bar plot with optional value labels.

    Supports all seaborn.barplot parameters via **kwargs
    (e.g., hue, palette, dodge, estimator, errorbar, etc.)

    Returns
    -------
    matplotlib.axes.Axes
        Axes object for further customization
    """
    ax = sns.barplot(data=data, x=x, y=y, **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        _add_value_labels(ax, fmt=fmt)

    if show:
        plt.show()

    return ax


def line_plot(
    data,
    x,
    y,
    title=None,
    show_values="no",
    fmt="{:.2f}",
    show=True,
    **kwargs
):
    """
    Draw a line plot with optional value labels.

    Supports all seaborn.lineplot parameters via **kwargs
    (e.g., hue, style, size, palette, estimator, ci, etc.)

    Returns
    -------
    matplotlib.axes.Axes
    """
    ax = sns.lineplot(data=data, x=x, y=y, marker="o", **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        _add_value_labels(ax, fmt=fmt)

    if show:
        plt.show()

    return ax


def scatter_plot(
    data,
    x,
    y,
    title=None,
    show_values="no",
    fmt="{:.2f}",
    show=True,
    **kwargs
):
    """
    Draw a scatter plot with optional value labels.

    Supports all seaborn.scatterplot parameters via **kwargs
    (e.g., hue, style, size, palette, legend, etc.)

    Returns
    -------
    matplotlib.axes.Axes
    """
    ax = sns.scatterplot(data=data, x=x, y=y, **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        _add_value_labels(ax, fmt=fmt)

    if show:
        plt.show()

    return ax


def count_plot(
    data,
    x,
    title=None,
    show_values="no",
    show=True,
    **kwargs
):
    """
    Draw a count plot with optional value labels.

    Supports all seaborn.countplot parameters via **kwargs
    (e.g., hue, palette, order, dodge, etc.)

    Returns
    -------
    matplotlib.axes.Axes
    """
    ax = sns.countplot(data=data, x=x, **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        for container in ax.containers:
            ax.bar_label(container, padding=3)

    if show:
        plt.show()

    return ax


def box_plot(
    data,
    x=None,
    y=None,
    title=None,
    show_values="no",
    fmt="{:.2f}",
    show=True,
    **kwargs
):
    """
    Draw a box plot. If show_values is enabled, display mean value(s).

    Supports all seaborn.boxplot parameters via **kwargs
    (e.g., hue, palette, order, width, etc.)

    Returns
    -------
    matplotlib.axes.Axes
    """
    ax = sns.boxplot(data=data, x=x, y=y, **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        # Compute mean(s)
        if y:
            if x:
                means = data.groupby(x)[y].mean()
            else:
                means = [data[y].mean()]
        else:
            means = [data.mean(numeric_only=True).values[0]]

        for i, mean_val in enumerate(means):
            ax.annotate(
                f"Mean: {fmt.format(mean_val)}",
                (i, mean_val),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                color="red"
            )

    if show:
        plt.show()

    return ax


def hist_plot(
    data,
    x,
    bins=10,
    title=None,
    show_values="no",
    fmt="{:.0f}",
    show=True,
    **kwargs
):
    """
    Draw a histogram. If show_values is enabled, display bin counts.

    Supports all seaborn.histplot parameters via **kwargs
    (e.g., hue, palette, kde, stat, multiple, element, etc.)

    Returns
    -------
    matplotlib.axes.Axes
    """
    ax = sns.histplot(data=data, x=x, bins=bins, **kwargs)

    if title:
        ax.set_title(title)

    if _show_flag(show_values):
        for patch in ax.patches:
            height = patch.get_height()
            if height > 0:
                ax.annotate(
                    fmt.format(height),
                    (patch.get_x() + patch.get_width() / 2, height),
                    ha="center",
                    va="bottom",
                    xytext=(0, 3),
                    textcoords="offset points"
                )

    if show:
        plt.show()

    return ax
