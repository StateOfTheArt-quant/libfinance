=========
Changelog
=========

Only changes that alter the behaviour of **existing code** are listed.

0.1.3 (2026-10-10)
==================

.. danger::

    **Results no longer carry the server's internal identities:** a security is named by ``order_book_id``
    only (contract 3.0.0, libfinanceserver v0.1.10 or later).

    - ``get_price``, ``all_instruments``, ``get_ex_factor`` and ``get_index_weights`` drop the ``permanent_id`` column.
    - ``get_dividends`` / ``get_splits`` / ``get_allotments`` / ``get_spinoffs`` drop ``permanent_id``, ``event_id`` and
      ``confirmed_by_revision``; ``get_spinoffs`` also drops ``child_permanent_id`` (``child_symbol`` still names the child).
    - The ``Instrument`` from ``instruments`` no longer has ``permanent_id``, ``listing_id`` or ``identity_quality``;
      C++ removes ``Instrument::permanent_id()``.
    - Code that joined or deduplicated on these columns uses ``order_book_id``; ``as_of`` resolves historical identity.

.. danger::

    **Live quotes name a security by order_book_id only:** the quote gateway protocol is now v4,
    incompatible with older gateways (dynamics protocol v4).

    - ``Quote`` and the trade / order / tick / depth records, subscription receipts (``SubRsp``) and gap
      notices (``SequenceGap``) carry one identity field, ``order_book_id``; ``instrument_id``,
      ``exchange_id`` and ``instrument_type`` are gone. ``get_last_quotes`` snapshots likewise.
    - In C++, ``order_book_id`` is a field instead of the method ``order_book_id()``.
    - For the kind of security, look up ``type`` with :func:`~libfinance.instruments`.

0.1.2 (2026-10-10)
==================

No change to existing behaviour. Adds the daily factor functions ``get_factor_exposure``, ``list_factor_libraries``
and ``list_factors`` (qlib, alpha158, Barra CNE5 / CNE6); they need libfinanceserver v0.1.9 or later.

0.1.1 (2026-10-05)
==================

The first 0.1 release on PyPI (0.1.0 was tagged, never published). Changes since 0.0.6 on PyPI:

.. danger::

    **Live subscription takes the unified order_book_id:** ``QuoteApi.subscribe(instruments, exchange_id, source="")``
    → ``subscribe(order_book_ids, *, source="")`` (``unsubscribe`` likewise).

    - ``api.subscribe(["600519"], "XSHG")`` → ``api.subscribe(["600519.XSHG"])``; exchanges may be mixed.
    - ``source`` is keyword-only: the old call's second positional argument raises ``TypeError`` instead of being
      taken silently as a source name.
    - A code without a suffix, or with one the gateway does not serve, raises ``ValueError`` before any request.
    - Subscription receipts, trade / order / tick / depth records and gap notices carry ``order_book_id``.
    - The C++ client gains the same ``libfinance::QuoteApi`` / ``QuoteSpi`` (``libfinance/quote_api.hpp``).

.. danger::

    **The industry functions follow the new industry data families:** ``get_industry`` and
    ``get_industry_mapping`` are removed.

    - An industry is named by an ``order_book_id`` (``801780.SW``, ``10.GICS``); ``source`` is the
      classification (``SW``, ``GICS``, ...).
    - ``get_industry(industry, source, date, market)`` → ``get_industry_constituents(order_book_id, as_of=None)``.
    - ``get_instrument_industry(order_book_ids, date, source="sw", level=1)`` →
      ``get_instrument_industry(order_book_ids, source=None, level=None, as_of=None)``: omitting ``source`` /
      ``level`` means all of them; the result is a long table ``order_book_id, related_order_book_id, source,
      market, level`` instead of the ``first_industry_code`` wide table.
    - New ``get_industry_weights(order_book_id, as_of=None)``, each row with its ``methodology``.
    - Listing industry nodes (formerly ``get_industry_mapping``) comes with the cross-type
      ``all_instruments(type=...)``.

.. danger::

    **Live subscription (``libfinance.subscribe``) now speaks gateway protocol v3 and
    is incompatible with older gateways.**

    - ``QuoteApi.login(user_id, password)`` is gone: **no login is needed**. ``connect()``
      fetches a market data ticket from the service (a basic per-IP allowance without
      login) and renews it before expiry; ``login(token)`` is only for supplying your own ticket.
    - Without an address, ``connect()`` uses the gateway address returned with the ticket;
      ``connect("host:port,host:port")`` still works.
    - Quote callbacks take a second argument: ``on_depth_market_data(quote, envelope)``,
      where ``envelope`` is the gateway's sequencing envelope (sequence numbers and
      timestamps). The old one-argument form raises ``TypeError``.
    - ``LoginRsp`` drops ``user_level`` and echoes the allowance instead
      (``max_subscriptions``, ``sub_all``, ``expires_at_ms``, …).
    - Whole-market subscription now depends on the allowance including it, not on an
      unlimited quota (otherwise ``error_id=8``).
    - New: re-sending missed records by sequence number after a reconnect,
      ``on_sequence_gap``, ``on_stream_status``, ``on_rsp_reauth``, ``on_session_closed``,
      and callbacks for trades, orders, tick and depth data.

0.0.6
=====

.. danger::

    **The ``adjust_type`` default on ``get_price`` changed from ``"none"`` to
    ``"pre"``, and ``skip_suspended`` from ``True`` to ``False``.**

    This is a **silent numerical change**: nothing fails, but without an explicit
    ``adjust_type`` your prices switch from unadjusted to forward-adjusted. Code
    relying on the old behaviour should state ``adjust_type="none"``.

    The reason: the client and server defaults used to be opposites — the same
    semantic call returned different numbers depending on which path it took, and
    nothing in the docs revealed the inconsistency.

Other changes:

.. list-table::
    :header-rows: 1
    :widths: 32 68

    *   - Change
        - Notes
    *   - :func:`~libfinance.get_price_coverage` takes ``market``
        - Once the server bound both CN and US, omitting ``market`` raised
          ``AmbiguousMarketError``. It now defaults to ``"cn"`` and supports
          ``"us"``
    *   - ``frequency`` validation in :func:`~libfinance.get_price`
        - Unsupported frequencies used to **return** an exception object instead of
          raising it, so callers hit an unrelated error later. It now raises
          ``ValueError`` properly
    *   - :func:`~libfinance.get_index_weights` argument renamed
        - ``index_id`` → ``index_code``
    *   - ``get_concept_weights`` (since removed) argument renamed
        - ``date`` → ``as_of``. The old name still works but emits a
          ``DeprecationWarning`` — the server separates "knowledge cutoff"
          (``as_of``) from "data date" (``date``), and they mean different things;
          see :doc:`../data/point_in_time`
    *   - Default ``source`` for :func:`~libfinance.get_instrument_industry`
        - Changed from ``"010303"`` to ``"sw"``. The server never accepted the
          former, so calling this function with defaults always failed
    *   - Out-of-range calendar queries
        - Raise ``CalendarCoverageError`` instead of silently returning a shortened
          result; stepping N sessions past the edge raises rather than returning
          the endpoint

0.0.2
=====

See the ``adjust_type`` note under 0.0.6 — that change took effect in 0.0.2.
