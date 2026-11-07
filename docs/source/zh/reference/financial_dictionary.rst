============
财务数据字典
============

:func:`~libfinance.get_pit_financials_ex` 可取的财务报表字段，与 :func:`~libfinance.get_financial_metrics` 可取的财务衍生指标。
两部分的表格分别由 financialstatement 的统一概念目录和 financialmetrics 的公式目录生成；PIT 语义见 :doc:`../data/fundamentals`\ 。
所连接的服务可能只部署了其中一部分。

财务报表
========

``fields`` 取下表"字段"列的值，三张报表的字段可以在一次查询里混合。CN 与 US 用同一套字段名，只在一个市场存在的科目在"市场"列标出，
其他市场查询结果恒为 ``NaN``\ 。

..  list-table::
    :header-rows: 1
    :widths: 18 82

    *   - 列
        - 含义
    *   - 期间
        - 时点：资产负债表日余额；期间：年初至报告期末的累计发生额（US 10-Q 同时给单季与年初至今时取年初至今）
    *   - 单位
        - 金额为报告币种的元，不做万元 / 亿元换算；每股为元/股；股数为股
    *   - 行业
        - 适用的报表模板：一般、银行、保险、证券；"全部"表示四类都适用
    *   - 市场
        - 有该科目的法域

符号：费用、支出、现金流出一律以正数表示，收益、流入为正；净额科目按"净增加"口径，减少为负。
报告期按期末的名义月末归入自然季度，52/53 周财年的期末 2023-07-01 归 ``2023q2``\ 。

..  include:: ../../../_shared/tables/financials/income_statement.zh.rst

..  include:: ../../../_shared/tables/financials/balance_sheet.zh.rst

..  include:: ../../../_shared/tables/financials/cash_flow_statement.zh.rst

财务衍生指标
============

每个交易日的值，是那一天收盘后（证券所在市场时区）能看到的最新报告算出的指标：数值在公告日跳变、其间持平。
最新报告算不出的（缺输入、分母为零）为 ``NaN``\ ，不拿更早的报告顶替。

..  list-table::
    :header-rows: 1
    :widths: 18 82

    *   - 后缀 / 期间
        - 含义
    *   - ``lf``
        - 最新报告期的值
    *   - ``ttm``
        - 最近四季合计：当前年初至今 + 上一财年全年 − 上年同期年初至今
    *   - ``mrq``
        - 最近单季：年初至今减同财年上一季的年初至今
    *   - ``lyr``
        - 最近一个财年（须在最近 12 个月内结束）；\ ``*_growth_lyr`` 为当前值 / 上年同期 − 1
    *   - ``5y``
        - 最近 5 个连续财年（余额为本期与此前 4 年同期），缺一年即缺失
    *   - average
        - ``roa_lf``\ 、\ ``roe_lf`` 的分母为本期与上一季度期末余额的平均
    *   - 日频
        - 估值与每股字段，用当日未复权收盘价、总股本（\ ``issued_shares``\ ）与流通股本，目前只有 CN

来源："通用"为常用财务衍生指标；"Barra 输入"为 Barra CNE5 / CNE6 描述符的财务输入；"行情 + 股本"为估值与每股字段。
公式中的名字是上文的报表字段。

..  include:: ../../../_shared/tables/financials/metrics-valuation.zh.rst

..  include:: ../../../_shared/tables/financials/metrics-operating.zh.rst

..  include:: ../../../_shared/tables/financials/metrics-cashflow.zh.rst

..  include:: ../../../_shared/tables/financials/metrics-financial.zh.rst

..  include:: ../../../_shared/tables/financials/metrics-growth.zh.rst
