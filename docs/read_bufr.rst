read_bufr
==============

.. py:function:: read_bufr(path, columns=[], filters={}, required_columns=True, flat=False)

    Extract data from BUFR as a pandas.DataFrame with the specified ``columns`` applying the ``filters`` either in :ref:`hierarchical <tree-mode-section>` or :ref:`flat <flat-mode-section>` mode.

    :param path: path to the BUFR file or a :ref:`message_list_object`
    :type path: str, bytes, os.PathLike or a :ref:`message_list_object`
    :param columns: a list of ecCodes BUFR keys to extract for each BUFR message/subset. When ``flat`` is True ``columns`` must be one of the following string values:

          * "all", empty str or empty list (default): all the columns are extracted
          * "header": only the columns from the header section are extracted
          * "data": only the columns from the data section are extracted

    :type columns: str, sequence[str]
    :param filters: defines the conditions when to extract the specified ``columns``. The individual conditions are combined together with the logical AND operator to form the filter. See :ref:`filters-section` for details.
    :type filters: dict
    :param required_columns: the list of ecCodes BUFR keys that are required to be present in the BUFR message/subset. It has a twofold meaning:

        * if any of the keys in ``required_columns`` is missing in the message/subset the whole message/subset is skipped
        * if all the keys in ``required_columns`` are present, the message/subset is processed even if some key from ``columns`` are missing (supposing the filter conditions are met)

        Bool values are interpreted as follows:

        * if ``flat`` is False:

          * True means all the keys in ``columns`` are required. It means that if any of the keys in ``columns`` missing in the message/subset the whole message/subset is skipped.
          * False means no columns are required

        * if ``flat`` is True either bool value means no columns are required

    :type required_columns: bool, iterable[str]
    :param flat: enables flat extraction mode. When it is ``True`` each message/subset is treated as a :ref:`flat list <flat-mode-section>`, while when it is ``False`` (default), data is extracted as if the message had a :ref:`tree-like hierarchy <tree-mode-section>`. See details below. New in *version 0.10.0*
    :type flat: bool
    :rtype: pandas.DataFrame


    In order to correctly use :func:`read_bufr` for a given BUFR file first you need to understand the structure of the messages and the keys/values you can use for data extraction and filter definition. The BUFR structure can be explored with *ecCodes* command line tools `bufr_ls <https://confluence.ecmwf.int/display/ECC/bufr_ls>`_  and `bufr_dump <https://confluence.ecmwf.int/display/ECC/bufr_dump>`_. You can also use `CodesUI <https://confluence.ecmwf.int/display/METV/CodesUI>`_ or `Metview <https://metview.readthedocs.io>`_, which provide graphical user interfaces to inspect BUFR/GRIB data.

    There are some :ref:`notebook examples <examples>` available demonstrating how to use :func:`read_bufr` for various observation/forecast BUFR data types.


BUFR keys
-----------

   ecCodes keys from both the BUFR header and data sections are supported in ``columns``, ``filters`` and ``required_columns``. However, there are some limitations:

        * keys containing the rank e.g. "#1#latitude" cannot be used
        * key attributes e.g. "latitude->code" cannot be used

   The "count" generated key, which refers to the message index, is also supported but please note that message indexing starts at 1 and not at 0!

Computed BUFR keys
-------------------

   There is also a set of **computed keys** that can be used for :func:`read_bufr`:


.. _key_data_datetime:

data_datetime
+++++++++++++++

    Generated from the "year", "month", "day", "hour", "minute", "second" keys in the BUFR data section. The values are converted to a **datetime.datetime** object.


.. _key_typical_datetime:

typical_datetime
+++++++++++++++++

    Generated from the "typicalYear", "typicalMonth", "typicalDay", "typicalHour", "typicalMinute", "typicalSecond" keys in the BUFR header section. The values are converted to a **datetime.datetime** object.


.. _key_wmo_station_id:

WMO_station_id
++++++++++++++++

    Generated from the "blockNumber" and "stationNumber" keys as::

          blockNumber*1000+stationNumber


.. _key_wigos_station_id:

WIGOS_station_id
++++++++++++++++++

    *New in version 0.12.0*

    Generated from the "wigosIdentifierSeries", "wigosIssuerOfIdentifier",  "wigosIssueNumber" and  "wigosLocalIdentifierCharacter" keys as a str in the following format::

          "{wigosIdentifierSeries}-{wigosIssuerOfIdentifier}-{wigosIssueNumber}-{wigosLocalIdentifierCharacter}


    For example: "0-705-0-1931".

    When using "WIGOS_station_id" in ``filters`` the value can be given as a str or as a tuple/list of 4 values. See: :ref:`filters-section`.

    Details about the WIGOS identifiers can be found `here <https://community.wmo.int/en/activity-areas/WIGOS/implementation-WIGOS/FAQ-WSI>`_.

