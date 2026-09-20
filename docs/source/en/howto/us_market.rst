=====================
Querying US equities
=====================

**Goal**: know what US data is available, how the calls differ from A-shares, and
which functions have no US data at all.

Three differences
=================

1. **The suffix is** ``.US``, as in ``AAPL.US``, ``NVDA.US``.
2. **Calendar functions need** ``market="us"``.
3. **Price calls do not need ``market``** — the suffix already says which market.

.. code-block:: python

    from libfinance import get_trading_dates, all_instruments, get_price

    get_trading_dates("2024-01-01", "2024-01-31", market="us")   # needs market
    all_instruments(market="us")                      # needs market
    get_price(["AAPL.US"], "2026-03-02", "2026-03-06")           # does not

What has US data
================

The table below is the result of calling each function against one live
deployment. Yours may differ — trust the error message: the server says plainly
that a namespace has no US provider, rather than returning an empty table.

.. list-table::
    :header-rows: 1
    :widths: 34 12 54

    *   - Function
        - US
        - Notes
    *   - :func:`~libfinance.get_trading_dates` and other calendar calls
        - ✅
        - Pass ``market="us"``
    *   - :func:`~libfinance.all_instruments` / :func:`~libfinance.instruments`
        - ✅
        - Stocks (``CS``) yes; indices return 0 rows
    *   - :func:`~libfinance.get_price`
        - ✅
        - ``turnover``, ``limit_up``, ``limit_down`` are ``NaN``
    *   - :func:`~libfinance.get_dividends`
        - ✅
        -
    *   - :func:`~libfinance.get_splits`
        - ✅
        -
    *   - :func:`~libfinance.get_spinoffs`
        - ✅
        - **US only**; A-shares do not produce these events
    *   - :func:`~libfinance.get_shares`
        - ❌
        - "namespace 'shares' has no provider for market='us'"
    *   - :func:`~libfinance.get_pit_financials_ex` / :func:`~libfinance.get_factor`
        - ❌
        - See the warning below
    *   - :func:`~libfinance.get_index_weights`
        - ❌
        - No US indices
    *   - :func:`~libfinance.get_instrument_industry` / :func:`~libfinance.get_industry`
        - ❌
        - "unsupported A-share symbol"

.. warning::

    **The financial functions give an unhelpful error for US codes.** Calling
    :func:`~libfinance.get_factor` with a US code yields:

    .. code-block:: text

        RpcError: Array type doesn't match type of values set: string vs null

    Nothing there says "no US financials". If you hit it, don't start debugging
    your arguments — first check whether the function has US data on your
    deployment.

No price limits
===============

.. code-block:: python

    >>> get_price(["AAPL.US"], "2026-03-02", "2026-03-06")

.. code-block:: text

                                     low        open        high        volume  \
    order_book_id datetime
    AAPL.US       2026-03-02  259.960487  262.168453  266.284660  4.186648e+07
                  2026-03-03  259.890551  263.237468  265.315553  3.860446e+07
                  2026-03-04  261.179364  264.406391  265.905010  3.983979e+07

                              turnover  limit_up       close  limit_down
    order_book_id datetime
    AAPL.US       2026-03-02       NaN       NaN  264.476326         NaN
    ...

``turnover``, ``limit_up`` and ``limit_down`` are all ``NaN`` — US equities have no
price limits, and this deployment does not supply turnover. Traded value has to be
approximated as ``close * volume``.

Coverage is tracked separately
==============================

US and A-share upper bounds are **independent**:

.. code-block:: python

    >>> from libfinance import get_price_coverage
    >>> get_price_coverage(market="us")
    {'US': {'start': None, 'end': '2026-08-21',
            'raw_end': None, 'adjust_cutoff': '2026-08-21'}}

Note that ``start`` and ``raw_end`` are ``None``: US upstream data is partitioned
by month, so there is no day-level bound and none is invented here. The bound for
adjusted prices comes from the adjustment cutoff, which is exact.

Names are full English names
============================

.. code-block:: python

    >>> from libfinance import instruments
    >>> instruments(["AAPL.US", "NVDA.US"])
    [Instrument(order_book_id='AAPL.US', symbol='Apple Inc. - Common Stock',
                type='CS', market='us'),
     Instrument(order_book_id='NVDA.US', symbol='NVIDIA Corporation - Common Stock',
                type='CS', market='us')]

``symbol`` is the full name including a security-type suffix, not the ticker. The
ticker is in ``order_book_id`` minus the ``.US`` suffix.

Spin-offs: US only
==================

.. code-block:: python

    >>> from libfinance import get_spinoffs
    >>> get_spinoffs("AAPL.US", start_date="2000-01-01", end_date="2026-09-01")
    Empty DataFrame
    Columns: [order_book_id, event_id, ..., valuation_price, valuation_basis,
              valuation_source, d_spin_per_share]

Apple has no spin-offs, so the table is empty — **that is "no events"**. Calling
the same function with an A-share code gives a "market not bound" error, which
means "this market has no such data". Don't confuse the two.

Column meanings are in :doc:`../data/corporate_actions`.
