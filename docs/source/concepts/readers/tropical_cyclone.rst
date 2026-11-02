.. _tropical-cyclone-reader:

Tropical cyclone
-----------------------

.. warning::

    This reader is **experimental** and the API might change in the future. It is not recommended to use it in production code yet.

*New in version 0.16.0*

.. py:function:: read_bufr(path, reader="tropical-cyclone", columns=[], filters=None, keep_missing=False, unit_system=None, units=None, units_columns=False, prefilter_headers=False)
    :noindex:

    Extract :ref:`tropical cyclone track data <tropical-cyclone-data>` from BUFR using pre-defined :ref:`parameters <tropical-cyclone-params>`. The reader name can also be specified as "tropical_cyclone".

    :param path: path to the BUFR file or a :ref:`message list object <message-list-object>`
    :type path: str, bytes, os.PathLike or a :ref:`message list object <message-list-object>`
    :param columns: specify the pre-defined :ref:`parameters <tropical-cyclone-params>` to extract. The possible values are as follows:

        - "default" or empty list: extract the :ref:`default parameters <tropical-cyclone-default-params>`
        - "wind_radii": extract the :ref:`wind radii parameters <tropical-cyclone-optional-params>` (all 12 of them)
        - "all": extract all the :ref:`default <tropical-cyclone-default-params>` and :ref:`optional <tropical-cyclone-optional-params>` parameters
        - the name of a single parameter (see :ref:`tropical-cyclone-params`)
        - when it is a list, it can contain any combination of the keys above, e.g. ``["default", "wind_radii"]`` or ``["default", "observed_lat", "observed_lon"]``. The keys "default", "wind_radii" and "all" will add all the parameters from the corresponding group.

        The order of the columns in the resulting DataFrame is fixed (see :ref:`tropical-cyclone-params`), it does not depend on the order of the items in ``columns``. An unknown name raises a ValueError.

    :type columns: str, sequence[str]
    :param filters: define the conditions when to extract the data. The individual conditions are combined together with the logical AND operator to form the filter. The keys can be the :ref:`parameter names <tropical-cyclone-params>` (whether they are selected in ``columns`` or not) and "count". See :ref:`tropical-cyclone-filters` and :ref:`filters` for details.
    :type filters: dict
    :param keep_missing: if False (the default), the steps without a valid centre position (``lat`` or ``lon`` is missing, e.g. because the track of the storm has ended) are dropped from the results. If True, these steps are kept and the missing values are set to NaN.
    :type keep_missing: bool
    :param unit_system: define the unit system to generate the resulting values. The default is None, which means that no conversion is applied but the values/units found in the BUFR are written to the output. The available unit systems are: "pdbufr" and "si". The "pdbufr" system uses the units as defined in the :ref:`tropical-cyclone-params` section. The "si" system converts the values to SI base units, so it converts ``lat``, ``lon``, ``max_wind_lat``, ``max_wind_lon``, ``observed_lat`` and ``observed_lon`` to radians. The values of the other parameters (``mslp``, ``max_wind_speed`` and the wind radii) are numerically unchanged, but the unit of ``mslp`` is written as base units ("kg / m / s ** 2").
    :type unit_system: str, None
    :param units: specify custom units conversions as a dictionary. The keys are the parameter names and the values are the units to convert to. For keys not specified the conversion defined by ``unit_system`` is applied. E.g.:

        .. code-block:: python

            units = {
                "mslp": "hPa",
                "max_wind_speed": "knot",
            }

    :type units: dict, None
    :param units_columns: if True, a :ref:`units column <tropical-cyclone-units>` is added to the resulting DataFrame for each :ref:`parameter <tropical-cyclone-params>` having a units. The column name is formed by adding the "_units" suffix to the parameter name. The default is False.
    :type units_columns: bool
    :param prefilter_headers: accepted for consistency with the other readers, but for this reader it gives no speed-up. The ``filters`` of this reader use :ref:`parameter names <tropical-cyclone-params>`, which are not BUFR header keys, so there is nothing to match before unpacking. Only :ref:`tropical cyclone track data <tropical-cyclone-data>` is supported, i.e. messages with ``dataCategory=7``, ``dataSubCategory=32`` and ``bufrHeaderCentre=98``; all other messages are ignored. Whatever the value of this option, the three header keys are checked before unpacking and a message that does not match is skipped without raising an error.
    :type prefilter_headers: bool


.. _tropical-cyclone-data:

