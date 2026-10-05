=========================
Prices and adjustment
=========================

:func:`~libfinance.get_price` returns daily bars. This chapter exists to make one
thing clear: **the prices you get are usually not the prices that traded.**

.. code-block:: python

    >>> from libfinance import get_price
    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")

.. code-block:: text

                              open      high       low     close        volume      turnover
    order_book_id datetime
    000001.XSHE   2024-03-01  8.897049  8.905450  8.762627  8.813035  2.175959e+08  1.917689e+09
                  2024-03-04  8.779430  8.821436  8.670212  8.678613  1.971024e+08  1.719563e+09
                  2024-03-05  8.653409  8.796232  8.619804  8.762627  2.163123e+08  1.889144e+09
                  2024-03-06  8.737423  8.779430  8.678613  8.678613  1.601692e+08  1.396940e+09

The result is indexed by ``(order_book_id, datetime)``.

Columns
=======

.. list-table::
    :header-rows: 1
    :widths: 20 80

    *   - Column
        - Meaning
    *   - ``open`` / ``high`` / ``low`` / ``close``
        - Open, high, low and close
    *   - ``volume``
        - Volume, in shares
    *   - ``turnover``
        - Turnover, in currency
    *   - ``limit_up`` / ``limit_down``
        - Daily price limits (A-shares only; ``NaN`` for US equities)

Omit ``fields`` for everything, or name the columns you want:

.. code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", fields=["close", "volume"])

Adjustment: the section that decides whether your numbers are right
===================================================================

After a dividend or a bonus issue, the price **gaps down**. That is not a decline;
it is less equity per share. Computing returns from unadjusted prices turns every
such gap into a fake loss.

Adjustment rescales historical prices onto one basis so that returns are
continuous.

Three settings
--------------

.. list-table::
    :header-rows: 1
    :widths: 14 22 64

    *   - Value
        - Name
        - When to use it
    *   - ``"pre"``
        - Forward-adjusted (**default**)
        - Returns, continuous price series, factor research. The recent price is
          the basis; history is rescaled.
    *   - ``"none"``
        - Unadjusted
        - The price as it **actually traded**: reconstructing the tape, checking
          price limits, computing period-accurate costs.
    *   - ``"post"``
        - Back-adjusted
        - The earliest price is the basis, compounding forward. Useful for
          long-horizon equity curves.

How big is the difference
-------------------------

Same stock, same day, two settings:

.. code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")["close"]              # default, pre
    8.813035
    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06",
    ...           adjust_type="none")["close"]                                        # unadjusted
    10.49

16%. **No error, no warning** — so if you believed you were holding the traded
price, every number downstream of this point is wrong.

.. danger::

    The default for ``adjust_type`` changed from ``"none"`` to ``"pre"`` in
    **0.0.2**.

    That is a **silent numerical change**: after upgrading, the same code does not
    fail, but prices switch from unadjusted to forward-adjusted. Code that relies
    on the old behaviour should state ``adjust_type="none"`` explicitly.

Volume is adjusted; turnover is not
-----------------------------------

This is the part people miss. Forward adjustment scales prices **down**, so the
share count for the same trade must scale **up** — otherwise ``price × volume``
would no longer equal the money that actually changed hands.

Verified on the data above:

.. code-block:: python

    >>> pre  = get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")
    >>> none = get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", adjust_type="none")

    >>> (pre["close"] * pre["volume"] - none["close"] * none["volume"]).abs().max()
    0.005468130111694336          # price x volume is conserved (floating-point noise)

    >>> (pre["turnover"] == none["turnover"]).all()
    True                          # turnover is already money; it is not adjusted

Therefore:

* for **traded value**, use ``turnover`` directly, not ``close * volume``;
* when comparing ``volume`` **across dates**, remember it has been rescaled.

Back-adjustment can be refused
------------------------------

Back-adjustment compounds factors from the earliest basis date. If some historical
corporate action has **no factor**, a cumulative factor spanning it would be off by
a constant — so the server refuses rather than returning a skewed number:

.. code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", adjust_type="post")
    RpcError: ... has 11 corporate action(s) with no factor in this release at
    1991-05-02, 1991-08-17, 1992-03-23, ...; a cumulative factor spanning them
    would be wrong by a constant. Ask from base_date=1999-10-18 onward, ...

The message tells you **which date is safe to start from**. A name without this
problem works normally:

.. code-block:: python

    >>> get_price(["600000.XSHG"], "2024-03-01", "2024-03-06", adjust_type="post")["close"]
    110.531242

Suspensions
===========

Suspended days carry zero volume in the raw data. ``skip_suspended=True`` drops
them:

.. code-block:: python

    >>> get_price(ids, start, end, skip_suspended=True)

The default is ``False``, i.e. suspended days are kept. Keeping them is more
convenient for panel alignment (every name shares one date axis); when computing
turnover ratios, remember to exclude zero-volume days.

Known limits
============

.. warning::

    **Daily bars only.** ``frequency`` currently accepts ``"1d"`` alone. Anything
    else is rejected outright — never silently downgraded:

    .. code-block:: python

        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-29", frequency="5d")
        RpcError: frequency='5d' 不支持；上游目前只有日频 artifact，可选 ['1d']

        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-29", frequency="1m")
        ValueError: frequency: 目前只支持日频 '1d'，收到 '1m'

.. warning::

    **Indices do not work through this function.** Passing an index code returns an
    **empty table**, with no warning at all:

    .. code-block:: python

        >>> get_price(["000300.XSHG"], "2024-03-01", "2024-03-08").shape
        (0, 0)

    When you get an empty table, check first that you passed a stock code. For
    index constituents and weights use :func:`~libfinance.get_index_weights`;
    see :doc:`universe`.

.. note::

    ``include_now`` has **no effect** on daily data; it is retained only for
    signature compatibility.

US equities
===========

Same function, just the ``.US`` suffix — no extra argument:

.. code-block:: python

    >>> get_price(["AAPL.US"], "2026-03-02", "2026-03-06")[["close", "volume"]]

US equities have no price limits, so ``limit_up``, ``limit_down`` and ``turnover``
come back as ``NaN``. See :doc:`../howto/us_market` for the full list of
differences.

Next
====

Now that you can fetch prices, you need to know **how recent they are** — see
:doc:`freshness`.
