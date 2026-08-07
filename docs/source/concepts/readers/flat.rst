.. _flat-reader:

Flat
==============

.. py:function:: read_bufr(path, reader="flat", columns=[], filters={}, required_columns=True, prefilter_headers=False)
    :noindex:

    Extract data from BUFR as a pandas.DataFrame assuming a flat BUFR structure.

    :param path: Path to the BUFR file or a :ref:`message list object <message-list-object>`
    :type path: str, bytes, os.PathLike or a :ref:`message list object <message-list-object>`
    :param columns: Specify the keys to extract. We can invoke the :ref:`block extraction mode <flat-block-extraction>` by using the following special keys:

        * "all", empty str or empty list (default): all the :ref:`eccodes-bufr-keys` (including both the header and data sections) are extracted
        * "header": only the :ref:`eccodes-bufr-keys` from the header section are extracted
        * "data": only the :ref:`eccodes-bufr-keys` from the data section are extracted

        Any other string value is treated as a single BUFR key to extract and any sequence of strings is treated
        as a list of BUFR keys to extract. See the :ref:`individual key extraction mode <flat-individual-key-extraction>` for details. The special keys ("all", "header", "data") cannot be combined with BUFR keys, but "header" and "data" can be
        combined together to get all the keys from both sections.

    :type columns: str, sequence[str]
    :param filters: Define the conditions when to extract the specified ``columns``. The individual conditions are combined together with the logical AND operator to form the filter. See :ref:`flat-filters` for details. Keys appearing in the ``filters`` are automatically added to the list of columns to extract if they are not already present in ``columns``.
    :type filters: dict
    :param required_columns: The list of :ref:`eccodes-bufr-keys` that are required to be present in a BUFR message/subset. The keys in ``required_columns`` are automatically added to the list of columns to extract if they are not already present in ``columns``. The required keys are matched with any rank in the message/subset.  It has a twofold meaning:

        * if any of the keys in ``required_columns`` is missing in the message/subset the whole message/subset is skipped
        * if all the keys in ``required_columns`` are present, the message/subset is processed even if some key from ``columns`` are missing (supposing the filter conditions are met)

        If it is a ``bool`` the value is interpreted as follows:

        * in :ref:`block extraction mode <flat-block-extraction>` (True or False), messages/subsets are always processed (supposing the filter conditions are met).
        * in :ref:`individual key extraction mode <flat-individual-key-extraction>` ``True`` means all the keys in ``columns`` are required, and if any of the keys in ``columns`` missing in the message/subset the whole message/subset is skipped. ``False`` means no columns are required.

    :type required_columns: bool, iterable[str]
    :param prefilter_headers: If True, the headers are filtered before unpacking the data section. This can significantly speed up the extraction when the ``filters`` contain header keys (and only a small fraction of messages/subsets matches). *New in version 0.15.0.*
    :type prefilter_headers: bool
    :rtype: pandas.DataFrame


.. _flat-reader-modes:

How does the flat reader work?
--------------------------------

The :ref:`flat reader <flat-reader>` has 2 modes based on the ``columns`` parameter.


.. _flat-block-extraction:

Block extraction mode
////////////////////////

When ``columns`` is set to "all", "header" or "data" the :ref:`flat reader <flat-reader>` extracts the data in blocks, i.e. it extracts all the keys from the header section and/or all the keys from the data section as a whole. Each extracted message/subset will be a separate record in the resulting DataFrame. The column order is preserved (see the warning below for exceptions).

By default, all the columns in a message/subset are extracted (see the exceptions below), but this can be changed by setting ``columns`` to "header" or "data" to get only the header or data section keys.

In the results the original :ref:`ecCodes keys <eccodes-bufr-keys>` containing the :ref:`rank <eccodes-key-rank>` are used as column names, e.g. "#1#latitude" instead of "latitude". The following set of keys are omitted:

* from the header: "unexpandedDescriptors"
* from the data section: data description operator qualifiers  (e.g. "delayedDescriptorReplicationFactor") and "operator"
* key attributes e.g. "latitude->code"


.. admonition:: Keys in uncompressed subsets
   :class: warning

    The **rank** appearing in the keys in a message containing **uncompressed subsets** is not reset by ecCodes when a new subset starts. To make the columns as aligned as a possible in the output pdbufr resets the rank in each subset and ensures that e.g. the first "latitude" key is always called "#1#latitude" in each uncompressed subset.


