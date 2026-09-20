=================
Live market data
=================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/realtime`.

Snapshots
=========

.. py:function:: get_last_quotes(order_book_ids)

    The latest snapshot for each code.

    :param order_book_ids: List of codes
    :returns: ``dict`` keyed by code, with
        :py:class:`~libfinance.subscribe.md_protocol.Quote` values. A value is
        ``None`` when no snapshot is currently available — outside trading hours,
        or on a deployment with no live feed.

    .. code-block:: python

        >>> get_last_quotes(["600000.XSHG"])
        {'600000.XSHG': None}

Subscriptions
=============

.. currentmodule:: libfinance.subscribe.quote_api

.. py:class:: QuoteApi(auto_reconnect=True)

    Client for the market data gateway. Reconnects and logs in again automatically
    after a disconnect.

    .. py:method:: register_spi(spi)

        Register the callback handler, an instance of :py:class:`~libfinance.subscribe.quote_api.QuoteSpi`.

    .. py:method:: connect(ip, port, timeout=3.0)

        Connect to the gateway. Returns ``0`` on success, ``-1`` on failure.

    .. py:method:: login(user_id, password)

        Log in. Credentials are remembered and replayed after a reconnect.

    .. py:method:: subscribe(instruments, exchange_id, source="")

        Subscribe to contracts. ``instruments`` carry **no suffix**; the exchange
        is given separately. An empty ``source`` lets the gateway pick and fail
        over; a named source disables failover.

        Call this inside ``on_rsp_login`` so it is replayed after a reconnect.

    .. py:method:: unsubscribe(instruments, exchange_id, source="")

        Cancel a subscription.

    .. py:method:: subscribe_all(market=0, instrument_type=0, data_type=0)

        Subscribe to everything matching market × instrument type × data type.
        ``0`` means unrestricted on that axis. Requires an unlimited quota.

    .. py:method:: unsubscribe_all()

        Cancel every whole-market subscription on this connection. Per-contract
        subscriptions are unaffected.

    .. py:method:: query_sources()

        Query the source directory. The answer arrives via
        ``on_rsp_query_sources``.

    .. py:method:: disconnect()

        Disconnect and stop the background threads.

.. py:class:: QuoteSpi

    Callback base class. Subclass it and override what you need. Callbacks run on
    the background receive thread, so do no slow work inside them.

    Methods: ``on_connected``, ``on_disconnected(reason)``,
    ``on_rsp_login(rsp, request_id)``, ``on_rsp_subscribe(rsp, request_id)``,
    ``on_rsp_unsubscribe(rsp, request_id)``,
    ``on_rsp_subscribe_all(rsp, request_id)``,
    ``on_rsp_unsubscribe_all(rsp, request_id)``,
    ``on_rsp_query_sources(sources, request_id)``,
    ``on_depth_market_data(quote)``, ``on_heartbeat``.

.. currentmodule:: libfinance.subscribe.md_protocol

.. py:class:: Quote

    One market data snapshot. Fields are listed in :doc:`../data/realtime`.
