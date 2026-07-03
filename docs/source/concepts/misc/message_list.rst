
.. _message-list-object:

Message list object
------------------------

:func:`read_bufr` can take a message list object as an input. It is particularly useful if we already have the BUFR data in another object/storage structure and we want to directly use it with pdbufr.

A message list object is sequence of messages, where a message must be a mutable mapping of ``str`` BUFR keys to values. Ideally, the message object should implement the following methods:

- a context manager (``__enter__`` and ``__exit__``)
- the ``get(key, default=None)`` method, which retrieves the value of a given key with an optional default value if the key is missing.
- the ``is_coord()`` method, which determines if a key is a BUFR coordinate descriptor.

If any of these methods are not available :func:`read_bufr` will automatically create a wrapper object to provide default implementations. For details see :class:`MessageWrapper` in ``pdbufr/bufr_structure.py``.
