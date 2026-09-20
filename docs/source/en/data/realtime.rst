=================
Live market data
=================

There are two paths to live data, for different purposes:

.. list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - Method
        - Entry point
        - When to use
    *   - Snapshot query
        - :func:`~libfinance.get_last_quotes`
        - Occasionally asking "what is the price now". One request, one answer
    *   - Streaming subscription
        - :class:`~libfinance.subscribe.quote_api.QuoteApi`
        - Continuously receiving updates as they happen

The two are **independent**: subscriptions go through a market data gateway on a
different address and port from the service :func:`~libfinance.init_client`
connects to. They merely share the
:class:`~libfinance.subscribe.md_protocol.Quote` type.

Snapshot queries
================

.. code-block:: python

    >>> from libfinance import get_last_quotes
    >>> get_last_quotes(["600000.XSHG"])
    {'600000.XSHG': Quote(...)}

Returns a dict keyed by code.

.. note::

    When no snapshot is currently available for a code — outside trading hours,
    or on a deployment with no live feed — the value is ``None``:

    .. code-block:: python

        >>> get_last_quotes(["600000.XSHG"])
        {'600000.XSHG': None}

    Check for ``None`` before reaching for ``.last_price``.

Streaming subscriptions
=======================

Subscriptions are **callback-based**: you implement a handler class, register it,
and your methods are called as data arrives.

.. code-block:: python

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

    class MySpi(QuoteSpi):
        def on_rsp_login(self, rsp, request_id):
            if rsp.error_id == 0:
                # Subscribe here, not in main — see below
                api.subscribe(["600519"], "XSHG")

        def on_depth_market_data(self, quote):
            print(quote.order_book_id, quote.last_price)

    api = QuoteApi()
    api.register_spi(MySpi())
    api.connect("gateway-host", 9001)
    api.login("user", "password")

.. important::

    **Subscribe inside ``on_rsp_login``.**

    After a disconnect the client reconnects and logs in again automatically, and
    a successful login fires ``on_rsp_login`` once more — so subscriptions placed
    there are replayed. Placed anywhere else, they are silently lost on
    reconnect: the program keeps running, the logs look fine, and no data ever
    arrives again.

    This is the contract of this API, not a style preference.

Two subscription modes
----------------------

.. list-table::
    :header-rows: 1
    :widths: 24 76

    *   - Mode
        - Behaviour
    *   - No ``source``
        - The gateway picks a source by health and priority, and fails over
          automatically when one drops
    *   - Explicit ``source``
        - Only that source is delivered, with no failover; if it is unhealthy the
          request fails explicitly

A contract has exactly one route on the gateway side, so the two modes **cannot be
mixed** for the same contract; conflicting requests fail explicitly in
``on_rsp_subscribe``.

Quote frames carry no source information. To know which source data came from,
read ``rsp.source`` on the subscription acknowledgement, or call
``query_sources()``.

``Quote`` fields
================

.. list-table::
    :header-rows: 1
    :widths: 34 66

    *   - Field
        - Meaning
    *   - ``order_book_id``
        - Code (read-only property built from ``instrument_id`` and ``exchange_id``)
    *   - ``data_time``
        - Quote timestamp
    *   - ``last_price``
        - Last traded price
    *   - ``open_price`` / ``high_price`` / ``low_price`` / ``close_price``
        - Open, high, low, close
    *   - ``pre_close_price``
        - Previous close
    *   - ``volume`` / ``turnover``
        - Volume and turnover
    *   - ``upper_limit_price`` / ``lower_limit_price``
        - Price limits
    *   - ``bid_price`` / ``ask_price``
        - Ten levels of bid/ask prices, each a list of length 10
    *   - ``bid_volume`` / ``ask_volume``
        - Sizes at those levels
    *   - ``total_bid_volume`` / ``total_ask_volume``
        - Total bid and ask size
    *   - ``total_trade_num``
        - Number of trades
    *   - ``trading_phase_code``
        - Trading session phase
    *   - ``open_interest`` / ``pre_open_interest`` / ``settlement_price`` / ``iopv``
        - Futures and fund fields; normally zero for equities

.. warning::

    Callbacks run on the background receive thread. **Do not do slow work inside
    them** — it blocks the entire quote stream. Push to a queue and process on
    another thread.

A complete runnable example is in :doc:`../howto/subscribe`.