Tropical cyclone track data
+++++++++++++++++++++++++++++++

For this reader the term "tropical cyclone track data" means the tropical cyclone tracks produced by ECMWF. The only input supported is messages with ``dataCategory=7``, ``dataSubCategory=32`` and ``bufrHeaderCentre=98``; all the other messages are silently ignored. See details on these header keys :ref:`here <bufr-data-category>`.

The data is structured as follows:

- each message describes one storm,
- each subset of the message describes one ensemble member. The subsets are either stored in a compressed message with multiple subsets or in uncompressed messages with a single subset,
- each subset contains the analysis (step 0) followed by the forecast steps. The steps are given by the ``timePeriod`` key in hours.

Two layouts of the data are supported:

- the current layout, which follows the WMO BUFR template 3 16 082. It is used in the ECMWF open data "tf" files, e.g. ``https://data.ecmwf.int/forecasts/YYYYMMDD/00z/ifs/0p25/enfo/YYYYMMDD000000-360h-enfo-tf.bufr``. In addition to the storm centre, the pressure and the maximum wind it also contains the :ref:`wind radii <tropical-cyclone-optional-params>` at the 18, 26 and 33 m/s thresholds in the four quadrants (NE, SE, SW, NW).
- the older ECMWF layout, which has no wind radii. For this layout all the wind radii parameters are missing (NaN).

At step 0 the position of the storm centre (``lat`` and ``lon``) is the position of the model analysis (the perturbed analysis for the ensemble members, the analysis for the control), and **not** the observed position. The observed position of the storm centre is available in the optional ``observed_lat`` and ``observed_lon`` parameters. They have the same value for all the steps of a given member.


The resulting DataFrame
+++++++++++++++++++++++++

The resulting DataFrame will contain one row for each storm, ensemble member and step, and one column per each :ref:`parameter <tropical-cyclone-params>`. The columns are named after the parameter names, e.g. "mslp". With the default settings the first columns are the storm identifier, the storm name, the ensemble member number, the base time, the step and the valid time followed by the position of the storm centre, the pressure and the maximum wind parameters. The ``step`` is an integer in hours, where 0 is the analysis. The ``valid_time`` is ``base_time`` plus ``step`` hours. E.g.::

      storm_id storm_name  member           base_time  step          valid_time   lat    lon      mslp  max_wind_lat  max_wind_lon  max_wind_speed
    0     04W       ...        0 2025-08-01 00:00:00     0 2025-08-01 00:00:00  ...    ...     ...         ...           ...         ...
    1     04W       ...        0 2025-08-01 00:00:00     6 2025-08-01 06:00:00  ...    ...     ...         ...           ...         ...

By default, the steps without a storm centre position (i.e. when the track has ended) are dropped. Use ``keep_missing=True`` to keep them.


.. _tropical-cyclone-units:

Units
/////////////////////

When ``units_columns=True`` and a parameter has an associated **units** a separate column is created for the units, which is placed right after the column of the parameter. The column name is formed by adding the "_units" suffix to the parameter name::

         mslp  mslp_units
    0   99800          Pa
    1   99500          Pa

The units can be changed with ``unit_system`` and ``units``. When ``unit_system`` or ``units`` is specified the values of the parameters having a units are converted to the target units and the "_units" columns contain the target units.

.. note::

    With ``unit_system="si"`` the longitude and latitude parameters are converted to radians.


.. _tropical-cyclone-params:

Parameters
+++++++++++++++++++++

A parameter is a high-level concept in ``pdbufr``. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. When using parameters we do not need to know the actual encoding, but the desired value is automatically extracted.

The parameters are divided into two groups:

- :ref:`default parameters <tropical-cyclone-default-params>`,
- :ref:`optional parameters <tropical-cyclone-optional-params>`.

In the resulting DataFrame the columns are always in the order given in the tables below (default parameters first), whatever the order specified in ``columns``.

.. _tropical-cyclone-default-params:

Default parameters
////////////////////////////

