# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# type: ignore

import os
import re
import sys
import typing as T
from importlib import import_module

import pytest

# See https://www.blog.pythonlibrary.org/2018/10/16/testing-jupyter-notebooks/

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "source", "how-tos")
TUTORIALS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "source", "tutorials")
LEGACY_EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "source", "legacy")

SKIP = ("prefilter_headers.ipynb",)  # data file too large to be downloaded in CI


def notebooks_list() -> T.Iterable[str]:
    notebooks = []
    for root in (EXAMPLES, LEGACY_EXAMPLES, TUTORIALS):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".ipynb_checkpoints"]
            for filename in filenames:
                if re.match(r".+\.ipynb$", filename):
                    notebooks.append(os.path.join(dirpath, filename))
    return sorted(notebooks)


def modules_installed(*modules: str) -> bool:
    for module in modules:
        try:
            import_module(module)
        except ImportError:
            return False
    return True


def MISSING(*modules: str) -> bool:
    return not modules_installed(*modules)


@pytest.mark.notebook
@pytest.mark.skipif(
    MISSING("nbformat", "nbconvert", "ipykernel"),
    reason="python package nbformat not installed",
)
@pytest.mark.skipif(sys.platform == "win32", reason="Cannot execute notebooks on Windows")
@pytest.mark.parametrize("path", notebooks_list())
def test_notebook(path: str) -> None:
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    if os.path.basename(path) in SKIP:
        pytest.skip("Notebook marked as 'skip'")

    with open(path) as f:
        nb = nbformat.read(f, as_version=4)

    proc = ExecutePreprocessor(timeout=60 * 2, kernel_name="python3")
    proc.preprocess(nb, {"metadata": {"path": os.path.dirname(path)}})
