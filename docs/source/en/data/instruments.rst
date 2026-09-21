==============================
Security codes and master data
==============================

Every data call starts by naming **which security**. This chapter covers how codes
are written, where names come from, and one trap that is easy to fall into:
whether delisted securities can still be resolved over a historical range.

Writing codes
=============

A code is ``<exchange code>.<market suffix>``:

.. list-table::
    :header-rows: 1
    :widths: 40 22 38

    *   - Market
        - Suffix
        - Example
    *   - Shanghai Stock Exchange
        - ``.XSHG``
        - ``600000.XSHG``
    *   - Shenzhen Stock Exchange
        - ``.XSHE``
        - ``000001.XSHE``
    *   - US equities
        - ``.US``
        - ``AAPL.US``

The suffix is not optional. The same digits can exist on both exchanges —
``000001.XSHG`` is the SSE Composite Index, ``000001.XSHE`` is Ping An Bank. Only
the suffix separates them.

.. warning::

    Given an incomplete code, :func:`~libfinance.instruments` returns ``None``
    **without raising**:

    .. code-block:: python

        >>> instruments("600000")      # no suffix
        None

    So when you get ``None``, check the spelling before concluding the security
    does not exist.

``order_book_id`` is the code, ``symbol`` is the name
=====================================================

These two are easy to swap. One example fixes it:

.. code-block:: python

    >>> from libfinance import instruments
    >>> ins = instruments("600000.XSHG")
    >>> ins.order_book_id
    '600000.XSHG'
    >>> ins.symbol
    '浦发银行'

A single code returns one
:class:`~libfinance.api.instrument.Instrument`; a list returns a list:

.. code-block:: python

    >>> instruments(["000001.XSHE", "000300.XSHG"])
    [Instrument(order_book_id='000001.XSHE', symbol='平安银行', type='CS',
                market='cn', listed_date='1991-04-03T00:00:00.000'),
     Instrument(order_book_id='000300.XSHG', symbol='沪深300', type='INDX',
                market='cn')]

Codes that cannot be resolved are **skipped** rather than returned as
placeholders, so the list may be shorter than what you passed in. If you need a
one-to-one mapping, build a dict keyed by ``order_book_id`` yourself.

The full universe
=================

:func:`~libfinance.all_instruments` returns every security:

.. code-block:: python

    >>> from libfinance import all_instruments
    >>> df = all_instruments(type="CS")
    >>> df.shape
    (10616, 6)
    >>> df.head(3)
      order_book_id symbol type market              listed_date  de_listed_date
    0   000001.XSHE   平安银行   CS     cn  1991-04-03T00:00:00.000             NaN
    1   000002.XSHE  万  科Ａ   CS     cn  1991-01-29T00:00:00.000             NaN
    2   000006.XSHE   深振业Ａ   CS     cn  1992-04-27T00:00:00.000             NaN

Values for ``type``:

.. list-table::
    :header-rows: 1
    :widths: 24 24 52

    *   - ``type``
        - Alias
        - Meaning
    *   - ``CS``
        - ``STOCK``
        - Common stock
    *   - ``INDX``
        - ``INDEX``
        - Index

For US equities pass ``market="us"``:

.. code-block:: python

    >>> us = all_instruments(market="us")
    >>> us[us["type"] == "EQTY"].head()

.. note::

    This table has ten thousand-plus rows and is not small, so the client caches
    it and invalidates the cache when the server's data changes. You do not need
    to cache it yourself; calling it repeatedly is cheap.

Delisted securities
===================

This is the easiest trap to fall into.

**Symptom**: you query a delisted stock over a range when it was still trading,
and get "invalid order book id".

**Cause**: a code must resolve to a security before its prices can be fetched. If
resolution happens against **today's** universe, codes that no longer exist today
resolve to nothing.

Take Haitong Securities (``600837.XSHG``, delisted 2025-03-04):

.. code-block:: python

    >>> instruments("600837.XSHG")            # as of today
    None

    >>> instruments("600837.XSHG", as_of="2022-09-20")   # as of 2022
    Instrument(order_book_id='600837.XSHG', symbol='海通证券', type='CS', market='cn',
               listed_date='1994-02-24T00:00:00.000',
               de_listed_date='2025-03-04T00:00:00.000')

**What to do**: :func:`~libfinance.get_price` resolves codes against the
``end_date`` you pass rather than today, so historical queries on delisted names
work with no extra effort:

.. code-block:: python

    >>> get_price(["600837.XSHG"], "2022-09-01", "2022-09-20").shape
    (13, 8)

You only need to pass a date explicitly when you validate codes yourself with
:func:`~libfinance.instruments`.

**Transferable rule**: any time you need to know whether a code existed at some
point in the past, say *when*. Not saying it means asking about today — and today
is not necessarily the world you are querying.
