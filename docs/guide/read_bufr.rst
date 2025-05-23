read_bufr
==============

.. py:function:: read_bufr(path, reader="generic", **kwargs)

    Extract data from BUFR as a pandas.DataFrame with the specified ``reader``.

    The following readers are available:


    .. list-table::
        :widths: 15 85
        :header-rows: 1

        * - Reader
          - Description
        * - :ref:`generic <generic-reader>`
          -  extracts arbitrary BUFR keys with a hierarchical collector
        * - :ref:`flat <flat-reader>`
          -  extracts whole BUFR messages/subsets as flat records
        * - :ref:`synop <synop-reader>`
          - extracts SYNOP/SHIP data using pre-defined parameters