These parameters are extracted when ``columns`` is empty or contains "default".

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: left

   * - **Name**
     - **Units/Object**
     - **Description**

   * - storm_id
     - str
     - Storm identifier (BUFR key: ``stormIdentifier``)

   * - storm_name
     - str
     - Storm name (BUFR key: ``longStormName``)

   * - member
     - int
     - Ensemble member number (BUFR key: ``ensembleMemberNumber``)

   * - base_time
     - datetime.datetime
     - Base (analysis) time of the forecast

   * - step
     - int (hours)
     - Forecast step in hours. Step 0 is the analysis.

   * - valid_time
     - datetime.datetime
     - Valid time of the step. It is ``base_time`` plus ``step`` hours.

   * - lat
     - deg
     - Latitude of the storm centre. At step 0 it is the position of the model analysis.

   * - lon
     - deg
     - Longitude of the storm centre. At step 0 it is the position of the model analysis.

   * - mslp
     - Pa
     - Pressure reduced to mean sea level at the storm centre

   * - max_wind_lat
     - deg
     - Latitude of the maximum wind

   * - max_wind_lon
     - deg
     - Longitude of the maximum wind

   * - max_wind_speed
     - m/s
     - Maximum 10 m wind speed


.. _tropical-cyclone-optional-params:

Optional parameters
////////////////////////////

These parameters are only extracted when requested in ``columns`` (individually, as the "wind_radii" group, or with "all"). The wind radii are the effective radii with respect to the wind speed thresholds of 18, 26 and 33 m/s in the NE, SE, SW and NW quadrants. They are only available in the current (WMO template 3 16 082) layout, and are missing for the older ECMWF layout.

.. list-table::
   :header-rows: 1
   :widths: 10 10 80
   :align: left

   * - **Name**
     - **Units/Object**
     - **Description**

   * - radius_18ms_ne, radius_18ms_se, radius_18ms_sw, radius_18ms_nw
     - m
     - Radius of the 18 m/s wind in the NE, SE, SW and NW quadrants (group "wind_radii")

   * - radius_26ms_ne, radius_26ms_se, radius_26ms_sw, radius_26ms_nw
     - m
     - Radius of the 26 m/s wind in the NE, SE, SW and NW quadrants (group "wind_radii")

   * - radius_33ms_ne, radius_33ms_se, radius_33ms_sw, radius_33ms_nw
     - m
     - Radius of the 33 m/s wind in the NE, SE, SW and NW quadrants (group "wind_radii")

   * - observed_lat
     - deg
     - Latitude of the observed storm centre. It is the same for all the steps of a member.

   * - observed_lon
     - deg
     - Longitude of the observed storm centre. It is the same for all the steps of a member.

   * - forecast_type
     - int
     - Ensemble forecast type code (BUFR key: ``ensembleForecastType``)


.. _tropical-cyclone-filters:

Parameter filters
+++++++++++++++++++++

Parameter names can be used in ``filters``, whether the parameter is selected in ``columns`` or not. In addition to the parameter names the key "count" can be used to filter on the (1-based) index of the message in the input. For the filter syntax see :ref:`filters`. A slice is inclusive on both ends.

The conditions are matched against the values as they appear in the output, so after the units conversion. E.g. when ``unit_system="si"`` the conditions on ``lat`` have to be given in radians.

.. warning::

    The individual conditions in ``filters`` are combined together with the logical AND operator. Conditions on ``storm_id``, ``storm_name`` and ``base_time`` select storms, conditions on ``member``, ``forecast_type``, ``observed_lat`` and ``observed_lon`` select ensemble members, while conditions on all the other parameters select individual rows (steps).

.. warning::

    BUFR keys cannot be used in ``filters``, only the parameter names and "count". Using an unknown key raises a ValueError. For some BUFR keys the error message suggests the parameter to use, e.g. "stormIdentifier" -> "storm_id", "longStormName" -> "storm_name", "ensembleMemberNumber" -> "member", "ensembleForecastType" -> "forecast_type" and "timePeriod" -> "step".


Filtering parameter values
////////////////////////////

.. code-block:: python

    # selecting the control forecast (member 0) of a storm
    filters = {"storm_id": "04W", "member": 0}

    # selecting the steps up to 72 hours (inclusive)
    filters = {"step": slice(0, 72)}

    # selecting the steps where the central pressure is below 98000 Pa
    filters = {"mslp": slice(None, 98000)}

    # selecting the first message only
    filters = {"count": 1}


Examples
++++++++++++++++++++++++++++

The following example extracts the default parameters and the wind radii for the first 72 hours of a storm from an ECMWF open data "tf" file (current layout):

.. code-block:: python

    import pdbufr

    df = pdbufr.read_bufr(
        "20250801000000-360h-enfo-tf.bufr",
        reader="tropical-cyclone",
        columns=["default", "wind_radii"],
        filters={"storm_id": "04W", "step": slice(0, 72)},
    )

- :ref:`tropical-cyclone-tutorial`
