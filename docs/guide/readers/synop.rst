.. _synop-reader:

Synop
-------------

.. warning::

    This reader is **experimental** and the API might change in the future. It is not recommended to use it in production code yet.


*New in version 0.13.0*

.. py:function:: read_bufr(path, reader="synop", columns=[], filters=None, stnid_keys=None, units_system=None, units=None, units_columns=False, level_columns=False)
    :noindex:

    Extract :ref:`synop-like data <synop-like-data>` from BUFR using pre-defined :ref:`parameters <synop-params>`.

    :param path: path to the BUFR file or a :ref:`message list object <message-list-object>`
    :type path: str, bytes, os.PathLike or a :ref:`message list object <message-list-object>`
    :param columns: specify the pre-defined :ref:`parameters <synop-params>` to extract. The possible values are as follows:

        - "default" or empty list: extract the parameters as in "station" followed by all the :ref:`default observed parameters <synop-default-obs-params>`
        - "location": extract only the "lat" and "lon" parameters (see :ref:`station parameters <synop-station-params>` for details)
        - "geometry": extract only the "lat", "lon" and "elevation" parameters (see :ref:`station parameters <synop-station-params>` for details)
        - "station": extract only the "stnid", "time", "lat", "lon" and "elevation" parameters (see :ref:`station parameters <synop-station-params>` for details)
        - when it is a non-empty list, specifies the :ref:`parameters <synop-params>` to extract. The keys "default", "location", "geometry" and "station" can all be part of the list and will add all the parameters from the corresponding group.

    :type columns: str, sequence[str]
    :param filters: define the conditions when to extract the data. The individual conditions are combined together with the logical AND operator to form the filter. It can contain both BUFR keys and parameters. See :ref:`synop-filters` and :ref:`filters` for details.
    :type filters: dict
    :param stnid_keys: BUFR keys to extract data for the ``stnid`` param. When None, the default list of BUFR keys are used (see ``stnid`` in :ref:`station parameters <synop-station-params>`). *New in version 0.14.0*
    :type stnid_keys: str, sequence[str], None
    :param unit_system: define the unit system to generate the resulting values. The default is None, which means that no conversion is applied but the values/units found in the BUFR are written to the output as is. The only available unit system is: "pdbufr". The "pdbufr" system uses the units as defined in the :ref:`synop-params` section.
    :type unit_system: str, None
    :param units: specify custom units conversions as a dictionary. The keys are the parameter names and the values are the units to convert to. For keys not specified in ``units`` the conversion defined by ``unit_system`` is applied. E.g.:

        .. code-block:: python

            units = {
                "t2m": "C",
                "mslp": "hPa",
            }

    :type units: dict, None
    :param units_columns: if True, a :ref:`units column <synop-units>` is added to the resulting DataFrame for each :ref:`parameter <synop-params>` having a units. The column name is formed by adding the "_units" suffix to the parameter name. The default is False.
    :type add_units: bool
    :param level_columns: if True, a :ref:`level column <synop-levels>` is added to the resulting DataFrame for each :ref:`parameter <synop-params>` having a level. The column name is formed by adding the "_level" suffix to the parameter name. The default is False.
    :rtype: pandas.DataFrame


.. _synop-like-data:

SYNOP-like data
++++++++++++++++++++++++++++

In the context of this reader the term "SYNOP-like" means data that is similar to SYNOP/SHIP observations, and it contains all messages/subsets with ``dataCategory`` either  0 (land) or 1 (sea). See details on the data category :ref:`here <bufr-data-category>`. Note that this also contains observations e.g. buoys, which might not fit into this category. This will be revisited in the future.


The resulting DataFrame
+++++++++++++++++++++++++

The resulting DataFrame will contain one row for each station/platform and one column for each :ref:`parameter <synop-params>`. The columns are named after the parameter names, e.g. "t2m". With the default settings the first columns are always the station/platform identifier, time, latitude, longitude and elevation followed by the observed parameters. E.g.::


        stnid       lat        lon   elevation       time     t2m  rh2m   ...
    0  91948 -23.13017 -134.96533       91.0 2020-03-15  300.45    73   ...
    1  11766  49.77722   17.54194      748.1 2020-03-15  269.25    65   ...


.. _synop-periods:

