Development
============

Contributions
-------------

The code repository is hosted on `Github`_, testing, bug reports and contributions are highly welcomed and appreciated. Feel free to fork it and submit your PRs against the **develop** branch.

Development setup
-----------------------

First, clone the repository locally. You can use the following command:

.. code-block:: shell

   git clone --branch develop git@github.com:ecmwf/pdbufr.git


Next, enter your Python virtual environment or create a new one. Once the virtual environment is activated, enter your git repository and run the following commands:

.. code-block:: shell

    pip install -e .[dev]
    pre-commit install

Please note in zsh you need to use quotes around the square brackets:


.. code-block:: shell

    pip install -e ".[dev]"
    pre-commit install

This setup enables the `pre-commit`_ hooks, performing a series of quality control checks on every commit. If any of these checks fails the commit will be rejected.

Run unit tests
---------------

To run the test suite, you can use the following command:

.. code-block:: shell

    pytest


Build documentation
-------------------

To build the documentation you need to have `pandoc`_ installed on your system. You can find the installation instructions on the `pandoc website`_.

To build the documentation locally use the following commands:

.. code-block:: shell

    cd docs
    make html

To see the generated HTML documentation open the ``docs/_build/html/index.html`` file in your browser.


.. _`Github`: https://github.com/ecmwf/pdbufr
.. _`pre-commit`: https://pre-commit.com/
.. _`pandoc`: https://pandoc.org/
.. _`pandoc website`: https://pandoc.org/installing.html
