.. _flat-reader:

Flat
==============

.. py:function:: read_bufr(path, reader="flat", columns=[], filters={}, required_columns=True)
    :noindex:

    Extract data from BUFR as a pandas.DataFrame assuming a flat BUFR structure.

    :param path: path to the BUFR file or a :ref:`message list object <message-list-object>`
    :type path: str, bytes, os.PathLike or a :ref:`message list object <message-list-object>`
    :param columns: specify the BUFR keys to extract. The following values are supported:

          * "all", empty str or empty list (default): all the :ref:`eccodes-bufr-keys` (including both the header and data sections) are extracted
          * "header": only the :ref:`eccodes-bufr-keys` from the header section are extracted
          * "data": only the :ref:`eccodes-bufr-keys` from the data section are extracted

    :type columns: str, sequence[str]
    :param filters: defines the conditions when to extract the specified ``columns``. The individual conditions are combined together with the logical AND operator to form the filter. See :ref:`filters` for details.
    :type filters: dict
    :param required_columns: the list of :ref:`eccodes-bufr-keys` that are required to be present in a BUFR message/subset. It has a twofold meaning:

        * if any of the keys in ``required_columns`` is missing in the message/subset the whole message/subset is skipped
        * if all the keys in ``required_columns`` are present, the message/subset is processed even if some key from ``columns`` are missing (supposing the filter conditions are met)
        * if it is a bool (either True or False), messages/subsets are always processed (supposing the filter conditions are met)

    :type required_columns: bool, iterable[str]
    :rtype: pandas.DataFrame


.. _flat-structure:

How the flat reader works
-----------------------------

    The :ref:`flat reader <flat-reader>` extracts each message/subset as a whole preserving the column order (see the warning below for exceptions). Each extracted message/subset will be a separate record in the resulting DataFrame.

    By default, all the columns in a message/subset are extracted (see the exceptions below), but this can be changed by setting ``columns`` to "header" or "data" to get only the header or data section keys. Other column selection modes are not available.

    In the results the original :ref:`ecCodes keys <eccodes-bufr-keys>` containing the **rank** are used as column names, e.g. "#1#latitude" instead of "latitude". The following set of keys are omitted:

    * from the header: "unexpandedDescriptors"
    * from the data section: data description operator qualifiers  (e.g. "delayedDescriptorReplicationFactor") and "operator"
    * key attributes e.g. "latitude->code"

    The **rank** appearing in the keys in a message containing **uncompressed subsets** is not reset by ecCodes when a new subset started. To make the columns as aligned as a possible in the output pdbufr resets the rank and ensures that e.g. the first "latitude" key is always called "#1#latitude" in each uncompressed subset.

    .. warning::

        Messages/subsets in a BUFR file can have a different set of BUFR keys. When a new message/subset is processed the :ref:`flat reader <flat-reader>` adds it to the resulting DataFrame as a new record and columns that are not yet present in the output are automatically appended by Pandas to the end changing the original order of keys for that message. When this happens pdbufr prints a warning message to the stdout
        (see the example below or the :ref:`/examples/r_flat.ipynb` notebook for details).


Filters
-------------------

    With ``filters`` we can control which messages/subsets should be selected. The conditions are combined together with the logical AND operator to form the filter. See :ref:`filters` for details. The following special rules apply to the :ref:`flat reader <flat-reader>` ``filters``:

    * they can only contain keys without a rank
    * for **non-computed keys** the filter condition matches if there is a match for the same key with any given rank in the message/subset. E.g. if ::

        filters = {"pressure": 50000}

      and there is e.g. a value "#12#pressure" = 50000 in the message/subset then the filter matches.
    * for **computed keys** the filter condition matches if there is a match for the involved keys at their first occurrence (e.i. rank=1) in the message/subset. E.g::

         filters = {"WMO_station_id": 12925}

      matches if "#1#blockNumber" = 12 and "#1#stationNumber" = 925 in the message/subset (remember WMO_station_id=blockNumber*1000+stationNumber)

Example
----------------

    The input is one of the tests data files with classic radiosonde observations, where each message contains a single location ("latitude", "longitude") with several pressure levels of temperature, dewpoint etc. The message hierarchy is shown in the following snapshot:

      .. image:: /_static/temp_structure.png
          :width: 450px


    To extract all the data values for the first two stations we can use this code:

      .. code-block:: python

          df = pdbufr.read_bufr(
              "tests/sample_data/temp.bufr",
              reader="flat",
              columns="data",
              filters={"count": [1, 2]},
          )

    which results in the following DataFrame:

      .. literalinclude:: /_static/flat_dump_output.txt

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
              "tests/sample_data/temp.bufr",
              reader="flat",
              columns="data",
              filters={"count": [1, 2]},
          )


Examples
-----------

    - :ref:`/examples/r_flat.ipynb`
