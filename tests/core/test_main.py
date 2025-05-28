# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from pdbufr import __main__


def test_main() -> None:
    __main__.main(argv=["selfcheck"])

    with pytest.raises(RuntimeError):
        __main__.main(argv=["bad-command"])
