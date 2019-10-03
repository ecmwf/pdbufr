import pytest

from pdbufr import __main__


def test_main():
    __main__.main(argv=['selfcheck'])

    with pytest.raises(RuntimeError):
        __main__.main(argv=['bad-command'])
