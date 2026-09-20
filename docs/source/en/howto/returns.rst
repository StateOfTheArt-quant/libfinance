==================
Computing returns
==================

**Goal**: derive returns from prices without contaminating them with ex-rights
events.

The conclusion first: **returns require adjusted prices**. With unadjusted prices,
every dividend and bonus issue becomes a fake decline.

A concrete example
==================

``600000.XSHG`` went ex-dividend on 2024-07-18, paying 0.321 per share. Put the
two bases side by side:

.. code-block:: python

    import pandas as pd
    from libfinance import get_price

    raw = get_price(["600000.XSHG"], "2024-07-15", "2024-07-22",
                    adjust_type="none")["close"].droplevel(0)
    adj = get_price(["600000.XSHG"], "2024-07-15", "2024-07-22")["close"].droplevel(0)

    out = pd.DataFrame({"raw": raw, "adjusted": adj})
    out["raw_return"] = out["raw"].pct_change()
    out["adjusted_return"] = out["adjusted"].pct_change()

.. code-block:: text

                 raw  adjusted  raw_return  adjusted_return
    datetime
    2024-07-15  8.88  7.937594         NaN              NaN
    2024-07-16  8.86  7.919716   -0.002252        -0.002252
    2024-07-17  9.04  8.080613    0.020316         0.020316
    2024-07-18  8.77  8.127879   -0.029867         0.005849     <- ex-date
    2024-07-19  8.73  8.090808   -0.004561        -0.004561
    2024-07-22  8.58  7.951791   -0.017182        -0.017182

Look at 2024-07-18: unadjusted says **down 2.99%**, adjusted says **up 0.58%**.

It actually went up. Almost all of that 2.99% "decline" is the 0.321 paid out —
money moved from the share price into shareholders' pockets, not a loss.

Every other day the two agree **exactly** — adjustment only changes returns on days
with events.

Multiple stocks
===============

Prices come back with a two-level index; ``unstack`` to a wide frame and compute:

.. code-block:: python

    from libfinance import get_price

    close = get_price(["000001.XSHE", "600000.XSHG"],
                      "2024-03-01", "2024-03-08")["close"]
    wide = close.unstack("order_book_id")
    returns = wide.pct_change()

.. code-block:: text

    >>> wide
    order_book_id  000001.XSHE  600000.XSHG
    datetime
    2024-03-01          8.8130       6.3554
    2024-03-04          8.6786       6.3197
    2024-03-05          8.7626       6.4001
    2024-03-06          8.6786       6.3644
    2024-03-07          8.7206       6.3823
    2024-03-08          8.7206       6.3644

    >>> returns
    order_book_id  000001.XSHE  600000.XSHG
    datetime
    2024-03-01             NaN          NaN
    2024-03-04       -0.015253    -0.005626
    2024-03-05        0.009681     0.012730
    2024-03-06       -0.009588    -0.005587
    2024-03-07        0.004840     0.002809
    2024-03-08        0.000000    -0.002801

Common mistakes
===============

.. list-table::
    :header-rows: 1
    :widths: 34 66

    *   - Practice
        - Note
    *   - Using ``close * volume`` as turnover
        - **Don't.** Use the ``turnover`` column. Under adjustment both ``close``
          and ``volume`` are rescaled; the product is conserved, but the column is
          already there
    *   - Forward adjustment over long spans
        - Forward adjustment is anchored to the most recent price, so **each new
          ex-rights event shifts the whole historical series**. For an equity
          curve that does not move under you, use ``adjust_type="post"``
    *   - Suspended days
        - Kept by default (zero volume), producing zero returns. Pass
          ``skip_suspended=True`` to drop them
    *   - First row is ``NaN``
        - Normal for ``pct_change()``; use ``.dropna()``

A note on back-adjustment
=========================

Back-adjustment compounds factors from the earliest basis date. For some names,
early corporate actions cannot be priced, and the server **refuses** rather than
returning a skewed result, naming the date from which it is safe:

.. code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", adjust_type="post")
    RpcError: ... has 11 corporate action(s) with no factor in this release ...;
    Ask from base_date=1999-10-18 onward, ...

Re-query from the date it gives you.