Periods
/////////////////////

When a parameter is associated with a **time period** for each period a separate column is created with the period encoded into the column name. E.g. if windgust is available for the last 10 minutes, the resulting DataFrame will contain the following columns::

            wind_gust_speed_10min  wind_gust_dir_10min
    0                 5.0            225
    1                 4.5            123

The period string is constructed from the values encoded in the BUFR message. When the period is not available the "_nan" suffix is used, e.d. "wind_gust_nan".

.. _synop-levels:

Levels
/////////////////////

When ``level_columns=True`` and a parameter is associated with a **height level** a separate column is created for the level value. The column name is formed by adding the "_level" suffix to the parameter name::

        t2m       t2m_level
    0   273.15       2.0
    1   274.15       2.5

.. _synop-units:

Units
/////////////////////

When ``units_columns=True`` and a parameter has an associated **units** a separate column is created for the units. The column name is formed by adding the "_units" suffix to the parameter name::

        t2m       t2m_units
    0   273.15       K
    1   274.15       K

Levels and units
/////////////////////

Options ``level_columns=True`` and ``units_columns=True`` can be used together. In this case the column names are formed as follows::

            t2m    t2m_units   t2m_level
    0   273.15       K              2.0
    1   274.15       K              2.5


Periods, levels and units
////////////////////////////

When periods are available "_level" and/or "_units" suffixes are added after the period in the column names. E.g. when ``level_columns=True`` the column names are formed as follows::

            wind_gust_speed_10min  wind_gust_10min_level  wind_gust_dir_10min  wind_gust_dir_10min_level
    0               5.0              9.6                   225                    9.6
    1               4.5              9.6                   123                    9.6




.. _synop-params:

Parameters
+++++++++++++++++++++

A parameter is a high-level concept in ``pdbufr``. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. E.g. 2m temperature can be represented in at least 2 different ways:

  - as "airTemperatureAt2M"
  - as "airTemperature" instnide a group "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform=2".

When using parameters like "t2m" we do not need to know the actual encoding, but the desired value is automatically extracted for us. Another advantage is that we can easily extract the observation periods, levels and units for each parameter, which is simply not possible with the :ref:`generic reader <flat-reader>`.

SYNOP parameters can be divided into three groups:

- `station/platform related parameters <synop-station-params>`_,
- `default observed parameters <synop-default-obs-params>`_,
- `additional observed parameters <synop-extra-obs-params>`_.


.. _synop-station-params:

Station/platform params
////////////////////////////

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: center

   * - **Name**
     - **Units/Object**
     - **Description**

   * - stnid
     -
     - | Station/platform identifier as a str. The following keys are
       | tried in order to generate the value (the first one with a
       | valid value is used):

        - "ident"
        - :ref:`WMO station id <key-wmo-station-id>`
        - :ref:`WIGOS station id <key-WIGOS-station-id>`
        - "shipOrMobileLandStationIdentifier"
        - "station_id"
        - "icaoLocationIndicator"
        - "stationOrSiteName"
        - "longStationName"

   * - time
     - datatime.datetime
     - Time of the observation

   * - lat
     - deg
     - Latitude

   * - lon
     - deg
     - Longitude

   * - elevation
     - m
     - Elevation

   * - name
     - str
     - | Name of the station/platform. The following keys are tried
       | in order to generate the value:
       | "stationOrSiteName" and "icaoLocationIndicator".


.. _synop-default-obs-params:

Default observed parameters
/////////////////////////////

These parameters are all added when using the default settings in ``columns``.

