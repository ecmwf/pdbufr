#!/usr/bin/env python
#
# (C) Copyright 2019- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

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
    install_requires=["attrs", "eccodes", "pandas"],
    extras_require={"tests": ["flake8", "pytest", "pytest-cov", "requests"]},
    zip_safe=True,
    keywords="eccodes bufr pandas",
    classifiers=[
        "Development Status :: 4 - Beta",
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
