.. _synop-reader:

Synop
-------------

.. warning::

    This reader is **experimental** and the API might change in the future. It is not recommended to use it in production code yet.


*New in version 0.13.0*

.. py:function:: read_bufr(path, reader="synop", columns=[], filters=None, stnid_keys=None, units_system=None, units=None, units_columns=False, level_columns=False, prefilter_headers=False)
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
    :param prefilter_headers: if True, the headers are filtered before unpacking the data section. This can significantly speed up the extraction when the ``filters`` contain header keys (and only a small fraction of messages/subsets matches). *New in version 0.15.0.*
    :type prefilter_headers: bool
    :rtype: pandas.DataFrame


.. _synop-like-data:

SYNOP-like data
++++++++++++++++++++++++++++

In the context of this reader the term "SYNOP-like" means data that is similar to SYNOP/SHIP observations, and it contains all messages/subsets with ``dataCategory`` either  0 (land) or 1 (sea). See details on the data category :ref:`here <bufr-data-category>`. Note that this also contains observations e.g. buoys, which might not fit into this category. This will be revisited in the future.


The resulting DataFrame
+++++++++++++++++++++++++

The resulting DataFrame will contain one row for each station/platform and one column for each :ref:`parameter <synop-params>`. The columns are named after the parameter names, e.g. "t2m". With the default settings the first columns are always the station/platform identifier, time, latitude, longitude and elevation followed by the observed parameters. E.g. the first parameters of ``tests/sample_data/syn_new.bufr``::

       stnid       lat        lon  elevation       time     t2m  rh2m
    0  91948 -23.13017 -134.96533       91.0 2020-03-15  300.45    73
    1  11766  49.77722   17.54194      748.1 2020-03-15  269.25    65
    2  56257  30.00000  100.27000     3950.0 2020-03-15  276.35    37

All the examples below were generated from the files in ``tests/sample_data``.

.. _synop-periods:

Periods
/////////////////////

Some parameters are only meaningful together with a **time period**: a maximum temperature is the highest value measured during a period, a precipitation amount is what accumulated during a period. For every period found in the message a separate column is created, with the period encoded into the column name.

A period is named by its **duration** followed by the units ecCodes reports for the BUFR time period descriptor, i.e. "h" for a period in hours and "min" for a period in minutes. E.g. ``tests/sample_data/synop_150_85_M22.bufr`` reports the maximum wind gust for the last 10 minutes, the last hour and the last 6 hours. Reading it with ``columns=["stnid", "max_wgust_speed"]`` gives one column per period::

      stnid  max_wgust_speed_10min  max_wgust_speed_60min  max_wgust_speed_360min
    0  7005                    5.6                    7.7                    12.9

Time periods are counted **backwards** from the observation time, so a single period of -12 hours describes the 12 hours ending at the observation time and is named "12h".

A parameter reported without a period is written to the plain column named after the parameter, e.g. "precipitation". A column can be None when no value was found for it.

.. _synop-period-lag:

Periods ending before the observation time
//////////////////////////////////////////

A period can end before the observation time, e.g. the maximum temperature reported at 12 UTC can be the maximum of the previous calendar day.

The column is named by the **duration** of the period with "_lag" and the offset of its end appended: ``_lag6h`` means the period ends 6 hours before the observation time. E.g. a 24 hour period ending 6 hours before the observation time is named "24h_lag6h"::

      stnid  max_t2m_24h_lag6h  min_t2m_24h_lag6h
    0  8495             291.49             289.89

*New in version 0.17.0.* In earlier versions only the first period of such a pair was used, which gave a wrong result.

Wrongly encoded periods
//////////////////////////

Some messages describe a period with the same start and end, e.g. -24 h/-24 h. This is not a valid start/end pair, so it is read as a single period counted back from the observation time and named by that value, e.g. "24h" (and never "0h_lag24h").

*New in version 0.17.0.* Earlier versions do not support this case.

.. _synop-levels:

Levels
/////////////////////

When ``level_columns=True`` and a parameter is associated with a **height level** a separate column is created for the level value. The column name is formed by adding the "_level" suffix to the parameter name::

       stnid     t2m  t2m_level
    0  91948  300.45        1.5
    1  11766  269.25        2.0
    2  56257  276.35        1.5

