==========
Quickstart
==========

A complete path in five minutes: **establish the sessions, then the securities,
then the prices**.

That order matters. The trading calendar and the security master are the frame of
reference for everything else: dates must land on sessions, and codes must resolve
to real securities, or the final step comes back mysteriously empty.

.. note::

    Every output below is a real run. Dates and values depend on how current your
    service is — **do not copy the dates**.

Setup
=====

.. code-block:: python

    import libfinance

    libfinance.init_client(host="libfinance.tech", port=8080)

Step 1: sessions
================

.. code-block:: python

    >>> from libfinance import get_trading_dates
    >>> get_trading_dates("2024-05-11", "2024-05-20")
    DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                   '2024-05-17', '2024-05-20'],
                  dtype='datetime64[ns]', freq=None)

Note that 11 and 12 May (a weekend) and 18 and 19 May are absent. You pass
calendar dates; you get back only sessions.

Step 2: securities
==================

Codes are written ``<exchange code>.<market suffix>``: ``.XSHG`` for the Shanghai
exchange, ``.XSHE`` for Shenzhen, ``.US`` for US equities.

.. code-block:: python

    >>> from libfinance import instruments
    >>> instruments("600000.XSHG")
    Instrument(order_book_id='600000.XSHG', symbol='浦发银行', type='CS',
               market='cn', listed_date='1999-11-10T00:00:00.000')

``order_book_id`` is the code; ``symbol`` is the **name**. These two are easy to
mix up.

Step 3: prices
==============

.. code-block:: python

    >>> from libfinance import get_price
    >>> get_price(["000001.XSHE", "600000.XSHG"], "2024-03-01", "2024-03-06")

.. code-block:: text

                              open      high       low     close        volume      turnover
    order_book_id datetime
    000001.XSHE   2024-03-01  8.897049  8.905450  8.762627  8.813035  2.175959e+08  1.917689e+09
                  2024-03-04  8.779430  8.821436  8.670212  8.678613  1.971024e+08  1.719563e+09
                  2024-03-05  8.653409  8.796232  8.619804  8.762627  2.163123e+08  1.889144e+09
                  2024-03-06  8.737423  8.779430  8.678613  8.678613  1.601692e+08  1.396940e+09
    600000.XSHG   2024-03-01  6.373316  6.400132  6.346500  6.355438  3.292615e+07  2.094740e+08
                  2024-03-04  6.364377  6.364377  6.301806  6.319683  3.116322e+07  1.971570e+08
                  2024-03-05  6.301806  6.418009  6.292867  6.400132  4.671382e+07  2.976761e+08
                  2024-03-06  6.409071  6.453764  6.364377  6.364377  2.899600e+07  1.858478e+08

The result is a ``DataFrame`` indexed by ``(order_book_id, datetime)``. Take one
stock with ``df.loc["000001.XSHE"]``, one day with
``df.xs("2024-03-04", level="datetime")``.

.. important::

    Above, ``000001.XSHE`` closes at **8.81** on 2024-03-01 — but the price it
    actually traded at that day was **10.49**, because ``adjust_type`` defaults to
    ``"pre"`` (forward-adjusted).

    For the price as it actually traded, pass ``adjust_type="none"`` explicitly.
    This matters enough that :doc:`../data/price` is devoted to it.

Next
====

* :doc:`../howto/price_panel` — why "the last N sessions" is not one line, and how to write it
* :doc:`../data/price` — exactly which numbers adjustment changes
* :doc:`../data/index` — the semantics of each data set
