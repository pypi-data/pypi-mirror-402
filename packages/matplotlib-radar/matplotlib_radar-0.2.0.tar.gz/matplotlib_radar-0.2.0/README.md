# matplotlib-radar

[![Version](https://img.shields.io/pypi/v/matplotlib-radar)](https://pypi.org/project/matplotlib-radar/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/matplotlib-radar)
[![codecov](https://codecov.io/gh/harryhaller001/matplotlib-radar/graph/badge.svg?token=WO0CGOVJOH)](https://codecov.io/gh/harryhaller001/matplotlib-radar)

Feature-rich generation of radar chart based on matplotlib.

## Quick start

Install package with `pip install matplotlib-radar` or `uv add matplotlib-radar`.

Example code to generate radar chart:

```python
from matplotlib_radar import radar_chart
import numpy as np

radar_chart(
    label=["A", "B", "C", "D", "E"],
    data={"Sample 1": np.random.rand(5), "Sample 2": np.random.rand(5), "Sample 3": np.random.rand(5)},
    rotation=5,
    title="Radar chart with multiple samples",
)
```


![Example radar chart](./docs/source/_static/image/example-radar-chart.jpg)

For more plotting examples, check out the vignette notebook in the documentation.

## Development

```bash
# Clone repo
git clone https://github.com/harryhaller001/matplotlib-radar
cd matplotlib-radar

# Setup virtualenv
uv venv

# Install dependencies and setup precommit hook
make install

# Run all checks
make format
make testing
make typing
make build
```

## License

MIT license
