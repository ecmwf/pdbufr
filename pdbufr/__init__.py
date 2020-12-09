from .bufr_structure import stream_bufr

__all__ = ["stream_bufr"]

try:
    from .bufr_read import read_bufr

    __all__ += ["read_bufr"]
except ModuleNotFoundError:
    pass  # pragma: no cover

__version__ = "0.9.0.dev0"