.. admonition:: Non-aligned columns in the output DataFrame
   :class: warning

    Messages/subsets in a BUFR file can have a different set of BUFR keys. When a new message/subset is processed the :ref:`flat reader <flat-reader>` adds it to the resulting DataFrame as a new record and columns that are not yet present in the output are automatically appended by Pandas to the end changing the original order of keys for that message. When this happens pdbufr prints a warning message to the stdout (see the :ref:`/tutorials/flat/r_flat_column_alignment.ipynb` notebook for details).


.. _flat-individual-key-extraction:

Individual key extraction mode
////////////////////////////////

When ``columns`` is set to a list of BUFR keys (or a single BUFR key) the :ref:`flat reader <flat-reader>` extracts only the specified keys. Each extracted message/subset will be a separate record in the resulting DataFrame.

The keys can contain a :ref:`rank <eccodes-key-rank>`, e.g. "#3#cloudType". Keys without a rank from the data section are interpreted as rank=1 keys, e.g. "cloudType" is treated as "#1#cloudType" (i.e. the first occurrence of "cloudType" in the message/subset is extracted). E.g.:


.. code-block:: python

    # extract the first and third occurrence of "cloudType" from the data section
    columns = ["cloudType", "#3#cloudType"]
    df = pdbufr.read_bufr(
        "tests/sample_data/obs_3day.bufr",
        reader="flat",
        columns=columns,
    )

.. admonition:: Keys without a rank are treated as rank=1
   :class: warning

    This behaviour differs from the ``eccodes.codes_get()`` function in the ecCodes API, which returns the last occurrence of a key in the message/subset when no rank is specified.


For uncompressed subsets the rank is treated in a special way as described below.

.. admonition:: Ranks in uncompressed subsets
   :class: warning

    The **rank** appearing in the keys in a message containing **uncompressed subsets** is not reset by ecCodes when a new subset started. To make the columns as aligned as a possible in the output pdbufr resets the rank in each subset and ensures that e.g. the first "latitude" key is always called "#1#latitude" in each uncompressed subset. The rank specified in the ``columns`` is interpreted as the reset rank, e.g. if "#3#cloudType" is specified in ``columns`` then the third occurrence of "cloudType" in each uncompressed subset will be extracted and called "#3#cloudType" in the resulting DataFrame.


.. _flat-filters:

Filters
-------------------

With ``filters`` we can control which messages/subsets should be selected. The conditions are combined together with the logical AND operator to form the filter. See the available :ref:`filter types  <filters>` for details. The following special rules apply to the :ref:`flat reader <flat-reader>` ``filters`` both for standard (i.e. non-computed) and for :ref:`computed keys <computed-bufr-keys>`.

Filters for standard keys
//////////////////////////////

* ranks can be used in the filter keys, e.g. ::

    filters = {"#2#pressure": 50000}

  matches if the second occurrence of "pressure" in the message/subset is 50000.

* key without a rank in the filter is interpreted as rank=1, e.g. ::

    filters = {"pressure": 50000}

  matches if the first occurrence of "pressure" in the message/subset is 50000.

* the special leading "~" notation can be used to check for any occurrence of a key in the message/subset, e.g. ::

    filters = {"~pressure": 50000}

  matches if any occurrence of "pressure" in the message/subset is 50000.


Filters for computed keys
//////////////////////////////

* ranks or the leading "~" notation cannot be used
* for :ref:`computed keys <computed-bufr-keys>` the filter condition matches if there is a match for the involved keys at their first occurrence (e.i. rank=1) in the message/subset. E.g::

     filters = {"WMO_station_id": 12925}

  matches if "#1#blockNumber" = 12 and "#1#stationNumber" = 925 in the message/subset (remember WMO_station_id=blockNumber*1000+stationNumber)


Examples
-------------------

- :ref:`/tutorials/flat/r_flat_overview.ipynb`
- :ref:`/tutorials/flat/r_flat_filters.ipynb`
- :ref:`/tutorials/flat/r_flat_required_columns_block.ipynb`
- :ref:`/tutorials/flat/r_flat_required_columns_individual.ipynb`
- :ref:`/tutorials/flat/r_flat_column_alignment.ipynb`
- :ref:`/tutorials/flat/r_flat_aircraft.ipynb`
