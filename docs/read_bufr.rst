read_bufr
==========

..  py:function:: read_bufr(path, columns, filters={}, required_columns=True)

   Extract data from BUFR as a pandas.DataFrame with the specified ``columns`` applying the ``filters``.
   
   :param path: path to the BUFR file
   :type path: str, bytes, os.PathLike
   :param columns: A list of ecCodes BUFR keys to extract for each BUFR message/subset.
   :type columns: iterable
   :param filters: A dictionary of ecCodes BUFR key filter conditions. The individual conditions are combined together with the logical AND operator to form the filter.
   :type filters: dict
   :param required_columns: The list of ecCodes BUFR keys that are required to be present in the BUFR message/subset. ``True`` means all the keys in ``columns`` are required.
   :type required_columns: bool, iterable[str]
   :rtype: pandas.DataFrame


   **Keys**

   ecCodes keys from both the BUFR header and data sections are supported but there are some limitations:
   
     * keys containing the rank e.g. "#1#latitude#" cannot be used
     * key attributes e.g. "latitude->code" cannot be used
  
   The "count" generated key, which refers to the message index, is also supported but please note that message indexing starts at 1 and not at 0!
   
   There is also a set of **computed keys** that can be used for :func:`read_bufr`:

    * "data_datetime" (datetime.datetime): generated from the "year", "month", "day", "hour", "minute", "second" keys in the BUFR data section.
    * "typical_datetime" (datetime.datetime): generated from the "typicalYear", "typicalMonth", "typicalDay", "typicalHour", "typicalMinute", "typicalSecond" keys in the BUFR header section.
    * "WMO_station_id": generated from the "blockNumber" and "stationNumber" BUFR data section keys as blockNumber*1000+stationNumber
    * "geometry": values extracted as a list of [longitude, latitude,heightOfStationGroundAboveMeanSeaLevel] (predefined to geometry for geopandas).
    * "CRS": generated from the "coordinateReferenceSystem" BUFR data section key using the following mappings:

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


    **Filters** 

    A filter condition can be a single value match:

     .. code-block:: python 

          filters={"blockNumber": 12}

    an "in" relation: 

     .. code-block:: python 
          
          filters={"stationNumber": [843, 925]}
          
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

    
    **Algorithm**

    A BUFR message/subset seemingly has a flat structure but actually it can be interpreted as a hierarchy. According to the WMO manual each key in class 01-09 introduces a new hierarchy level in the BUFR message/subset::

          Element descriptors corresponding to the following classes in Table B 
          shall remain in effect until superseded by redefinition:
               Class
               01 Identification
               02 Instrumentation
               03 Instrumentation
               04 Location (time)
               05 Location (horizontal - 1)
               06 Location (horizontal - 2)
               07 Location (vertical)
               08 Significance qualifiers
               09 Reserved
               
          Note: Redefinition is effected by the occurrence of element descriptors
               which contradict the preceding element descriptors from these classes. If two or
               more elements from the same class do not contradict one another, they all apply.

     
    This may sound cryptic but this is what ``read_bufr`` uses to define the hierarchy and decide when a set of collected columns has to be added to the output as a new record.
