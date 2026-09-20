=========
Changelog
=========

Only changes that alter the behaviour of **existing code** are listed.

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
    *   - :func:`~libfinance.get_concept_weights` argument renamed
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
