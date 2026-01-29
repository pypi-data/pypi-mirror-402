# WindKit

[![pipeline status](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/badges/master/pipeline.svg)](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/pipelines)
[![coverage](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/badges/master/coverage.svg)](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/pipelines)
[![release](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/badges/release.svg)](https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/releases)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-docs.wasp.dk-blue?logo=readthedocs&logoColor=white)](https://docs.wasp.dk/windkit)

[![PyPI](https://img.shields.io/pypi/v/windkit)](https://pypi.org/project/windkit/)
[![Downloads-pypi](https://img.shields.io/pypi/dm/windkit)](https://pypi.org/project/windkit/)


WindKit provides core functionalities for working with wind resource data, built on top of [xarray](https://xarray.dev/) and [geopandas](https://geopandas.org/).

## Installation

**pip:**
```bash
pip install windkit
```

**conda:**
```bash
conda install -c https://conda.windenergy.dtu.dk/channel/open windkit
```

## Quick Start

```python
import windkit as wk

# Read a binned wind climate
bwc = wk.read_bwc("hovsore.tab")

# Calculate mean wind speed
mean_ws = wk.mean_wind_speed(bwc)
print(f"Mean wind speed: {mean_ws.values:.2f} m/s")

# Fit Weibull distribution and convert to Weibull wind climate
wwc = wk.weibull_fit(bwc)
```

## Features

- **Wind Climate I/O** - Read/write binned, Weibull, generalized, and time-series wind climates (NetCDF, .lib, .tab, .rsf, .wrg)
- **Map I/O** - Read/write elevation, roughness, and landcover maps (raster and vector formats)
- **WAsP Integration** - Read WAsP Workspace files and WAsP Engineering project files
- **Spatial Processing** - Clip, reproject, and interpolate spatial data with full CRS support
- **Wind Statistics** - Calculate mean wind speed, power density, Weibull parameters, and more
- **Plotting** - Interactive plots with Plotly, static plots with Matplotlib
- **Remote Data Access** - Download ERA5 reanalysis data and satellite-derived maps

## Documentation

Full documentation: [docs.wasp.dk/windkit](https://docs.wasp.dk/windkit)

Community forum: [WAsP Python tools](https://www.wasptechnical.dk/forum/forum/19-wasp-python-tools/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

BSD-3-Clause - see [LICENSE](LICENSE) for details.
