Installation and Getting Started
================================

Installing from PyPI
--------------------

Install the latest release with Python >= 3.9 and ``pip`` as follows:

.. code-block:: bash

    pip install pdbufr


Import and use
--------------

.. code-block:: python

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


Selfcheck
------------

You may run a simple selfcheck command to ensure that your system is set up correctly:

.. code-block:: bash

    $ python -m pdbufr selfcheck
    Found: ecCodes v2.19.0.
    Your system is ready.