.. _key_geometry:

geometry
++++++++++

    Values extracted as a list of::

          [longitude,latitude,heightOfStationGroundAboveMeanSeaLevel]

    as required for geopandas.

.. _crs:

CRS
++++

    Generated from the "coordinateReferenceSystem" key using the following mapping:

          .. list-table::
             :header-rows: 1

             * - coordinateReferenceSystem
               - CRS

             * - 0
               - EPSG:4326

             * - 1
               - EPSG:4258

             * - 2
               - EPSG:4269

             * - 3
               - EPSG:4314

             * - 4 or 5
               - not supported

             * - missing
               - EPSG:4326



.. note::

    Computed keys do not preserve their position in ``columns`` but are placed to the end of the resulting DataFrame.


.. _filters-section:

Filters
--------------

    The filter conditions are specified as a dict via ``filters`` and determine when the specified ``columns`` will actually be extracted.

Single value
++++++++++++++

    A filter condition can be a single value match:

      .. code-block:: python

          filters = {"blockNumber": 12}
          filters = {"WMO_station_id": 12925}

          # The "WIGOS_station_id" can be specified in various ways
          # When tuple/list is used the first 3 values must be integers, the last one must be a string.
          filters = {"WIGOS_station_id": "0-705-0-1931"}
          filters = {"WIGOS_station_id": (0, 705, 0, "1931")}

          # However, implicit str to int  conversion is done for the first 3 values, so this is also valid.
          filters = {"WIGOS_station_id": ("0", "705", "0", "1931")}

List/tuple/set of values
++++++++++++++++++++++++++

    A list/tuple/set of values specifies an "in" relation:

     .. code-block:: python

         filters = {"stationNumber": [843, 925]}
         filters = {"blockNumber": range(10, 13)}
         filters = {"WMO_station_id": [12925, 12843]}

         # The "WIGOS_station_id" can be specified in various ways.
         # When tuple/list is used in an id the first 3 values must be integers, the last one must be a string.
         filters = {"WIGOS_station_id": ["0-705-0-1931", "0-705-0-1932"]}
         filters = {"WIGOS_station_id": ((0, 705, 0, "1931"), (0, 705, 0, "1932"))}

         # However, implicit str to int conversion is done for the first 3 values, so this is also valid.
         filters = {
             "WIGOS_station_id": [("0", "705", "0", "1931"), ("0", "705", "0", "1932")]
         }

Slices
++++++++

    Intervals can be expressed as a ``slice`` (the boundaries as inclusive):

      .. code-block:: python

          # closed interval (>=273.16 and <=293.16)
          filters = {"airTemperature": slice(273.16, 293.16)}

          # open interval (<=273.16)
          filters = {"airTemperature": slice(None, 273.16)}

          # open interval (>=273.16)
          filters = {"airTemperature": slice(273.16, None)}


Callables
+++++++++++

    We can even use a ``callable`` condition. This example uses a lambda expression to filter values in a certain range:

    .. code-block:: python

        filters = {"airTemperature": lambda x: x > 250 and x <= 300}


    The same task can also be achieved by using a function:

    .. code-block:: python

        def filter_temp(t):
            return t > 250 and t <= 300


        df = pdbufr.read_bufr(
            "temp.bufr",
            columns=("latitude", "longitude", "airTemperature"),
            filters={"airTemperature": filter_temp},
        )


Combining conditions
+++++++++++++++++++++

    When multiple conditions are specified they are connected with a logical AND:

       .. code-block:: python

           filters = {
               "blockNumber": 12,
               "stationNumber": [843, 925],
               "airTemperature": slice(273.16, 293.16),
           }

    A ``geographical filter`` can be defined like this:

     .. code-block:: python

         # locations in the 40W,10S - 30E,20N area
         filters = {"latitude": slice(-10, 20), "longitude": slice(-40, 30)}

    while the following expression can be used as a ``temporal filter``:

     .. code-block:: python

         filters = {
             "data_datetime": slice(
                 datetime.datetime(2009, 1, 23, 13, 0),
                 datetime.datetime(2009, 1, 23, 13, 1),
             )
         }


.. _tree-mode-section:

