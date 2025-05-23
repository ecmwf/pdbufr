.. _synop-reader:

SYNOP
-------------

.. py:function:: read_bufr(path, reader="synop", columns=[], filters=None, units_system=None, units=None, add_units_columns=False, add_level_columns=False)

    Extract **SYNOP/SHIP** data from BUFR using pre-defined :ref:`parameters <synop-params>`.

    :param path: path to the BUFR file or a :ref:`message_list_object`
    :type path: str, bytes, os.PathLike or a :ref:`message_list_object`
    :param columns: specify the pre-defined parameters to extract. The possible values are as follows:

        - "all" or empty list: extract both the :ref:`station parameters <synop-station-params>` and the  :ref:`observed parameters <synop-obs-params>`
        - "location": extract only the "lat" and "lon" parameters (see: :ref:`station parameters <synop-station-params>` for details)
        - "geometry": extract only the "lat", "lon" and "elevation" parameters (see :ref:`station parameters <synop-station-params>` for details)
        - "station": extract only the :ref:`station parameters <synop-station-params>` ("sid", "time", "lat", "lon" and "elevation")
        - when it is a non-empty list, specifies the :ref:`observed parameters <synop-obs-params>` to extract on top of the :ref:`station parameters <synop-station-params>`, which are always extracted.

    :type columns: str, sequence[str]
    :param filters: define the conditions when to extract the data. The individual conditions are combined together with the logical AND operator to form the filter. It can contain both BUFR keys and parameters. See :ref:`filters-section` for details.
    :type filters: dict
    :param unit_system: define the unit system to generate the resulting values. The default is None, which means that no conversion is applied but the values/units found in the BUFR are written to the output. The available unit systems are: "default" and "si". The "default" system uses the units as defined in the :ref:`synop-obs-params` section.
    :type unit_system: str, None
    :param units: specify custom units conversions as a dictionary. The keys are the parameter names and the values are the units to convert to. For keys not specified the conversion defined by ``unit_system`` is applied. E.g.:

        .. code-block:: python

            units = {
                "t2m": "C",
                "mslp": "hPa",
            }

    :type units: dict, None
    :param add_units_columns: if True, a :ref:`units column <synop-units>` is added to the resulting DataFrame for each :ref:`parameter <synop-params>` having a units. The column name is formed by adding the "_units" suffix to the parameter name. The default is False.
    :type add_units: bool
    :param add_level_columns: if True, a :ref:`level column <synop-levels>` is added to the resulting DataFrame for each :ref:`parameter <synop-params>` having a level. The column name is formed by adding the "_level" suffix to the parameter name. The default is False.
    :rtype: pandas.DataFrame


The resulting DataFrame
+++++++++++++++++++++++++

The resulting DataFrame will contain one row for each station/platform and one column for each :ref:`parameter <synop-params>`. The columns are named after the parameter names, e.g. "t2m". The first colums are always the station/platform identifier, time, latitude, longitude and elevation. The observed parameters comes after the station parameters. E.g.::


        sid       lat        lon   elevation       time     t2m  rh2m   ...
    0  91948 -23.13017 -134.96533       91.0 2020-03-15  300.45    73   ...
    1  11766  49.77722   17.54194      748.1 2020-03-15  269.25    65   ...


.. _synop-periods:

Periods
/////////////////////

When a parameter is associated with a **time period** for each period a separate column is created with the period being encoded into the column name. E.g. if windgust is available for both the last 10 minutes and the last 1 hour, the resulting DataFrame will contain two columns: "wind_gust_10min" and "wind_gust_1h"::

            wind_gust_10min  wind_gust_1h
    0               5.0            6.0
    1               4.5            5.5

The period string is constructed from the values encoded in the BUFR message. When the period is not available the "_nan" suffix is used, e.d. "wind_gust_nan".

.. _synop-levels:

Levels
/////////////////////

When ``add_level_columns=True`` and a parameter is associated with a **height level** a separate column is created for the level value. The column name is formed by adding the "_level" suffix to the parameter name::

        t2m       t2m_level
    0   273.15       2.0
    1   274.15       2.5

.. _synop-units:

Units
/////////////////////

When ``add_units_columns=True`` and a parameter has an associated **units** a separate column is created for the units. The column name is formed by adding the "_units" suffix to the parameter name::

        t2m       t2m_units
    0   273.15       K
    1   274.15       K

