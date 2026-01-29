import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import Colormap, ListedColormap
from matplotlib.projections.polar import PolarAxes
from numpy.typing import NDArray


def radar_chart(
    label: list[str],
    data: NDArray[np.number] | list[int] | list[float] | dict[str, NDArray[np.number] | list[int] | list[float]],
    cmap: Colormap | ListedColormap | str | list[str] | list[tuple[float, float, float]] = "tab10",
    ax: PolarAxes | None = None,
    return_axis: bool = False,
    show_grid: bool = True,
    rotation: int = 0,
    ticks: int | list[float] | list[int] = 3,
    vmax: int | float | None = None,
    vmin: int | float = 0,
    title: str | None = None,
    opacity: float = 0.25,
) -> PolarAxes | None:
    """Generate radar chart with matplotlib.

    .. code-block:: python

        from matplotlib_radar import radar_chart
        import numpy as np

        radar_chart(
            label=["A", "B", "C", "D", "E"],
            data={
                "Sample 1": np.random.rand(5),
                "Sample 2": np.random.rand(5),
                "Sample 3": np.random.rand(5),
            },
            title="Radar chart example",
        )

    Args:
        label (typing.List[str]): List of labels to annotate polar axes.
        data (typing.Union[numpy.ndarray[numpy.number], typing.Dict[str, numpy.ndarray[numpy.number]]]):
            Data to plot as radar chart. As data type list or numpy array of numbers are supported. If plotting multiple
            samples, data must be a dictionary with labels as keys and data arrays as values.
        cmap (typing.Union[matplotlib.colors.Colormap, matplotlib.colors.ListedColormap, str, typing.List[str], typing.List[typing.Tuple[float, float, float]]], optional): Colormap for coloring plot. Provide name of colormap as
            string (both qualitative and sequential colormaps are valid) or pass a Colormap object. Defaults to
            `"tab10"`.
        ax (typing.Optional[matplotlib.projections.polar.PolarAxes], optional): Matplotlib axes. Axes are generate and
            returned if not provided. Defaults to `None`.
        return_axis (bool, optional): Whether to return axis of the generated plot. If false, axes are returned.
            Defaults to `False`.
        show_grid (bool, optional): Show grid. Defaults to `True`.
        rotation (int, optional): Rotation of polar axes. Defaults to `0`.
        ticks (typing.Union[int, typing.List[float], typing.List[int]]): Define ticks for plot. Provide number of ticks
            to generate or and array of numbers to tick values. Defaults to `3`.
        vmax (typing.Optional[typing.Union[int, float]], optional): Axes maximal value. Defaults to `None`. If None,
            maximal value is calculated from provided data.
        vmin (typing.Union[int, float], optional): Axes minimal value. Defaults to `0`.
        title (typing.Optional[str], optional): Title of plot. Defaults to `None`.
        opacity (float, optional): Alpha value of plot fill color. Defaults to `0.25`.

    Raises:
        AssertionError: If labels are not provided.
        AssertionError: If data array has more than 2 dimensions.
        TypeError: If other types besides `Colormap` or `str` are passed as `cmap` parameter.

    Returns:
        typing.Union[matplotlib.projections.polar.PolarAxes, None]: Return axes if `show_figure=False`. Otherwise
        returns `None`.
    """
    # Check length and shape of labels and data array
    assert len(label) > 1, "At least 1 label is required."

    sample_labels: list[str] = []
    sample_data: NDArray

    if isinstance(data, list):
        # Convert to list if data is numpy array
        data = np.array(data)

    if isinstance(data, np.ndarray):
        assert len(data.shape) == 1, "If data is a numpy array, only 1 dimension is supported."
        # Reshape data array if only 1 dim
        sample_data = np.array([data])
    elif isinstance(data, dict):
        sample_labels = list(data.keys())
        sample_data = np.array(list(data.values()))
    else:
        raise AssertionError("Only data as 1 or 2 dimensional arrays are supported.")

    assert len(label) == sample_data.shape[1]

    # Generate angles for axes in polar plot
    theta = np.linspace(0, 2 * np.pi, len(label), endpoint=False)

    # If no axes are given as argument, generate them
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, polar=True)  # type: ignore

    assert ax is not None, "Axes at not defined."

    # Get colormap for polygons
    if isinstance(cmap, str):
        cmap = matplotlib.colormaps.get_cmap(cmap)
    elif isinstance(cmap, list):
        cmap = ListedColormap(cmap)

    if not isinstance(cmap, Colormap):
        raise TypeError(f"Type '{type(cmap).__name__}' of argument 'cmap' not supported")

    if cmap.N > 20:
        norm = plt.Normalize(vmin=0, vmax=sample_data.shape[0] - 1)
    else:
        norm = plt.Normalize(vmin=0, vmax=cmap.N - 1)

    handles = []

    for index, sample_data_item in enumerate(sample_data):
        # Plot outline
        (plot_handle,) = ax.plot(
            np.concatenate((theta, [theta[0]])),
            np.concatenate((sample_data_item, [sample_data_item[0]])),
            linewidth=1,
            color=cmap(norm(index)),
            marker=None,
            alpha=1,
        )

        # Append outline axis to handle
        handles.append(plot_handle)

        # Fill plotted outline
        ax.fill(
            np.concatenate((theta, [theta[0]])),
            np.concatenate((sample_data_item, [sample_data_item[0]])),
            alpha=opacity,
            color=cmap(norm(index)),
        )

    # add estimation of vmax
    if vmax is None:
        vmax = sample_data.flatten().max() * 1.1

    if isinstance(ticks, list):
        ax.set_rticks(ticks)
    else:
        ax.set_rticks(np.round(np.linspace(vmin, vmax, ticks + 2), 2))  # Less radial ticks

    ax.set_rlabel_position(-22)  # Move radial labels away from plotted line

    ax.set_thetagrids(theta * 180 / np.pi, label)
    ax.set_theta_offset(rotation / 180 * np.pi)

    # Add/remove grid
    ax.grid(show_grid)

    # Add legend if multiple samples are provided
    if len(sample_labels) > 0:
        ax.legend(handles, sample_labels, loc="center", borderaxespad=0.0, bbox_to_anchor=(1, 1))

    # Add title
    if title is not None:
        ax.set_title(title, loc="center")

    # Show plot or return axes
    if return_axis is True:
        return ax

    return None
