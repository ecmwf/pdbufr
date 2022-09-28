Usage
=====

First, you need a well-formed BUFR file, if you don't have one at hand you can download our
`sample file <http://download.ecmwf.int/test-data/metview/gallery/temp.bufr>`_::

    $ wget http://download.ecmwf.int/test-data/metview/gallery/temp.bufr

You can explore the file with *ecCodes* command line tools ``bufr_ls`` and ``bufr_dump`` to
understand the structure and the keys/values you can use to select the observations you
are interested in.

The ``pdbufr.read_bufr`` function return a ``pandas.DataFrame`` with the requested columns.
It accepts query filters on the BUFR message header
that are very fast and query filters on the observation keys.
Additionally also on the following computed keys:

- data_datetime and typical_datetime (datetime.datetime)
- geometry (List [longitude,latitude,heightOfStationGroundAboveMeanSeaLevel])
- CRS (BufrKey Coordinate Reference System Values 0,1,2,3 and missing are supported (4 and 5 are not supported), defaults to WGS84 (EPSG:4632))

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
