============
Contributing
============

The repository is on
`GitHub <https://github.com/StateOfTheArt-quant/libfinance>`_.

Reporting problems
==================

When opening an issue, include the block at the end of
:doc:`../howto/troubleshooting` (version, coverage ranges, full call and full
error). It saves a round trip.

Local development
=================

.. code-block:: bash

    $ git clone https://github.com/StateOfTheArt-quant/libfinance
    $ cd libfinance
    $ pip install -e .
    $ pytest test/

Some tests need a running server, named through environment variables. Without one
they skip automatically:

.. code-block:: bash

    $ LIBFINANCE_TEST_HOST=127.0.0.1 LIBFINANCE_TEST_PORT=8080 pytest test/

Building the docs
=================

The docs are two independent source trees, built separately:

.. code-block:: bash

    $ cd docs
    $ pip install -r requirements.txt
    $ python -m sphinx -b html source/zh build/html/zh
    $ python -m sphinx -b html source/en build/html/en

Chinese reStructuredText has two typesetting traps: docutils does not recognise
inline markup boundaries next to full-width punctuation, and title underlines are
measured in **display width** (CJK characters count as two columns). After editing
the Chinese tree, run:

.. code-block:: bash

    $ python _shared/fix_cjk_markup.py source/zh

It repairs both, and is safe to run repeatedly.

After changing an interface
===========================

``test/test_docs_contract.py`` checks that every public function has an entry in
both documentation trees, and that the hand-written signatures in the English tree
match the code. Adding a function makes it fail until the docs catch up.
