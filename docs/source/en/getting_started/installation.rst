============
Installation
============

``libfinance`` is a pure Python client — the data lives on a server, so installing
is light. Afterwards you still need to :doc:`connect to a service <connect>`
before you can query anything.

Requires Python 3.7 or newer.

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
    $ pip install -e .

Check the install
=================

First confirm the package **imports**. This step needs no server:

.. code-block:: python

    >>> import libfinance
    >>> libfinance.__version__
    '0.0.6'

A ``ModuleNotFoundError`` here means a dependency is missing; reinstall.
``libfinance`` requires ``pandas``, ``numpy``, ``lz4``, ``msgpack``, ``six`` and
``python-dateutil``, all pulled in automatically by pip.

Next: :doc:`connect`.