Periods and levels
/////////////////////

When both periods and levels are available and ``add_level_columns=True`` the column names are formed as follows::

            wind_gust_10min  wind_gust_10min_level   wind_gust_1h   wind_gust_1h_level
    0               5.0              9.6                   6.0            10.5
    1               4.5              9.6                   5.5            10.3


.. _synop-params:

Parameters
+++++++++++++++++++++

A parameter is a high-level concept in ``pdbufr`` to represent data extracted from BUFR. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. E.g. 2m temperature can be present as "airTemperatureAt2M" or as "airTemperature" inside a group of "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform=2". When using a parameters like "t2m" we do not need to know the actual encoding the desired value is automatically extracted.

SYNOP parameters can be divided into two groups: ``station parameters`` and ``observed parameters``. The station parameters are always extracted, while the observed parameters are optional.

.. _synop-station-params:

Station params
///////////////////

These parameters are alway extracted.

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: center

   * - **Name**
     - **Units/Object**
     - **Description**


   * - sid
     -
     - | Station/platform identifier. The following keys are tried
       | in order to generate the value:
       | :ref:`WMO station id <key_wmo_station_id>`, :ref:`WIGOS station id <key_WIGOS_station_id>`,
       | "shipOrMobileLandStationIdentifier" and "station_id".

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


.. _synop-obs-params:

Observed parameters
/////////////////////

These parameters are optional.

.. list-table::
   :header-rows: 1
   :widths: 10 10 70 10
   :align: center

   * - **Name**
     - **Units**
     - **Description**
     - **Has level**

   * - t2m
     - K
     - 2m temperature
     - yes

   * - td2m
     - K
     - 2m dew point temperature
     - yes

   * - rh2m
     - %
     - 2m relative humidity (0-100)
     - yes

   * - mslp
     - Pa
     - Mean sea level pressure
     - no

   * - wind10m_speed
     - m/s
     - 10m wind speed
     - yes

   * - wind10m_dir
     - deg
     - 10m wind direction
     - yes

   * - wgust_speed
     - m/s
     - Maximum wind gust speed
     - yes

   * - wgust_dir
     - deg
     - Maximum gust direction
     - yes

   * - visibility
     - m
     - Visibility
     - no

   * - present_weather
     -
     - Present weather
     - no

   * - past_weather_1
     -
     - Past weather 1
     - no

   * - past_weather_2
     -
     - Past weather 2
     - no

   * - cloud_cover
     - %
     - Total cloud cover (0-100)
     - no

   * - max_t2m
     - K
     - Maximum 2m temperature
     - yes

   * - min_t2m
     - K
     - Minimum 2m temperature
     - yes

   * - precipitation
     - kg m-2
     - Precipitation
     - no

   * - snow_depth
     - m
     - Snow depth
     - no


.. _synop-filters:

Parameter filters
+++++++++++++++++++++

Parameter names and levels can be used in ``filters``. For the filter syntax see :ref:`filters-section`.

.. warning::

    The individual conditions in ``filters`` are combined together with the logical AND operator. So if any condition fails to match then the whole station/platform will be omitted from the results.


Filtering parameter values
////////////////////////////

.. code-block:: python

    # accepting station where 2m temperature > 273.15 K
    filters = {"t2m": slice(273.15, None)}


Filtering parameter levels
////////////////////////////////////

When a parameter has an associated level (see the "Has level" column in :ref:`synop-obs-param`) this can be used in a filter. We can refer to level by adding the "_level" suffix to the parameter name.

.. code-block:: python

    # accepting station with 2m temperature observed exactly at 2m
    filters = {"t2m_level": 2}

    # accepting station with 2m temperature observed in the height range of 1.5m to 2.5m
    filters = {"t2m_level": slice(1.5, 2.5)}

    # accepting station with 10m wind observed exactly at 10m
    filters = {"wind10m_level": 10}

    # accepting station with 10m wind observed in the height range of 9.5m to 11.5m
    filters = {"wind10m_level": slice(9.5, 11.5)}

    # accepting station with wind gust observations in the height range of 9.5m to 11.5m
    filters = {"wind_gust_level": slice(9.5, 11.5)}