.. list-table:: P: means has a period, L: means has a level
   :header-rows: 1
   :widths: 10 10 60 10 10
   :align: center


   * - Name
     - Units
     - Description
     - P
     - L

   * - t2m
     - K
     - 2m temperature
     -
     - L

   * - td2m
     - K
     - 2m dew point temperature
     -
     - L

   * - rh2m
     - %
     - 2m relative humidity (0-100)
     -
     - L

   * - mslp
     - Pa
     - Mean sea level pressure
     -
     -

   * - pressure
     - Pa
     - Pressure at station/platform
     -
     -

   * - wind10m
     -
     - | Only used in ``columns`` to specify both 10m wind
       | speed and direction at once.
     -
     - L

   * - wind10m_speed
     - m/s
     - 10m wind speed, cannot be used in ``columns``
     -
     - L

   * - wind10m_dir
     - deg
     - 10m wind direction, cannot be used in ``columns``
     -
     - L

   * - max_wgust
     -
     - | Only used in ``columns`` to specify both the
       | maximum wind gust speed and direction at once.
     - P
     - L

   * - max_wgust_speed
     - m/s
     - | Maximum wind gust speed in a period,
       | cannot be used in ``columns``
     - P
     - L

   * - max_wgust_dir
     - deg
     - | Maximum gust direction in a period,
       | cannot be used in ``columns``
     - P
     - L

   * - visibility
     - m
     - Visibility
     -
     -

   * - present_weather
     -
     - Present weather
     -
     -

   * - past_weather_1
     -
     - Past weather 1
     - P
     -

   * - past_weather_2
     -
     - Past weather 2
     - P
     -

   * - cloud_cover
     - %
     - Total cloud cover (0-100)
     -
     -

   * - max_t2m
     - K
     - Maximum 2m temperature over a period
     - P
     - L

   * - min_t2m
     - K
     - Minimum 2m temperature over a period
     - P
     - L

   * - precipitation
     - kg m-2
     - Precipitation over a period
     - P
     - L

   * - snow_depth
     - m
     - Snow depth
     -
     -

.. _synop-extra-obs-params:

Additional observed parameters
////////////////////////////////////

These parameters are not added by default but can be specified in ``columns``.

.. list-table:: P: means has a period, L: means has a level
   :header-rows: 1
   :widths: 10 10 60 10 10
   :align: center

   * - Name
     - Units
     - Description
     - P
     - L

   * - q2m
     - kg/kg
     - 2m specific humidity
     -
     - L

   * - pressure_change
     - Pa
     - Pressure change in a period
     - P
     -

   * - char_pressure_tendency
     -
     - Characteristic of pressure tendency
     -
     -

   * - lw_radiation
     - J m-2
     - | Longwave radiation integrated over
       | a period
     - P
     - L

   * - sw_radiation
     - J m-2
     - | Shortwave radiation integrated over
       | a period
     - P
     -

   * - net_radiation
     - J m-2
     - | Net radiation integrated over
       | a period
     - P
     -

   * - global_solar_radiation
     - J m-2
     - | Global solar radiation integrated over
       | a period
     - P
     -

   * - diffuse_solar_radiation
     - J m-2
     - | Diffuse solar radiation integrated over
       | a period
     - P
     -

   * - direct_solar_radiation
     - J m-2
     - | Direct solar radiation integrated over
       | a period
     - P
     -

   * - total_sunshine_duration
     - min
     - | Total sunshine duration over
       | a period
     - P
     -

.. _synop-filters:

Parameter filters
+++++++++++++++++++++

Parameter names can be used in ``filters``. For the filter syntax see :ref:`filters`.

.. warning::

    The individual conditions in ``filters`` are combined together with the logical AND operator. So if any condition fails to match then the whole station/platform will be omitted from the results.


Filtering parameter values
////////////////////////////

.. code-block:: python

    # accepting stations with 2m temperature > 273.15 K
    filters = {"t2m": slice(273.15, None)}


.. Filtering parameter levels
.. ////////////////////////////////////

.. When a parameter has an associated level (see the "Has level" column in :ref:`synop-obs-param`) this can be used in a filter. We can refer to level by adding the "_level" suffix to the parameter name.

.. .. code-block:: python

..     # accepting stations with 2m temperature observed exactly at 2m
..     filters = {"t2m_level": 2}

..     # accepting stations with 2m temperature observed in the height range of 1.5m to 2.5m
..     filters = {"t2m_level": slice(1.5, 2.5)}

..     # accepting stations with 10m wind observed exactly at 10m
..     filters = {"wind10m_level": 10}

..     # accepting stations with 10m wind observed in the height range of 9.5m to 11.5m
..     filters = {"wind10m_level": slice(9.5, 11.5)}

..     # accepting stations with wind gust observations in the height range of 9.5m to 11.5m
..     filters = {"wind_gust_level": slice(9.5, 11.5)}


Examples
++++++++++++++++++++++++++++

 - :ref:`/examples/r_synop_overview.ipynb`
