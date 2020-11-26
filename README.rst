
Pandas reader for the BUFR format using ecCodes.

Features with development status **Alpha**:

- extracts observations from a BUFR file as a Pandas DataFrame,
- reads BUFR 3 and 4 files with uncompressed and compressed subsets,
- supports all modern versions of Python 3.9, 3.8, 3.7, 3.6 and PyPy3,
- works on Linux, MacOS and Windows, the ecCodes C-library is the only binary dependency.

Limitations:

- no special handling of nodata values (yet),
- no conda-forge package (yet),
- filters only match exact values.

Installation
============

The easiest way to install *pdbufr* dependencies is via Conda::

    $ conda install -c conda-forge python-eccodes pandas

and *pdbufr* itself as a Python package from PyPI with::

    $ pip install pdbufr


System dependencies
-------------------

The Python module depends on the ECMWF *ecCodes* library
that must be installed on the system and accessible as a shared library.
Some Linux distributions ship a binary version that may be installed with the standard package manager.
On Ubuntu 18.04 use the command::

    $ sudo apt-get install libeccodes0

On a MacOS with HomeBrew use::

    $ brew install eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m pdbufr selfcheck
    Found: ecCodes v2.19.0.
    Your system is ready.


Usage
=====

First, you need a well-formed BUFR file, if you don't have one at hand you can download our
`sample file <http://download.ecmwf.int/test-data/metview/gallery/temp.bufr>`_::

    $ wget http://download.ecmwf.int/test-data/metview/gallery/temp.bufr

You can explore the file with *ecCodes* command line tools ``bufr_ls`` and ``bufr_dump`` to
understand the structure and the keys/values you can use to select the observations you
are interested in.

The ``pdbufr.read_bufr`` function return a ``pandas.DataDrame`` with the requested columns.
It accepts query filters on the BUFR message header
that are very fast and query filters on the observation keys.
Filters match on an exact value or with one of the values in a list and all filters must match:

.. code-block:: python

    >>> import pdbufr
    >>> df_all = pdbufr.read_bufr('temp.bufr', columns=('stationNumber', 'latitude', 'longitude'))
    >>> df_all.head()
       stationNumber  latitude  longitude
    0            907     58.47     -78.08
    1            823     53.75     -73.67
    2              9    -90.00       0.00
    3            486     18.43     -69.88
    4            165     21.98    -159.33

    >>> df_one = pdbufr.read_bufr(
    ...     'temp.bufr',
    ...     columns=('stationNumber', 'latitude', 'longitude'),
    ...     filters={'stationNumber': 907},
    ... )
    >>> df_one.head()
       stationNumber  latitude  longitude
    0            907     58.47     -78.08

    >>> df_two = pdbufr.read_bufr(
    ...     'temp.bufr',
    ...     columns=('stationNumber', 'data_datetime', 'pressure', 'airTemperature'),
    ...     filters={'stationNumber': [823, 9]},
    ... )

    >>> df_two.head()
       stationNumber  pressure  airTemperature       data_datetime
    0            823  100000.0             NaN 2008-12-08 12:00:00
    1            823   97400.0           256.7 2008-12-08 12:00:00
    2            823   93700.0           255.1 2008-12-08 12:00:00
    3            823   92500.0           255.3 2008-12-08 12:00:00
    4            823   90600.0           256.7 2008-12-08 12:00:00

    >>> df_two.tail()
         stationNumber  pressure  airTemperature       data_datetime
    190              9    2990.0             NaN 2008-12-08 12:00:00
    191              9    2790.0           206.3 2008-12-08 12:00:00
    192              9    2170.0             NaN 2008-12-08 12:00:00
    193              9    2000.0           203.1 2008-12-08 12:00:00
    194              9    1390.0           197.9 2008-12-08 12:00:00


Contributing
============

The main repository is hosted on GitHub,
testing, bug reports and contributions are highly welcomed and appreciated:

https://github.com/ecmwf/pdbufr

Please see the CONTRIBUTING.rst document for the best way to help.

Lead developer:

- `Alessandro Amici <https://github.com/alexamici>`_ - `B-Open <https://bopen.eu>`_

Main contributors:

- `Sandor Kertesz <https://github.com/sandorkertesz>`_ - `ECMWF <https://ecmwf.int>`_

See also the list of `contributors <https://github.com/ecmwf/pdbufr/contributors>`_ who participated in this project.


License
=======

Copyright 2019 European Centre for Medium-Range Weather Forecasts (ECMWF).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0.
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
