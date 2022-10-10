read_bufr
==============

..  py:function:: read_bufr(path, columns, filters={}, required_columns=(), mode="tree")

   Extract data from BUFR as a pandas.DataFrame with the specified ``columns`` applying the ``filters`` either in hierarchical or flat ``mode``.
   
   :param path: path to the BUFR file
   :type path: str, bytes, os.PathLike
   :param columns: a list of ecCodes BUFR keys to extract for each BUFR message/subset. When ``mode`` is "flat" ``columns`` must be a str with one of the following values:
    
        *  "all": all the columns extracted
        *  "header": only columns from the header section extracted
        *  "data": only the columns from the data section extracted

   :type columns: str, iterable
   :param filters: a dictionary of ecCodes BUFR key filter conditions. The individual conditions are combined together with the logical AND operator to form the filter. See details below.
   :type filters: dict
   :param required_columns: the list of ecCodes BUFR keys that are required to be present in the BUFR message/subset. The default value ``True`` has a different meaning based on ``mode``:

      * If ``mode`` is "tree" True means all the keys in ``columns`` are required
      * If ``mode`` is "flat" True means no columns are required
  
   :type required_columns: bool, iterable[str]
   :param mode: the extraction mode. When it is "tree" data is extracted as if the message had a tree-like hierarchy. When it is "flat" each message/subset is treated as a flat list. See details below.
   :type mode: str
   :rtype: pandas.DataFrame


   In order to correctly use :func:`read_bufr` for a given BUFR file first you need to understand the structure of the messages and the keys/values you can use for data extraction and filter definition. The BUFR structure can be explored with *ecCodes* command line tools `bufr_ls <https://confluence.ecmwf.int/display/ECC/bufr_ls>`_  and  `bufr_dump <https://confluence.ecmwf.int/display/ECC/bufr_dump>`_.

   There are some :ref:`notebook examples <examples>` available demonstrating how to use :func:`read_bufr` for various observation/forecast BUFR data types. 


   **BUFR keys**

   ecCodes keys from both the BUFR header and data sections are supported in ``columns``, ``filters`` and ``required_columns``. However, there are some limitations:
   
     * keys containing the rank e.g. "#1#latitude#" cannot be used
     * key attributes e.g. "latitude->code" cannot be used
  
   The "count" generated key, which refers to the message index, is also supported but please note that message indexing starts at 1 and not at 0!
   
   There is also a set of **computed keys** that can be used for :func:`read_bufr`:

    * "data_datetime" (datetime.datetime): generated from the "year", "month", "day", "hour", "minute", "second" keys in the BUFR data section.
    * "typical_datetime" (datetime.datetime): generated from the "typicalYear", "typicalMonth", "typicalDay", "typicalHour", "typicalMinute", "typicalSecond" keys in the BUFR header section.
    * "WMO_station_id": generated from the "blockNumber" and "stationNumber" keys as:: 
  
          blockNumber*1000+stationNumber

    * "geometry": values extracted as a list of::
  
          [longitude,latitude,heightOfStationGroundAboveMeanSeaLevel]
          
      as required for geopandas.
    * "CRS": generated from the "coordinateReferenceSystem" key using the following mapping:

          .. list-table::
             :header-rows: 1

             * - coordinateReferenceSystem
               - CRS

             * - 0
               - EPSG:4326

             * - 1
               - EPSG:4258

             * - 2
               - EPSG:4269

             * - 3
               - EPSG:4314
               
             * - 4 or 5
               - not supported

             * - missing
               - EPSG:4326


     .. note::

          The computed keys do not preserve their position in ``columns`` but are placed to the end of the resulting DataFrame.

    **Filters** 

    A filter condition can be a single value match:

     .. code-block:: python 

          filters={"blockNumber": 12}

    an "in" relation: 

     .. code-block:: python 
          
          filters={"stationNumber": [843, 925]}
          filters={"blockNumber": range(10, 13)}
          
    or an interval expressed as a ``slice`` (the boundaries as inclusive):

     .. code-block:: python
               
          # closed interval (>=273.16 and <=293.16)  
          filters={"airTemperature": slice(273.16, 293.16)}

          # open interval (<=273.16)  
          filters={"airTemperature": slice(None, 273.16)}

          # open interval (>=273.16)      
          filters={"airTemperature": slice(273.16, None)}

    When multiple conditions are specified they are connected with a logical AND:
     
       .. code-block:: python
     
          filters={"blockNumber": 12, 
               "stationNumber": [843, 925], 
               "airTemperature": slice(273.16, 293.16)}

    A geographical filter can be defined like this:

     .. code-block:: python
     
          # locations in the 40W,10S - 30E,20N area
          filters={"latitude": slice(-10, 20),
                   "longitude": slice(-40, 30)}

    while the following expression can be used as a temporal filter:

     .. code-block:: python
     
          filters={"data_datetime": 
               slice(datetime.datetime(2009,1,23,13,0), 
                     datetime.datetime(2009,1,23,13,1))}

    
    **Tree mode**
    
    When ``mode`` is "tree" the contents of a BUFR message/subset is interpreted as a hierarchy. This is based on a certain group of BUFR keys (related instrumentation, location etc), which according to the `WMO BUFR manual <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/bufr-edition-3-and-crex-edition-1>`_ introduce a new hierarchy level. So ``read_bufr`` traverses this hierarchy and when all the columns are collected and the all the filters match a new record is added to the output. With this it is possible that several records extracted from the same message/subset.

    **Flat mode** 

    When ``mode`` is "flat" there can be at most one record per message/subset in the output. In the resulting DataFrame the column names are the original ecCodes keynames containing the rank e.g. "#1#latitude#". The following set of keys are omitted:

    * "unexpandedDescriptors"
    * non-element keys (i.e. when the identifier id available as keyname->code is not 0) 
    * key attributes e.g. "latitude->code"

    ``filters`` can still be used in this mode but are interpreted in a different way:

    * filters can only contain keys without a rank
    * computed keys cannot be used
    * a filter condition matches if there is a match for the same key with any given rank in the message/subset. E.g. if ::

        filters = {"pressure": 50000}

      and e.g. "#12#pressure" is 50000 in the message/subset then the filter matches.

    .. note::

        Messages/subsets can contain a potentially different BUFR keys. When it happens Pandas adds the keys not yet present in the DataFrame to the end of the columns.
