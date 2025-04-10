# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
from typing import List
from typing import Optional
from typing import Union

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if not os.path.exists(os.path.join(ROOT_DIR, "tests", "data")):
    ROOT_DIR = "./"

LOCAL_SAMPLE_DIR = os.path.join(ROOT_DIR, "tests", "sample_data")
LOCAL_REF_DIR = os.path.join(ROOT_DIR, "tests", "ref_data")
URL_DATA_DIR = os.path.join(ROOT_DIR, "url_data")
URL_ROOT = "https://get.ecmwf.int/repository/test-data/pdbufr/test-data"


def sample_test_data_path(filename: str) -> str:
    return os.path.join(LOCAL_SAMPLE_DIR, filename)


def reference_test_data_path(filename: str) -> str:
    return os.path.join(LOCAL_REF_DIR, filename)


def simple_download(url: str, target: str) -> None:
    import requests  # type: ignore

    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    open(target, "wb").write(r.content)


def get_remote_test_data_path(filename: str, subfolder: str) -> str:
    return os.path.join(URL_ROOT, subfolder, filename)


def get_remote_test_data(
    filename: Union[str, List[str]], subfolder: Optional[str] = None
) -> Union[str, List[str]]:
    if not isinstance(filename, list):
        filename = [filename]

    if subfolder is None:
        subfolder = ""

    if subfolder:
        url_subfolder = f"{URL_ROOT}/{subfolder}"
        target_dir = os.path.join(URL_DATA_DIR, subfolder)
    else:
        url_subfolder = URL_ROOT
        target_dir = URL_DATA_DIR

    res = []
    for fn in filename:
        os.makedirs(target_dir, exist_ok=True)
        f_path = os.path.join(target_dir, fn)
        if not os.path.exists(f_path):
            simple_download(url=f"{url_subfolder}/{fn}", target=f_path)
        res.append(f_path)

    if len(res) == 1:
        return res[0]
    else:
        return res
