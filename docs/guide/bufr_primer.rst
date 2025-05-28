.. _bufr-intro:

BUFR primer
================

The BUFR format
-----------------

BUFR (Binary Universal Form for the Representation of meteorological data) is a binary format used for the exchange of meteorological and other data. It is maintained by the `World_Meteorological_Organization <https://en.wikipedia.org/wiki/World_Meteorological_Organization>`_ (WMO). Although BUFR is often only regarded as an **observation** format it can also store **forecast** data. Actually, BUFR is so flexible (in the name "U" stands for "Universal") that basically any kind of meteorological data can be encoded in it.

.. _bufr-structure:

The BUFR structure
---------------------

BUFR is a messages based format, meaning that data is organized into messages, each of which can contain multiple subsets. Messages are individual units and can be arbitrarily concatenated together without having any relation between them.

Each message can be divided into 2 basic parts:

- the **header** contains metadata about the message. Subsets within a message share a single header. See the `ecCodes BUFR Header documentation <https://confluence.ecmwf.int/display/ECC/BUFR+headers>`_ for details.
- the **data** section contains the actual data

When using ecCodes to read a BUFR message the content is represented as a list of key-value pairs. The key names are defined by ecCodes, since WMO does not provide these. Some of the key values are numeric codes, and we need to look up the external "tables" published by WMO or other data producers to interpret them.

.. tip::

    See the `ecCodes BUFR Table documentation <https://confluence.ecmwf.int/display/ECC/BUFR+tables>`_ for the available ecCodes BUFR keys and their meanings.

.. _bufr-tree-structure:

Hierarchical structure
-----------------------

The order of the keys in a message/subset defines a hierarchical structure. This is based on a certain group of BUFR keys (related to instrumentation, location etc), which according to the `WMO BUFR manual <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ introduce a new hierarchy level in the message/susbset.

.. tip::

    The BUFR structure can be explored with *ecCodes* command line tools `bufr_ls <https://confluence.ecmwf.int/display/ECC/bufr_ls>`_  and `bufr_dump <https://confluence.ecmwf.int/display/ECC/bufr_dump>`_. We can also use `CodesUI <https://confluence.ecmwf.int/display/METV/CodesUI>`_ or `Metview <https://metview.readthedocs.io>`_, which provide graphical user interfaces to inspect BUFR/GRIB data.


.. _bufr-data-category:

What does a message contain?
-----------------------------

One of the first difficulties in working with BUFR is to figure out what a message contains. The ecCodes key to use is ``dataCategory``, which is located in the header section of a message. It contains a numeric code that can be interpreted using the WMO BUFR tables. The first couple of values are as follows:

- 0: surface data - land
- 1: surface data - sea
- 2: vertical soundings (other than satellite)

and so on. The full list of codes can be found in the WMO BUFR Table A: `BUFR Table A <https://github.com/wmo-im/BUFR4/blob/master/BUFR_TableA_en.csv>`_.

The header also contains the data sub-category, which further specifies the type of data in the message/subset. This is encoded in different ways in BUFR edition 3 and edition 4.

Sub-category in edition 3
+++++++++++++++++++++++++++

The ``dataSubCategory`` key is a numeric code defined by local automatic data processing (ADP) centres and not by WMO. The centre is defined by the ``bufrHeaderCentre`` key in the header section, it is also a numeric code. So, for example the following key combination indicates a "SYNOP land auto" report according to the subcategory codes used by ECMWF in an edition 3 BUFR message:

- ``dataCategory``: 0
- ``dataSubCategory``: 3
- ``bufrHeaderCentre``: 98


Sub-category in edition 4
+++++++++++++++++++++++++++

The ``internationalDataSubCategory`` is a numeric code defined by WMO and published in the `Common Code Table C-13 <https://github.com/wmo-im/CCT/blob/master/C13.csv>`_. There is also the ``dataSubCategory`` key defined by local automatic data processing (ADP) centres and not by WMO and according to the WMO BUFR manual::

    The local data sub-category is maintained for backwards-compatibility with
    BUFR editions 0-3,since many ADP centres have made extensive use of such
    values in the past. The internationaldata sub-category introduced with BUFR
    edition 4 is intended to provide a mechanism for better understanding of the
    overall nature and intent of messages exchanged between ADP centres. These
    two values (i.e. local sub-category and internationalsub-category) are intended
    to be supplementary to one another, so both may be used within a particular
    BUFR message.


unexpandedDescriptor
+++++++++++++++++++++

The data category and sub-category are just providing hints about the data encoded in the message. The actual data is described by the ``unexpandedDescriptors`` key in the header section, which contains a list of numeric codes that can be interpreted using the `BUFR tables <https://confluence.ecmwf.int/display/ECC/BUFR+tables>`_. So it can happen that two messages with the same data category and sub-category contain similar data encoded in a different way.

Table versions
+++++++++++++++++++++

Another level of complexity is the version of the WMO BUFR tables used to encode the message. This is indicated by the ``masterTableNumber``, ``masterTablesVersionNumber``, ``localTablesVersionNumber`` key in the header section.
