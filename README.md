<p align="center">
  <picture>
    <source srcset="https://github.com/ecmwf/logos/raw/refs/heads/main/logos/pdbufr/pdbufr-dark.svg" media="(prefers-color-scheme: dark)">
    <img src="https://github.com/ecmwf/logos/raw/refs/heads/main/logos/pdbufr/pdbufr-light.svg" height="120">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg" alt="ECMWF Software EnginE">
  </a>
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/Project Maturity">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/Project Maturity/incubating_badge.svg" alt="Maturity Level">
  </a>
  <a href="https://opensource.org/licenses/apache-2-0">
    <img src="https://img.shields.io/badge/Licence-Apache 2.0-blue.svg" alt="Licence">
  </a>
  <a href="https://github.com/ecmwf/pdbufr/releases">
    <img src="https://img.shields.io/github/v/release/ecmwf/pdbufr?color=purple&label=Release" alt="Latest Release">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a>
  •
  <a href="#installation">Installation</a>
  •
  <a href="https://pdbufr.readthedocs.io/en/latest/">Documentation</a>
</p>

> \[!IMPORTANT\]
> This software is **Incubating** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).

**pdbufr** is a Python package implementing a [Pandas](https://pandas.pydata.org) reader for the BUFR format using  [ecCodes](https://confluence.ecmwf.int/display/ECC).

## Quick Start

```python

    import urllib.request
    from pathlib import Path
    import pdbufr

    # get a radiosonde BUFR file
    url = "https://sites.ecmwf.int/repository/pdbufr/test-data/temp.bufr"
    if not Path("temp.bufr").exists():
        urllib.request.urlretrieve(url, "temp.bufr")

    # extract the station id, datetime, pressure and air temperature for two stations
    # for all the available pressure levels into a pandas dataframe
    df = pdbufr.read_bufr(
        "temp.bufr",
        columns=("WMO_station_id", "data_datetime", "pressure", "airTemperature"),
        filters={"WMO_station_id": [71823, 71907]},
    )

```

## Installation

Install via `pip` with:

```
$ pip install pdbufr
```

Alternatively, install via `conda` with:

```
$ conda install pdbufr -c conda-forge
```

## Licence

```
Copyright 2019-, European Centre for Medium Range Weather Forecasts.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

In applying this licence, ECMWF does not waive the privileges and immunities
granted to it by virtue of its status as an intergovernmental organisation
nor does it submit to any jurisdiction.
```
