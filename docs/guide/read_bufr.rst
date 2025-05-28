read_bufr
==============

.. py:function:: read_bufr(path, reader="generic", **kwargs)

    Extract data from BUFR as a pandas.DataFrame with the specified ``reader``. To see the available ``**kwargs`` please refer to the documentation of the specific reader. The default reader is :ref:`generic <generic-reader>`.

    The following readers are available:


    .. list-table::
        :widths: 15 85
        :header-rows: 1

        * - Reader
          - Description
        * - :ref:`generic <generic-reader>`
          -  extract arbitrary BUFR keys with a hierarchical collector
        * - :ref:`flat <flat-reader>`
          -  extract whole BUFR messages/subsets as flat records


    The readers below are **experimental** and the API might change in the future. It is not recommended to use it in production code yet.

    .. list-table::
        :widths: 15 85
        :header-rows: 1

        * - Reader
          - Description

        * - :ref:`synop <synop-reader>`
          -  extract :ref:`synop-like data <synop-like-data>` from BUFR using pre-defined :ref:`parameters <synop-params>`
        * - :ref:`temp <temp-reader>`
          -  extract :ref:`temp-like data <temp-like-data>` from BUFR using pre-defined :ref:`parameters <temp-params>`