Hierarchical mode
-------------------

    When ``flat`` is ``False`` the contents of a BUFR message/subset is interpreted as a hierarchical structure. This is based on a certain group of BUFR keys (related to instrumentation, location etc), which according to the `WMO BUFR manual <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ introduce a new hierarchy level in the message/susbset. During data extraction ``read_bufr`` traverses this hierarchy and when all the ``columns`` are collected and the all the ``filters`` match a new record is added to the output. With this several records can be extracted from the same message/subset.

    **Example**

    In this example we extract values from a classic radiosonde observation BUFR file. Here each message contains a single location ("latitude", "longitude") with several pressure levels of temperature, dewpoint etc. The message hierarchy is shown in the following snapshot:

      .. image:: /_static/temp_structure.png
          :width: 450px

    To extract the temperature profile for the first two stations we can use this code:

      .. code-block:: python

          df = pdbufr.read_bufr(
              "temp.bufr",
              columns=("latitude", "longitude", "pressure", "airTemperature"),
              filters={"count": [1, 2]},
          )

    which results in the following DataFrame:

      .. literalinclude:: _static/h_dump_output.txt


.. _flat-mode-section:

Flat mode
--------------

    New in *version 0.10.0*

    When ``flat`` is ``True`` messages/subsets are extracted as a whole preserving the column order (see the note below for exceptions) and each extracted message/subset will be a separate record in the resulting DataFrame.

    With ``filters`` we can control which messages/subsets should be selected. By default, all the columns in a message/subset are extracted (see the exceptions below), but this can be changed by setting ``columns`` to "header" or "data" to get only the header or data section keys. Other column selection modes are not available.

    In the resulting DataFrame the original ecCodes keys containing the **rank** are used as column names, e.g. "#1#latitude" instead of "latitude". The following set of keys are omitted:

    * from the header: "unexpandedDescriptors"
    * from the data section: data description operator qualifiers  (e.g. "delayedDescriptorReplicationFactor") and "operator"
    * key attributes e.g. "latitude->code"

    The **rank** appearing in the keys in a message containing **uncompressed subsets** is not reset by ecCodes when a new subset started. To make the columns as aligned as a possible in the output :func:`read_bufr` resets the rank and ensures that e.g. the first "latitude" key is always called "#1#latitude" in each uncompressed subset.

    ``filters`` control what messages/subsets should be extracted from the BUFR file. They are interpreted in a different way than in the  :ref:`hierarchical <tree-mode-section>` mode:

    * they can only contain keys without a rank
    * for **non-computed keys** the filter condition matches if there is a match for the same key with any given rank in the message/subset. E.g. if ::

        filters = {"pressure": 50000}

      and there is e.g. a value "#12#pressure" = 50000 in the message/subset then the filter matches.
    * for **computed keys** the filter condition matches if there is a match for the involved keys at their first occurrence (e.i. rank=1) in the message/subset. E.g::

         filters = {"WMO_station_id": 12925}

      matches if "#1#blockNumber" = 12 and "#1#stationNumber" = 925 in the message/subset (remember WMO_station_id=blockNumber*1000+stationNumber)

    .. warning::

        Messages/subsets in a BUFR file can have a different set of BUFR keys. When a new message/subset is processed :func:`read_bufr` adds it to the resulting DataFrame as a new record and columns that are not yet present in the output are automatically appended by Pandas to the end changing the original order of keys for that message. When this happens :func:`pdbufr` prints a warning message to the stdout
        (see the example below or the :ref:`/examples/flat_dump.ipynb` notebook for details).

    **Example**

    We use the same radiosonde BUFR file as for the :ref:`hierarchical mode <tree-mode-section>` example above. To extract all the data values for the first two stations we can use this code:

      .. code-block:: python

          df = pdbufr.read_bufr(
              "temp.bufr",
              columns="data",
              flat=True,
              filters={"count": [1, 2]},
          )

    which results in the following DataFrame:

      .. literalinclude:: _static/flat_dump_output.txt

    and generates the following warning::

      Warning: not all BUFR messages/subsets have the same structure in the input file.
      Non-overlapping columns (starting with column[189] = #1#generatingApplication)
      were added to end of the resulting dataframe altering the original column order
      for these messages.

    This warning can be disabled by using the **warnings** module. The code below produces the same DataFrame as the one above but does not print the warning message:

      .. code-block:: python

          import warnings

          warnings.filterwarnings("ignore", module="pdbufr")

          df = pdbufr.read_bufr(
              "temp.bufr",
              columns="data",
              flat=True,
              filters={"count": [1, 2]},
          )

    .. note::

      See the :ref:`/examples/flat_dump.ipynb` notebook for more details.

.. _message-list-object-section:

Message list object
------------------------

:func:`read_bufr` can take a message list object as an input. It is particularly useful if we already have the BUFR data in another object/storage structure and we want to directly use it with pdbufr.

A message list object is sequence of messages, where a message must be a mutable mapping of ``str`` BUFR keys to values. Ideally, the message object should implement a context manager (``__enter__`` and ``__exit__``) and also the ``is_coord`` method, which determines if a key is a BUFR coordinate descriptor. If any of these methods are not available :func:`read_bufr` will automatically create a wrapper object to provide default implementations. For details see :class:`MessageWrapper` in ``pdbufr/bufr_structure.py``.
