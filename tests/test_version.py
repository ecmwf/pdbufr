import pdbufr
import pytest


@pytest.mark.skip(reason="dynamic version not available during ci")
def test_version() -> None:
    assert pdbufr.__version__ != "999"
