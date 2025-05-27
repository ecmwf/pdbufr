.. _temp-reader:

.. warning::

    This reader is **experimental** and the API might change in the future. It is not recommended to use it in production code yet.

TEMP
-------------

.. py:function:: read_bufr(path, reader="temp", columns=[], filters=None, geopotential="geopotential", units_system=None, units=None, add_units_columns=False)

    Extract :ref:`temp-like data <temp-like-data>` from BUFR using pre-defined :ref:`parameters <temp-params>`.

    :param path: path to the BUFR file or a :ref:`message_list_object`
    :type path: str, bytes, os.PathLike or a :ref:`message_list_object`
    :param columns: specify the pre-defined :ref:`parameters <temp-params>` to extract. The possible values are as follows:

        - "default" or empty list: extract the parameters as in "station" followed by all the :ref:`upper level parameters <temp-default-obs-params>`. See ``geopotential`` for details on extracting the geopotential parameters.
        - "location": extract only the "lat" and "lon" parameters (see :ref:`station parameters <temp-station-params>` for details)
        - "geometry": extract only the "lat", "lon" and "elevation" parameters (see :ref:`station parameters <temp-station-params>` for details)
        - "station": extract only the "sid", "time", "lat", "lon" and "elevation" parameters (see :ref:`station parameters <temp-station-params>` for details)
        - "upper": extract only the :ref:`upper level parameters <temp-upper-params>`
        - when it is a non-empty list, specifies the :ref:`parameters <temp-params>` to extract. The keys "default", "location", "geometry", "station" and "upper" can all be part of the list and will add all the parameters from the corresponding group. No individual upper level parameters can be specified in the list, only the whole "upper" group can be extracted.

    :type columns: str, sequence[str]
    :param geopotential: define if the geopotential or/and geopotential height parameters should be extracted. The possible values are as follows:

        - "z": extract the geopotential parameter. If not available, it is computed from the geopotential height using the formula:

            .. math::

                z = zh \cdot g

          where :math:`zh` is the geopotential height and :math:`g` is the standard acceleration of gravity (9.80665 m/s²).
        - "zh": extract the geopotential height parameter. If only geopotential is available, it is converted to geopotential height using the formula:

            .. math::

                zh = \frac{z}{g}

          where :math:`z` is the geopotential and :math:`g` is the standard acceleration of gravity (9.80665 m/s²).
        - "both": extract both the geopotential and geopotential height parameters.
        - "any": extract either the geopotential or geopotential height parameter, depending on which one is available in the BUFR message/subset. If both are available, both are extracted.

    :type geopotential: str
    :param filters: define the conditions when to extract the data. The individual conditions are combined together with the logical AND operator to form the filter. It can contain both BUFR keys and parameters. See :ref:`filters-section` for details.
    :type filters: dict
    :param unit_system: define the unit system to generate the resulting values. The default is None, which means that no conversion is applied but the values/units found in the BUFR are written to the output. The only available unit system is: "default". The "default" system uses the units as defined in the :ref:`synop-obs-params` section.
    :type unit_system: str, None
    :param units: specify custom units conversions as a dictionary. The keys are the parameter names and the values are the units to convert to. For keys not specified the conversion defined by ``unit_system`` is applied. E.g.:

        .. code-block:: python

            units = {
                "t": "C",
            }

    :type units: dict, None
    :param add_units_columns: if True, a :ref:`units column <synop-units>` is added to the resulting DataFrame for each :ref:`parameter <synop-params>` having a units. The column name is formed by adding the "_units" suffix to the parameter name. The default is False.
    :type add_units: bool


.. _temp-like-data:

TEMP-like data
++++++++++++++++++++++++++++

For this reader the term "TEMP-like data" means data that is similar to classic radiosonde observations, and it contains all messages/subsets with ``dataCategory=2``. See details on the data category :ref:`here <bufr-data-category>`.


The resulting DataFrame
+++++++++++++++++++++++++

The resulting DataFrame will contain one row for each observed level. or each :ref:`parameter <synop-params>`. The columns are named after the parameter names, e.g. "t". The first columns are always the station/platform identifier, time, latitude, longitude and elevation. The observed parameters comes after the station parameters. E.g.::


        sid       lat        lon   elevation       time  p    t      td   ...
    0  91948 -23.13017 -134.96533       91.0 2020-03-15     300.45    73   ...
    1  11766  49.77722   17.54194      748.1 2020-03-15     269.25    65   ...


.. _temp-units:

Units
/////////////////////

When ``add_units_columns=True`` and a parameter has an associated **units** a separate column is created for the units. The column name is formed by adding the "_units" suffix to the parameter name::

        t2m       t2m_units
    0   273.15       K
    1   274.15       K


.. _temp-params:

Parameters
+++++++++++++++++++++

A parameter is a high-level concept in ``pdbufr``. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. When using parameters lwe do not need to know the actual encoding, but the desired value is automatically extracted.


SYNOP parameters can be divided into three groups:

- `station/platform related parameters <temp-station-params>`_,
- `upper parameters <synop-upper-params>`_,

.. _temp-station-params:

Station/platform params
////////////////////////////

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
       | "shipOrMobileLandStationIdentifier", "station_id",
       | "stationOrSiteName", "station_id"
       | and "icaoLocationIndicator".

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


.. _temp-upper-params:

Upper level parameters
/////////////////////

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: center

   * - **Name**
     - **Units**
     - **Description**

   * - pressure
     - Pa
     - Pressure

   * - z
     - m2 s-2
     - Geopotential

   * - zh
     - gpm
     - Geopotential height

   * - t
     - K
     - Temperature

   * - td
     - K
     - Dew point temperature

   * - wind_speed
     - m/s
     - Wind speed

   * - wind_dir
     - deg
     - Wind direction



.. _temp-filters:

Parameter filters
+++++++++++++++++++++

Parameter names and levels can be used in ``filters``. For the filter syntax see :ref:`filters-section`.

.. warning::

    The individual conditions in ``filters`` are combined together with the logical AND operator. So if any condition fails to match then the whole station/platform will be omitted from the results.


Filtering parameter values
////////////////////////////

.. code-block:: python

    # accepting pressure level where t temperature > 243.15 K
    filters = {"t2m": slice(243.15, None)}
