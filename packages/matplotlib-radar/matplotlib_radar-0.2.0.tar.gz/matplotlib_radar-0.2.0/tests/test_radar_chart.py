import pytest
from matplotlib.projections.polar import PolarAxes

from matplotlib_radar import radar_chart


def test_plotting() -> None:
    """
    Testing if plotting function is running.
    """

    # Testing basic plotting function
    radar_chart(label=["A", "B", "C"], data=[1, 2, 3])

    # Testing sequential colormap as parameter
    radar_chart(label=["A", "B", "C"], data=[1, 2, 3], cmap="viridis")

    # Testing list of colors as parameter for cmap
    radar_chart(label=["A", "B", "C"], data=[1, 2, 3], cmap=["#C70E7B", "#1BB6AF"])

    # Testing title
    radar_chart(label=["A", "B", "C"], data=[1, 2, 3], title="Testing")

    # Testing ticks
    radar_chart(label=["A", "B", "C"], data=[1, 2, 3], ticks=[0.0, 2.0, 4.0])

    # Testing return axes
    assert isinstance(radar_chart(label=["A", "B", "C"], data=[1, 2, 3], return_axis=True), PolarAxes)

    # Testing multiple samples
    radar_chart(label=["A", "B", "C"], data={"1": [1, 2, 3], "2": [4, 5, 6], "3": [7, 8, 9]})

    with pytest.raises(TypeError):
        radar_chart(
            label=["A", "B", "C"],
            data=[1, 2, 3],
            cmap=None,  # type: ignore
        )
