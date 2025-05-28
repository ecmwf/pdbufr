.. _generic-reader:

Generic
==============

.. py:function:: read_bufr(path, reader="generic", columns=[], filters={}, required_columns=True)
    :noindex:

    Extract the specified ``columns`` from BUFR as a pandas.DataFrame using a :ref:`hierarchical collector <tree-structure>`.

    :param path: path to the BUFR file or a :ref:`message list object <message-list-object>`
    :type path: str, bytes, os.PathLike or a :ref:`message list object <message-list-object>`
    :param columns: a list of :ref:`BUFR keys <eccodes-bufr-keys>` and :ref:`computed keys <computed-bufr-keys>` to extract from each BUFR message/subset. Please note that :ref:`computed keys <computed-bufr-keys>` do not preserve their position in ``columns`` but are placed to the end of the resulting DataFrame.
    :type columns: str, sequence[str]
    :param filters: defines the conditions when to extract the specified ``columns``. The individual conditions are combined together with the logical AND operator to form the filter. See :ref:`filters` for details.
    :type filters: dict
    :param required_columns: the list of :ref:`ecCodes BUFR keys <eccodes-bufr-keys>` that are required to be present in the BUFR message/subset. It has a twofold meaning:

        * if any of the keys in ``required_columns`` is missing in the message/subset the whole message/subset is skipped
        * if all the keys in ``required_columns`` are present, the message/subset is processed even if some key from ``columns`` are missing (supposing the filter conditions are met)

        Bool values are interpreted as follows:

          * True means all the keys in ``columns`` are required. It means that if any of the keys in ``columns`` missing in the message/subset the whole message/subset is skipped.
          * False means no columns are required

    :type required_columns: bool, iterable[str]
    :rtype: pandas.DataFrame

.. _tree-structure:

How the generic reader works
-----------------------------

    The :ref:`generic reader <generic-reader>` reader interprets each BUFR message/subset as a hierarchical structure (see :ref:`bufr-tree-structure` for details). During data extraction pdbufr traverses this hierarchy and when all the ``columns`` are collected and the all the ``filters`` match a new record is added to the output. With this several records can be extracted from the same message/subset.

Example
----------------

    The input is one of the tests data files with classic radiosonde observations, where each message contains a single location ("latitude", "longitude") with several pressure levels of temperature, dewpoint etc. The message hierarchy is shown in the following snapshot:

      .. image:: /_static/temp_structure.png
          :width: 450px

      To extract the temperature profile for the first two stations we can use this code:

      .. code-block:: python

          df = pdbufr.read_bufr(
              "tests/sample_data/temp.bufr",
              columns=("latitude", "longitude", "pressure", "airTemperature"),
              filters={"count": [1, 2]},
          )

      which results in the following DataFrame:

      .. literalinclude:: /_static/h_dump_output.txt


Examples
-----------

    - :ref:`/examples/r_generic_aircraft.ipynb`
    - :ref:`/examples/r_generic_ens.ipynb`
    - :ref:`/examples/r_generic_radiosonde.ipynb`
    - :ref:`/examples/r_generic_synop.ipynb`
    - :ref:`/examples/r_generic_tropical_cyclone.ipynb`
    - :ref:`/examples/r_generic_sat.ipynb`
