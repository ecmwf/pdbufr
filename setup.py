#!/usr/bin/env python
#
# Copyright 2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#

import os
import re

import setuptools  # type: ignore


def read(path: str) -> str:
    file_path = os.path.join(os.path.dirname(__file__), *path.split("/"))
    return open(file_path).read()


# single-sourcing the package version using method 1 of:
#   https://packaging.python.org/guides/single-sourcing-package-version/
def parse_version_from(path: str) -> str:
    version_file = read(path)
    version_match = re.search('^__version__ = "(.*)"', version_file, re.M)
    if version_match is None or len(version_match.groups()) > 1:
        raise ValueError("couldn't parse version")
    return version_match.group(1)


setuptools.setup(
    name="pdbufr",
    version=parse_version_from("pdbufr/__init__.py"),
    description="Pandas reader for the BUFR format using ecCodes.",
    long_description=read("README.rst"),
    author="European Centre for Medium-Range Weather Forecasts (ECMWF)",
    author_email="software.support@ecmwf.int",
    license="Apache License Version 2.0",
    url="https://github.com/ecmwf/pdbufr",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["eccodes", "pandas"],
    extras_require={"tests": ["flake8", "pytest", "pytest-cov"]},
    zip_safe=True,
    keywords="eccodes bufr pandas",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
    ],
)
