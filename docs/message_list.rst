Message list object
=====================

:func:`read_bufr` can take a message list object as an input. It is particularly useful if we already have the BUFR data in another object/storage structure and we want to directly use it with pdbufr.

A message list object is sequence of messages, where a message must be a mutable mapping of ``str`` BUFR keys to values. 

The simplest form of a message list is a list of dictionaries:

.. code-block:: python 

    messages = [{
        "edition": 1,
        "#1#year": 2020,
        "#1#subsetNumber": 1,
        "#1#latitude": 43.0,
        "#1#longitude": 12.0,
        "#1#airTemperature": 300.0,
        "#1#latitude->code": "005001",
        "#1#longitude->code": "006001",
    },{
        "edition": 1,
        "#1#year": 2020,
        "#1#subsetNumber": 1,
        "#1#latitude": -12.0,
        "#1#longitude": 5.0,
        "#1#airTemperature": 310.0,
        "#1#latitude->code": "005001",
        "#1#longitude->code": "006001",
    },]

    import pdbufr

    df = pdbufr.read_bufr(messages, columns=("latitude", "longitude", "airTemperature"), filters={"latitude": slice(0, None))

Ideally, the message object should implement a context manager and the `is_coord` method. The latter tells us if a key is a BUFR coordinate descriptor. If these are not available, like in the example above, :func:`read_bufr` will create a wrapper object providing a default implementation for each. 

The `is_coord` method  for performance . The default implementation looks like this:

.. code-block:: python 
        
    def is_coord(self, key, name=None): 
         """Check if the specified key is a BUFR coordinate descriptor

        Parameters
        ----------
        key: str
            The full key name containing the ecCodes ranks

        Returns
        -------
        bool
            True if the specified ``key`` is a BUFR coordinate descriptor
        """
        try:
            return int(self[key + "->code"]) < 9999
        except Exception:
            return False
