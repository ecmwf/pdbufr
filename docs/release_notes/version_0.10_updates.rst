
Version 0.10 Updates
/////////////////////////


Version 0.10.2
===============

- fixed issue when :func:`read_bufr` incorrectly treated different message structures as if they were identical  (`#49 <https://github.com/ecmwf/pdbufr/issues/49>`_)

Version 0.10.1
===============

- fixed issue when :func:`read_bufr` failed with an uncaught eccodes.KeyValueNotFoundError exception when could not get value for a key present in a BUFR message (`#46 <https://github.com/ecmwf/pdbufr/issues/46>`_)

Version 0.10.0
===============

- added :ref:`flat dump <flat-mode-section>` mode to :func:`read_bufr` (`#37 <https://github.com/ecmwf/pdbufr/issues/37>`_)
- fixed issue when memory was accumulated as BUFR messages were processed (`#40 <https://github.com/ecmwf/pdbufr/issues/40>`_)
- fixed issue when string data in compressed subsets were not correctly expanded (`#35 <https://github.com/ecmwf/pdbufr/issues/35>`_)