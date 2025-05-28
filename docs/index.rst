
Welcome to pdbufr's documentation
====================================

|Static Badge| |image1| |License: Apache 2.0| |Latest
Release|

.. |Static Badge| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE
.. |image1| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/graduated_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity
.. |License: Apache 2.0| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://opensource.org/licenses/apache-2-0
.. |Latest Release| image:: https://img.shields.io/github/v/release/ecmwf/pdbufr?color=blue&label=Release&style=flat-square
   :target: https://github.com/ecmwf/pdbufr/releases


.. important::

    This software is **Graduated** and subject to ECMWF's guidelines on `Software Maturity <https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity>`_.



*pdbufr* is a Python package implementing a `Pandas <https://pandas.pydata.org>`_ reader for the BUFR format using  :xref:`eccodes`. It features the :func:`read_bufr` function to extract data from a BUFR file as a Pandas DataFrame using a rich filtering engine.

*pdbufr* supports BUFR 3 and 4 files with uncompressed and compressed subsets. It works on Linux, MacOS and Windows, the ecCodes C-library is the only binary dependency.


Quick start
-----------

.. code-block:: python

    import pdbufr

    # Read a radiosonde BUFR file and extract temperature profiles
    # for the first two stations
    df = pdbufr.read_bufr(
        "tests/sample_data/temp.bufr",
        reader="generic",
        columns=["latitude", "longitude", "pressure", "airTemperature"],
        filters={"count": [1, 2]},
    )



.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 1
   :caption: Documentation

   guide/index
   development

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
