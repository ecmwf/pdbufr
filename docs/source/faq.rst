.. _faq:

Frequently Asked Questions
============================

.. rubric:: How do I read only a subset of messages from a large BUFR file?

Use the ``filters`` parameter to select only the messages you need before any data
is decoded. For example, to read only messages from station 1:

.. code-block:: python

    import pdbufr

    df = pdbufr.read_bufr(
        "observations.bufr",
        columns=["latitude", "longitude", "airTemperature"],
        filters={"stationNumber": 1},
    )

See :ref:`filters` for the full list of filtering options.

.. rubric:: What is the difference between the generic and flat readers?

The :ref:`generic-reader` reconstructs the hierarchical BUFR structure, which is useful
for messages that contain sequences (e.g. multiple pressure levels per station).

The :ref:`flat-reader` treats every key in the message as a flat column, making it
useful when you want to examine or extract all BUFR keys at once.

.. rubric:: Why do some columns contain ``NaN``?

A ``NaN`` value means the corresponding BUFR key was not present in that particular
message or subset. BUFR files can have a varying set of keys across messages; pdbufr
fills missing columns with ``NaN`` to keep the DataFrame aligned.

.. rubric:: How do I suppress the column-alignment warning?

.. code-block:: python

    import warnings
    import pdbufr

    warnings.filterwarnings("ignore", module="pdbufr")

    df = pdbufr.read_bufr("observations.bufr", columns="data")

.. rubric:: Can I read BUFR data from a URL or an in-memory buffer?

Yes. Pass a :ref:`message list object <message-list-object>` as the ``path`` argument.
See the :ref:`message-list-object` section of the concepts guide for details.

.. rubric:: Where can I report bugs or request features?

Please open an issue on the `GitHub repository <https://github.com/ecmwf/pdbufr/issues>`_.
