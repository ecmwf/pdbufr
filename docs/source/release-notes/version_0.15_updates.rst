Version 0.15 Updates
/////////////////////////


Version 0.15.0
===============

Improved flat reader
---------------------

The :ref:`flat reader <flat-reader>` has been refactored and significantly improved (:pr:`113`, :pr:`120`, :pr:`121`). This includes:

- Enabling the usage of arbitrary keys (see: :ref:`flat-individual-key-extraction`).
- Enabling the usage of ranks in key names (see: :ref:`flat-individual-key-extraction`) both in the ``columns`` and ``filters`` kwargs.
- Improved performance (:pr:`121`).

See the notebook examples:

  - :ref:`/tutorials/flat/r_flat_overview.ipynb`
  - :ref:`/tutorials/flat/r_flat_filters.ipynb`
  - :ref:`/tutorials/flat/r_flat_column_alignment.ipynb`
  - :ref:`/tutorials/flat/r_flat_required_columns_block.ipynb`
  - :ref:`/tutorials/flat/r_flat_required_columns_individual.ipynb`
  - :ref:`/tutorials/flat/r_flat_aircraft.ipynb`
  - :ref:`/tutorials/generic_vs_flat.ipynb`



New features
---------------

- Added the ``prefilter_headers`` option to all readers (:pr:`105`).  If True, the BUFR headers are filtered before unpacking the data section. This can significantly speed up the extraction when the ``filters`` contain header keys (and only a small fraction of messages/subsets matches). The default is False.

See the notebook example:

  - :ref:`/how-tos/options/prefilter_headers.ipynb`


Changes
----------------

- Revised usage of the get() method in the message object (internal change) (:pr:`104`).


Documentation
-------------

- The documentation has been completely renewed (:pr:`115`).
