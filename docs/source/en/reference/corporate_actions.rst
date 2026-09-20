=================
Corporate actions
=================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/corporate_actions`. All four functions take
identical arguments.

.. py:function:: get_dividends(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None, market=None)

    Cash dividend events.

    :param order_book_ids: One code or a list
    :param start_date: Start date, filtering on ``ex_date``; omit for the earliest
    :param end_date: End date; omit for the latest
    :param fields: Which columns; omit for all
    :param as_of: Use the information **known** at that point; omit for the latest
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` of events

    Key columns: ``ex_date`` (the price gap happens here), ``record_date``,
    ``payable_date``, ``declaration_date``, ``cash_per_share``,
    ``bonus_per_share``, ``transfer_per_share``.

.. py:function:: get_splits(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None, market=None)

    Splits and bonus issues. Arguments as for :py:func:`get_dividends`.

    ``ratio_from`` / ``ratio_to`` read as "``ratio_from`` shares become
    ``ratio_to`` shares".

.. py:function:: get_allotments(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None, market=None)

    Rights issues. Arguments as for :py:func:`get_dividends`.

.. py:function:: get_spinoffs(order_book_ids, start_date=None, end_date=None, fields=None, as_of=None, market=None)

    Spin-off events, **US only**. Arguments as for :py:func:`get_dividends`.

    Parent shareholders receive subsidiary shares pro rata. Ex-rights needs an
    amount, but the subsidiary often has no independent market price on the
    ex-date, so ``valuation_price`` is **estimated** — read it together with
    ``valuation_basis`` and ``valuation_source``. ``d_spin_per_share`` is the value
    attributed to each parent share.

    A-share codes yield a "market not bound" error, which is not "no spin-offs in
    this period".
