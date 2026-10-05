========
字段字典
========

各接口返回的字段含义与单位。

行情
====

:func:`~libfinance.get_price` 返回的列：

..  list-table::
    :header-rows: 1
    :widths: 24 16 60

    *   - 字段
        - 单位
        - 含义
    *   - ``open`` / ``high`` / ``low`` / ``close``
        - 元
        - 开盘、最高、最低、收盘价。受 ``adjust_type`` 影响
    *   - ``volume``
        - 股
        - 成交量。\ **也受复权影响**\ （与价格反向缩放）
    *   - ``turnover``
        - 元
        - 成交额。不受复权影响
    *   - ``limit_up`` / ``limit_down``
        - 元
        - 涨停价、跌停价。美股为 ``NaN``

索引是 ``(order_book_id, datetime)``\ 。

证券主数据
==========

:func:`~libfinance.all_instruments` / :func:`~libfinance.instruments`\ ：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 证券代码，如 ``600000.XSHG``
    *   - ``symbol``
        - 证券名称，如 ``浦发银行``
    *   - ``type``
        - ``CS`` 股票 / ``INDX`` 指数
    *   - ``market``
        - ``cn`` / ``us``
    *   - ``listed_date``
        - 上市日期
    *   - ``de_listed_date``
        - 退市日期；仍在交易的为 ``NaN``

股本
====

:func:`~libfinance.get_shares`\ ，\ **所有字段单位均为股**\ ：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``total``
        - 总股本
    *   - ``total_a``
        - A 股总股本
    *   - ``circulation_a``
        - A 股流通股本
    *   - ``non_circulation_a``
        - A 股非流通股本
    *   - ``free_circulation``
        - 自由流通股本
    *   - ``preferred_shares``
        - 优先股

公司行动
========

分红（\ :func:`~libfinance.get_dividends`\ ）：

..  list-table::
    :header-rows: 1
    :widths: 30 70

    *   - 字段
        - 含义
    *   - ``ex_date``
        - 除权除息日，价格跳空发生在这天
    *   - ``record_date``
        - 股权登记日
    *   - ``payable_date``
        - 派发日
    *   - ``declaration_date``
        - 公告日
    *   - ``cash_per_share``
        - 每股派现
    *   - ``bonus_per_share``
        - 每股送股
    *   - ``transfer_per_share``
        - 每股转增
    *   - ``dist_kind`` / ``marker``
        - 分配类型与标记
    *   - ``currency``
        - 币种

拆股（\ :func:`~libfinance.get_splits`\ ）：\ ``ratio_from`` / ``ratio_to`` 读作
"``ratio_from`` 股变成 ``ratio_to`` 股"。

分拆（\ :func:`~libfinance.get_spinoffs`\ ，仅美股）：\ ``valuation_price`` 是估算价，
必须连着 ``valuation_basis`` 与 ``valuation_source`` 一起看。

财务
====

:func:`~libfinance.get_pit_financials_ex` 除了你请求的财务字段外，还带两列：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``info_date``
        - 这一版的披露日期，必定 ``<= as_of``
    *   - ``if_adjusted``
        - ``0`` 原始披露值，\ ``1`` 修订值

可用的财务字段名与因子名由服务端提供，不同部署可能不同。

指数与概念权重
==============

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``index_code`` / ``concept_id``
        - 指数代码 / 概念 id
    *   - ``date``
        - 权重对应的日期
    *   - ``order_book_id``
        - 成分股代码
    *   - ``weight``
        - 权重，同一天内加总为 1

实时行情
========

``Quote`` 的字段见 :doc:`../data/realtime`\ 。
