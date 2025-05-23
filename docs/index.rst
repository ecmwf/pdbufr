
Welcome to pdbufr's documentation
====================================

*pdbufr* is a Python package implementing a `Pandas <https://pandas.pydata.org>`_ reader for the BUFR format using  `ecCodes <https://confluence.ecmwf.int/display/ECC>`_.  It features the :func:`read_bufr` function to extract data from a BUFR file as a Pandas DataFrame using a rich filtering engine.

*pdbufr* supports BUFR 3 and 4 files with uncompressed and compressed subsets. It works on Linux, MacOS and Windows, the ecCodes C-library is the only binary dependency.


.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 1
   :caption: Documentation

   guide/index
   contributing

.. toctree::
   :maxdepth: 1
   :caption: Installation

   install
   release_notes/index
   licence


Indices and tables
==================

* :ref:`genindex`

.. * :ref:`modindex`
.. * :ref:`search`
