Why pdbufr?
==========================

**pdbufr** is a Pandas reader for the `BUFR <https://en.wikipedia.org/wiki/BUFR>`_ (Binary Universal Form for the Representation of meteorological data) format, built on top of :xref:`eccodes`.

**pdbufr** makes it straightforward to extract observations and other meteorological data from BUFR files into familiar `pandas <https://pandas.pydata.org>`_ DataFrames, without needing to understand the low-level binary format.

**pdbufr** provides a rich filtering engine so that only the data you need is decoded, making it efficient even for large BUFR files with many messages or subsets.

Key features
-------------

* **Simple API** — a single :func:`read_bufr` function covers all use cases.
* **Multiple readers** — choose the reader that best matches your BUFR structure:

  * :ref:`generic-reader` for most observation types
  * :ref:`flat-reader` for flat, non-hierarchical messages
  * :ref:`synop-reader` for WMO SYNOP land-surface reports
  * :ref:`temp-reader` for WMO TEMP upper-air soundings

* **Rich filtering** — select messages, subsets and individual keys by value before decoding, avoiding unnecessary work.
* **Compressed and uncompressed subsets** — both BUFR 3 and BUFR 4 are supported.
* **Cross-platform** — works on Linux, macOS and Windows; the only binary dependency is the ecCodes C-library.