When several sensors report the same parameter for the same period, the value from the sensor closest to the **nominal height** (2 m for the maximum/minimum 2 m temperature, 10 m for the maximum wind gust) is used, and it keeps its own level. For the maximum/minimum 2 m temperature sensors below 0.5 m (e.g. a grass sensor) are ignored.

.. _synop-units:

Units
/////////////////////

When ``units_columns=True`` and a parameter has an associated **units** a separate column is created for the units. The column name is formed by adding the "_units" suffix to the parameter name::

       stnid     t2m t2m_units
    0  91948  300.45         K
    1  11766  269.25         K
    2  56257  276.35         K

Levels and units
/////////////////////

Options ``level_columns=True`` and ``units_columns=True`` can be used together. In this case both suffix columns are added::

       stnid     t2m t2m_units  t2m_level
    0  91948  300.45         K        1.5
    1  11766  269.25         K        2.0
    2  56257  276.35         K        1.5


Periods, levels and units
////////////////////////////

The "_level" and "_units" suffixes are added **after** the period, so they always follow the column of the value they describe. E.g. ``tests/sample_data/synop_0_74_M32.bufr`` with ``columns=["stnid", "max_t2m"]``, ``level_columns=True`` and ``units_columns=True``::

      stnid  max_t2m_12h max_t2m_12h_units  max_t2m_12h_level
    0  8495       291.49                 K               1.25

A "_level" or "_units" column is never created without the value column it belongs to.



.. _synop-params:

Parameters
+++++++++++++++++++++

A parameter is a high-level concept in ``pdbufr``. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. E.g. 2m temperature can be represented at least in 2 different ways:

  - as "airTemperatureAt2M"
  - as "airTemperature" instnide a group "heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform=2".

When using parameters like "t2m" we do not need to know the actual encoding, but the desired value is automatically extracted for us. Another advantage is that we can easily extract the observation periods, levels and units for each parameter, which is simply not possible with the :ref:`generic reader <flat-reader>`.

SYNOP parameters can be divided into three groups:

- :ref:`station/platform related parameters <synop-station-params>`,
- :ref:`default observed parameters <synop-default-obs-params>`,
- :ref:`additional observed parameters <synop-extra-obs-params>`.


.. _synop-station-params:

Station/platform params
////////////////////////////

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: left

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
   :align: left


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
   :align: left

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

   * - cloud_type_low
     -
     - Cloud type at low level (CL), see :ref:`synop-cloud-params`
     -
     -

   * - cloud_type_middle
     -
     - Cloud type at middle level (CM), see :ref:`synop-cloud-params`
     -
     -

   * - cloud_type_high
     -
     - Cloud type at high level (CH), see :ref:`synop-cloud-params`
     -
     -

   * - cloud_amount_nh
     -
     - Cloud amount (Nh), see :ref:`synop-cloud-params`
     -
     -

   * - cloud_base_lowest
     - m
     - Height of the base of the lowest cloud, see :ref:`synop-cloud-params`
     -
     -

.. _synop-cloud-params:

Cloud parameters
////////////////////////////////////

The following parameters describe the cloud summary of a report:

- ``cloud_type_low``, ``cloud_type_middle`` and ``cloud_type_high``: the cloud types CL, CM and CH. The values are raw WMO Code Table 0 20 001 values, assigned to the three columns in the order they are reported.
- ``cloud_amount_nh``: the cloud amount (Nh) of the low cloud, or of the middle cloud when no low cloud is reported. The value is a raw WMO Code Table 0 20 011 value, **not** a percentage (e.g. 2 = two oktas, 8 = overcast, 9 = sky obscured).
- ``cloud_base_lowest``: the height of the base of the lowest cloud in metres.

The values are taken from the cloud group with vertical significance 7 ("low cloud" in WMO Code Table 0 08 002). When there is no such group, the first cloud group is used if its vertical significance is missing or 0. Groups with vertical significance 1-6 are individual cloud layers and are never used for these parameters.

Only ``cloud_base_lowest`` has units. Like the other parameters with units, it gets a ``cloud_base_lowest_units`` column when ``units_columns=True`` and it is converted when ``unit_system`` or ``units`` requests a conversion. The other cloud parameters are code table values: they never get a "_units" column and are never converted.

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

- :ref:`/tutorials/synop/r_synop_overview.ipynb`
- :ref:`/tutorials/synop/r_synop_periods_levels.ipynb`
- :ref:`/tutorials/synop/r_synop_cloud.ipynb`
