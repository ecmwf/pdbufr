Version 0.13 Updates
/////////////////////////

Version 0.13.0
===============

Readers
----------------

Implemented the "readers" interface to allow better extraction for specific data types. The original :func:`read_bufr` interface was kept for backwards compatibility and works as before.  (:pr:`88`)

New code should use the readers, which can be activated via the ``reader`` keyword argument in the :func:`read_bufr` function. The following readers are available:

    - :ref:`generic <generic-reader>`: extracts arbitrary BUFR keys with a hierarchical collector. It has the same functionality as the original :func:`read_bufr` function, with the ``flat=False`` option (set by default).
    - :ref:`flat <flat-reader>`: extracts whole BUFR messages/subsets as flat records. It has the same functionality as the original :func:`read_bufr` function, with the ``flat=True`` option.

    The following readers are **experimental** and may change in future releases:

    - :ref:`synop <synop-reader>`: extracts :ref:`synop-like data <synop-like-data>` from BUFR using pre-defined :ref:`parameters <synop-params>`. A parameter is a high-level concept in ``pdbufr``. It was introduced to overcome the problem that the same quantity can be encoded in BUFR in multiple ways. When using parameters like "t2m" we do not need to know the actual encoding, but the desired value is automatically extracted for us. Another advantage is that we can easily extract the observation periods, levels and units for each parameter, which is simply not possible with the :ref:`generic reader <generic-reader>`.
    - :ref:`temp <temp-reader>`: extracts :ref:`temp-like data <temp-like-data>` from BUFR using pre-defined :ref:`parameters <temp-params>`.
