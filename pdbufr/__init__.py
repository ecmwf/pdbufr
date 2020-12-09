from .bufr_structure import stream_bufr

__all__ = ["stream_bufr"]

try:
    from .bufr_read import read_bufr

    __all__ += ["read_bufr"]
except ModuleNotFoundError:
    pass

__version__ = "0.8.3.dev0"
