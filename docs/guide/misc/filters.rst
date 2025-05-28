
.. _filters:

Filters
--------------

The filter conditions are specified as a dict via the ``filters`` keyword argument of :func:`read_bufr` and determine when the data will actually be extracted.

Single value
++++++++++++++

    A filter condition can be a single value match:

      .. code-block:: python

          filters = {"blockNumber": 12}
          filters = {"WMO_station_id": 12925}

          # The "WIGOS_station_id" can be specified in various ways
          # When tuple/list is used the first 3 values must be integers, the last one must be a string.
          filters = {"WIGOS_station_id": "0-705-0-1931"}
          filters = {"WIGOS_station_id": (0, 705, 0, "1931")}

          # However, implicit str to int  conversion is done for the first 3 values, so this is also valid.
          filters = {"WIGOsS_station_id": ("0", "705", "0", "1931")}

List/tuple/set of values
++++++++++++++++++++++++++

    A list/tuple/set of values specifies an "in" relation:

     .. code-block:: python

         filters = {"stationNumber": [843, 925]}
         filters = {"blockNumber": range(10, 13)}
         filters = {"WMO_station_id": [12925, 12843]}

         # The "WIGOS_station_id" can be specified in various ways.
         # When tuple/list is used in an id the first 3 values must be integers, the last one must be a string.
         filters = {"WIGOS_station_id": ["0-705-0-1931", "0-705-0-1932"]}
         filters = {"WIGOS_station_id": ((0, 705, 0, "1931"), (0, 705, 0, "1932"))}

         # However, implicit str to int conversion is done for the first 3 values, so this is also valid.
         filters = {
             "WIGOS_station_id": [("0", "705", "0", "1931"), ("0", "705", "0", "1932")]
         }

Slices
++++++++

    Intervals can be expressed as a ``slice`` (the boundaries as inclusive):

      .. code-block:: python

          # closed interval (>=273.16 and <=293.16)
          filters = {"airTemperature": slice(273.16, 293.16)}

          # open interval (<=273.16)
          filters = {"airTemperature": slice(None, 273.16)}

          # open interval (>=273.16)
          filters = {"airTemperature": slice(273.16, None)}


Callables
+++++++++++

    We can even use a ``callable`` condition. This example uses a lambda expression to filter values in a certain range:

    .. code-block:: python

        filters = {"airTemperature": lambda x: x > 250 and x <= 300}


    The same task can also be achieved by using a function:

    .. code-block:: python

        def filter_temp(t):
            return t > 250 and t <= 300


        df = pdbufr.read_bufr(
            "temp.bufr",
            columns=("latitude", "longitude", "airTemperature"),
            filters={"airTemperature": filter_temp},
        )


Combining conditions
+++++++++++++++++++++

    When multiple conditions are specified they are connected with a logical AND:

       .. code-block:: python

           filters = {
               "blockNumber": 12,
               "stationNumber": [843, 925],
               "airTemperature": slice(273.16, 293.16),
           }

    A ``geographical filter`` can be defined like this:

     .. code-block:: python

         # locations in the 40W,10S - 30E,20N area
         filters = {"latitude": slice(-10, 20), "longitude": slice(-40, 30)}

    while the following expression can be used as a ``temporal filter``:

     .. code-block:: python

         filters = {
             "data_datetime": slice(
                 datetime.datetime(2009, 1, 23, 13, 0),
                 datetime.datetime(2009, 1, 23, 13, 1),
             )
         }
