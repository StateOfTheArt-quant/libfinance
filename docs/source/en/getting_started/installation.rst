============
Installation
============

The data lives on a server; the client only sends requests and decodes answers, so installing is
light. This page installs the Python client; its dependencies -- ``pandas``, ``numpy``, ``pyarrow``,
``lz4``, ``msgpack`` -- come with pip.

.. tip::

    **Using C++?** The C++ client matches the Python functions one for one, is added to a project
    with CMake ``FetchContent`` and needs Apache Arrow C++. Installing, building and examples:
    `the C++ client guide <https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/readme_en.md>`_.

With pip
========

.. code-block:: bash

    $ pip install libfinance

From source
===========

To track unreleased changes, or to modify the code:

.. code-block:: bash

    $ git clone https://github.com/StateOfTheArt-quant/libfinance
    $ cd libfinance
    $ pip install -e python

Check the install
=================

First confirm the package **imports**. This step needs no server:

.. code-block:: python

    >>> import libfinance
    >>> libfinance.__version__        # the repository's version, shared by the C++ and Python clients

A ``ModuleNotFoundError`` here means a dependency is missing; run the install again.

Next: :doc:`quickstart`.
