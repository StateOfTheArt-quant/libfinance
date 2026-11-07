=========================
Financial data dictionary
=========================

The statement fields :py:func:`~libfinance.get_pit_financials_ex` accepts and the financial metrics
:py:func:`~libfinance.get_financial_metrics` accepts. The tables are generated from financialstatement's unified
concept catalog and financialmetrics' formula catalog, with notes in Chinese; point-in-time semantics:
:doc:`../data/fundamentals`. A server may deploy only part of them.

Financial statements
====================

Pass the values of the Field column as ``fields``; fields of the three statements can be mixed in one query.
CN and US share one set of field names. A line item that exists in one market only says so in the Market column
and is always ``NaN`` elsewhere.

..  list-table::
    :header-rows: 1
    :widths: 18 82

    *   - Column
        - Meaning
    *   - Period
        - instant: balance at the balance-sheet date; duration: cumulative from the start of the fiscal year
          (where a US 10-Q gives both the quarter and the year to date, the year to date)
    *   - Unit
        - Amounts in units of the reporting currency, not in thousands or millions; per-share amounts per share;
          share counts in shares
    *   - Industry
        - The statement templates it applies to: general, bank, insurance, broker; "all" for all four
    *   - Market
        - The jurisdictions that report it

Signs: expenses, costs and cash outflows are positive, as are income and inflows; net items are net increases,
negative when they decrease. A report period falls in the calendar quarter of its nominal month end: a 52/53-week
period ending 2023-07-01 is ``2023q2``.

Income statement
----------------

..  include:: ../../../_shared/tables/financials/income_statement.en.rst

Balance sheet
-------------

..  include:: ../../../_shared/tables/financials/balance_sheet.en.rst

Cash flow statement
-------------------

..  include:: ../../../_shared/tables/financials/cash_flow_statement.en.rst

Financial metrics
=================

A session's value is the metric of the latest report visible at the end of that day (in the security's market
time zone): values step on announcement days and stay flat in between. A metric the latest report cannot give
(missing input, zero denominator) is ``NaN``; an older report never stands in. The categories are RQData's.

..  list-table::
    :header-rows: 1
    :widths: 18 82

    *   - Suffix / period
        - Meaning
    *   - ``lf``
        - The latest report period
    *   - ``ttm``
        - Trailing four quarters: year to date + last fiscal year − the year-ago year to date
    *   - ``mrq``
        - The latest single quarter: year to date minus the previous quarter's year to date
    *   - ``lyr``
        - The latest fiscal year (ended within the last 12 months); ``*_growth_lyr`` is current / year-ago − 1
    *   - ``5y``
        - The last 5 consecutive fiscal years (balances: this period and the same period of the 4 years before);
          one missing year makes it missing
    *   - average
        - ``roa_lf`` and ``roe_lf`` divide by the average of this and the previous quarter-end balance
    *   - daily
        - Valuation and per-share fields from the session's unadjusted close, issued shares and float shares; CN only

Source: "RQData" has RQData's name and definition; "Barra input" is a financial input of the Barra CNE5 / CNE6
descriptors; "market data" is a valuation or per-share field. Names in the formulas are the statement fields above.

Valuation
---------

..  include:: ../../../_shared/tables/financials/metrics-valuation.en.rst

Operating
---------

..  include:: ../../../_shared/tables/financials/metrics-operating.en.rst

Cash flow
---------

..  include:: ../../../_shared/tables/financials/metrics-cashflow.en.rst

Financial
---------

..  include:: ../../../_shared/tables/financials/metrics-financial.en.rst

Growth
------

..  include:: ../../../_shared/tables/financials/metrics-growth.en.rst
