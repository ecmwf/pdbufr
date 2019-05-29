
Pandas reader for the BUFR format using ecCodes.

Features with development status **Pre-Alpha**:

- Reading BUFR


Installation
============

The package is installed from PyPI with::

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

Or if you manage binary packages with *Conda* use::

    $ conda install eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation

Note that *ecCodes* support for the Windows operating system is experimental.

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m cfgrib selfcheck
    Found: ecCodes v2.7.0.
    Your system is ready.


Contributing
============

The main repository is hosted on GitHub,
testing, bug reports and contributions are highly welcomed and appreciated:

https://github.com/ecmwf/pdbufr

Please see the CONTRIBUTING.rst document for the best way to help.

Lead developer:

- `Alessandro Amici <https://github.com/alexamici>`_ - `B-Open <https://bopen.eu>`_

See also the list of `contributors <https://github.com/ecmwf/cfgrib/contributors>`_ who participated in this project.


License
=======

Copyright 2017-2018 European Centre for Medium-Range Weather Forecasts (ECMWF).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0.
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
