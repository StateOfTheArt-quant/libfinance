=======================
Understanding the data
=======================

This part is about **semantics**: what each data set is, where its boundaries are,
and which defaults change the numbers you compute.

Skip it and your code still runs — only the results are wrong, with nothing to
warn you. So even if you only want data quickly, skim the summary boxes in
:doc:`price` and :doc:`freshness` first.

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Chapter
        - The mistake it prevents
    *   - :doc:`instruments`
        - Correct-looking codes that resolve to nothing; delisted stocks "vanishing"
    *   - :doc:`calendar`
        - Treating a non-session as a session; ranges silently shrinking
    *   - :doc:`price`
        - Using adjusted prices while believing they are traded prices
    *   - :doc:`freshness`
        - Passing today as ``end_date`` and having the whole query rejected
    *   - :doc:`point_in_time`
        - A backtest that reads financials nobody had published yet
    *   - :doc:`corporate_actions`
        - Mistaking an ex-rights gap for bad data
    *   - :doc:`fundamentals`
        - Misreading quarterly semantics and units
    *   - :doc:`universe`
        - A stock universe that leaks future information
    *   - :doc:`realtime`
        - Subscriptions quietly lost after a reconnect

.. toctree::
    :maxdepth: 1

    instruments
    calendar
    price
    freshness
    point_in_time
    corporate_actions
    fundamentals
    universe
    realtime
