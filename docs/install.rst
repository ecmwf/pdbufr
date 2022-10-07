Installation
============

The easiest way to install *pdbufr* dependencies is via Conda::

    $ conda install -c conda-forge python-eccodes pandas

and *pdbufr* itself as a Python package from PyPI with::

    $ pip install pdbufr

System dependencies
-------------------

The Python module depends on the ECMWF *ecCodes* library
that must be installed on the system and accessible as a shared library.
Some Linux distributions ship a binary version that may be installed with the standard package manager.
On Ubuntu 18.04 use the command::

    $ sudo apt-get install libeccodes0

On a MacOS with HomeBrew use::

    $ brew install eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m pdbufr selfcheck
    Found: ecCodes v2.19.0.
    Your system is ready.
