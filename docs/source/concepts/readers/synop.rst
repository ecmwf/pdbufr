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

Periods ending before the observation time
//////////////////////////////////////////

A period does not always end at the observation time: the maximum temperature reported at 12 UTC can be the maximum of the previous calendar day. Such periods are encoded with **two consecutive** time period descriptors: the first one is the start of the period and the second one is its end, both counted back from the observation time. The second value is 0 when the period ends at the observation time. This is the rule for the extreme temperatures in the SYNOP land template TM 307080; see WMO-No. 306, Manual on Codes Volume I.2, regulation B/C1.10.4.2 "Periods of reference for extreme temperatures", Notes (1) and (2) (the same rule is repeated for the mobile land (B/C5) and ship (B/C10) reports).

The column is named by the **duration** of the period and, when the period does not end at the observation time, the offset of its end from the observation time is appended as "_end" plus that offset with its units. E.g. the pair -12/0 is the 12 hours ending at the observation time::

      stnid  max_t2m_12h  min_t2m_12h
    0  8495       291.49       289.89

(``tests/sample_data/synop_0_74_M32.bufr``, ``columns=["stnid", "max_t2m", "min_t2m"]``), while the pair -30/-6 is the 24 hours ending 6 hours before the observation time::

      stnid  max_t2m_24h_end6h  min_t2m_24h_end6h
    0  8495             291.49             289.89

(``tests/sample_data/synop_period_end_offset.bufr``, the same values with the pairs changed to -30/-6).

Only two consecutive time period descriptors are a start/end pair. Two periods separated by another data element (for example a time significance) are two independent periods, and the replications of a sequence (the 1/3/6/12/24 hour precipitation, the 1/24 hour sunshine and radiation, the 10/60/360 minute gust) are separate periods as well, never a pair.

Messages that do not follow the WMO regulations and encode a period as a positive displacement are read by its absolute value, so a column name never contains a "-". E.g. the corrupt ``tests/sample_data/synop_0_231_M15.bufr`` reports a gust period of 1448::

       stnid  max_wgust_speed_1448min
    0  26029                     25.5

Sensor heights
///////////////

Several sensors can report the same parameter for the same period. When that happens the value of the sensor closest to the **nominal height** of the parameter is used: 2 m for the maximum/minimum 2 m temperature and 10 m for the wind gust. For the 2 m temperatures the sensors below 0.5 m (a ground or grass sensor) are ignored. A value reported without a sensor height is still used, but a value from a sensor with a known (eligible) height takes precedence. A reported value always wins over a missing one, and it keeps its own level and units.

E.g. ``tests/sample_data/synop_172_98_M29.bufr`` reports the same 60 minute minimum twice, 275.45 K at 2 m and 274.95 K at 0.05 m. The ground sensor is ignored and the 2 m value is reported with its own height (``columns=["stnid", "min_t2m"]``, ``level_columns=True``)::

       stnid  min_t2m_60min  min_t2m_60min_level
    0  12805         275.45                  2.0

.. note::

    The height selection works within each BUFR encoding of a parameter. Two cases are not handled, and neither occurs in the sample data used for testing: a ground sensor whose height is given only as "heightAboveStation" is not ignored; and when the same 2 m temperature period is reported by two different BUFR elements in one message (e.g. "minimumTemperatureAtHeightAndOverPeriodSpecified" and "minimumTemperatureAtHeightSpecifiedPast12Hours"), the later one is used, not the one closest to 2 m.

Values without a period
////////////////////////

A parameter can be reported without a time period. The value is then written into the column named after the parameter alone, without a period suffix, e.g. "precipitation". The "_nan" suffix used for a missing period in earlier versions of the reader no longer occurs.

E.g. ``tests/sample_data/synop_0_212_M14.bufr`` reports the precipitation twice, once for a 3 hour period and once without a period (``columns=["stnid", "precipitation"]``)::

      stnid  precipitation  precipitation_3h precipitation_24h
    0  8534            0.0               0.0              None

When both the value and the period are missing no period column is created at all; the plain column may still appear, filled with None, as the generic result of a requested parameter that was not found (in the example above the ``max_t2m`` and ``min_t2m`` columns of this file are None). Conversely, when the period is known but the value is missing, the suffixed column may appear filled with None, e.g. ``max_t2m_12h`` in ``tests/sample_data/synop_176_98_M29.bufr``.

.. _synop-levels:

Levels
/////////////////////

When ``level_columns=True`` and a parameter is associated with a **height level** a separate column is created for the level value. The column name is formed by adding the "_level" suffix to the parameter name::

       stnid     t2m  t2m_level
    0  91948  300.45        1.5
    1  11766  269.25        2.0
    2  56257  276.35        1.5

(``tests/sample_data/syn_new.bufr``, ``columns=["stnid", "t2m"]``, ``level_columns=True``)

.. _synop-units:

Units
/////////////////////

When ``units_columns=True`` and a parameter has an associated **units** a separate column is created for the units. The column name is formed by adding the "_units" suffix to the parameter name::

       stnid     t2m t2m_units
    0  91948  300.45         K
    1  11766  269.25         K
    2  56257  276.35         K

(``tests/sample_data/syn_new.bufr``, ``columns=["stnid", "t2m"]``, ``units_columns=True``)

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
     - | Cloud type at low level (CL), taken from the
       | cloud summary group
     -
     -

   * - cloud_type_middle
     -
     - | Cloud type at middle level (CM), taken from the
       | cloud summary group
     -
     -

   * - cloud_type_high
     -
     - | Cloud type at high level (CH), taken from the
       | cloud summary group
     -
     -

   * - cloud_amount_nh
     -
     - | Cloud amount of the low cloud (Nh), or of the middle cloud when
       | no low cloud is reported, as a raw code table 020011 value
     -
     -

   * - cloud_base_lowest
     - m
     - Height of the base of the lowest cloud, taken from the cloud summary group
     -
     -

The cloud summary columns are extracted from the cloud group with
``verticalSignificanceSurfaceObservations`` = 7 ("low cloud" in WMO Code Table 0 08 002).
When a subset has no such group, its first cloud group is used only if its vertical
significance is missing (e.g. template 307092) or 0 (in SYNOP reports 0 means that the group
follows the SYNOP rules and describes the lowest cloud base and the cloud types). The groups
with vertical significance 1-6 are individual cloud layers and never fill these columns.
The cloud types are raw WMO Code Table 0 20 001 values, assigned positionally to the CL, CM,
CH columns in the order they are reported, and ``cloud_amount_nh`` is a raw Code Table 0 20 011
value (e.g. 2 = two oktas, 8 = overcast, 9 = sky obscured), not a percentage.

Only ``cloud_base_lowest`` has associated units: the BUFR units of its ``heightOfBaseOfCloud``
key, which are metres ("m"). Like the other parameters with units, it gets a
``cloud_base_lowest_units`` column when ``units_columns=True`` and its values are unit converted
when ``unit_system`` or ``units`` requests a conversion. The cloud types and
``cloud_amount_nh`` are code table values without units: no "_units" column is created for
them, even when ``units_columns=True``, and their values are never unit converted, even when
``unit_system`` or ``units`` requests a conversion.

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
- :ref:`/tutorials/synop/r_synop_cloud.ipynb`
