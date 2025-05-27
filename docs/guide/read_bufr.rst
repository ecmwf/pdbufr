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
          -  extracts :ref:`synop-like data <synop-like-data>` from BUFR using pre-defined :ref:`parameters <synop-params>`
        * - :ref:`temp <temp-reader>`
          -  extracts :ref:`temp-like data <temp-like-data>` from BUFR using pre-defined :ref:`parameters <temp-params>`
