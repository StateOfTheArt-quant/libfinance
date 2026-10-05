========
公司行动
========

分红、送转、配股、分拆——这些事件是\ **价格跳空的来源**\ ，也是复权因子的成因。看到某只
股票某天"暴跌 10%"却查不到任何消息时，先来这里查一下那天是不是除权日。

四个接口的参数完全一样，只是取的事件类型不同：

..  list-table::
    :header-rows: 1
    :widths: 34 14 52

    *   - 函数
        - 市场
        - 事件
    *   - :func:`~libfinance.get_dividends`
        - CN · US
        - 分红（派现）
    *   - :func:`~libfinance.get_splits`
        - CN · US
        - 拆股 / 送转
    *   - :func:`~libfinance.get_allotments`
        - CN · US
        - 配股
    *   - :func:`~libfinance.get_spinoffs`
        - **仅 US**
        - 分拆

分红
====

..  code-block:: python

    >>> from libfinance import get_dividends
    >>> get_dividends("600000.XSHG", start_date="2023-01-01", end_date="2026-09-01")

..  code-block:: text

      order_book_id    ex_date dist_kind   marker cash_per_share currency  \
    0   600000.XSHG 2023-07-21      CASH  REGULAR           0.32      CNY
    1   600000.XSHG 2024-07-18      CASH  REGULAR          0.321      CNY
    2   600000.XSHG 2025-07-16      CASH  REGULAR           0.41      CNY
    3   600000.XSHG 2026-07-16      CASH  REGULAR           0.42      CNY

      bonus_per_share transfer_per_share  declaration_date record_date payable_date
    0             0.0                0.0        2023-07-13  2023-07-20   2023-07-21
    ...

几个关键字段：

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``ex_date``
        - **除权除息日**\ 。价格跳空发生在这一天
    *   - ``record_date``
        - 股权登记日，持有到这天收盘才有权
    *   - ``payable_date``
        - 派发日
    *   - ``declaration_date``
        - 公告日
    *   - ``cash_per_share``
        - 每股派现金额
    *   - ``bonus_per_share`` / ``transfer_per_share``
        - 每股送股 / 每股转增

拆股与送转
==========

..  code-block:: python

    >>> from libfinance import get_splits
    >>> get_splits("600000.XSHG", start_date="2000-01-01", end_date="2026-09-01")
      order_book_id    ex_date event_type ratio_from ratio_to record_date payable_date
    0   600000.XSHG 2006-05-12      SPLIT       10.0     13.0  2006-05-10   2006-05-12

``ratio_from`` / ``ratio_to`` 读作"10 股变成 13 股"。

分拆（仅美股）
==============

母公司股东按比例获得子公司股份。A 股的分拆上市走另一套流程，不产生这类除权事件。

..  warning::

    对 A 股代码调用 :func:`~libfinance.get_spinoffs`\ ，得到的是"该市场未绑定"的错误，
    **不是**"这段时间没有分拆"。两者含义完全不同。

分拆的估值列要连着口径一起看：除权需要一个金额，而子公司在除权当日往往还没有独立的
市场价格，所以 ``valuation_price`` 是\ **估算**\ 出来的。

..  list-table::
    :header-rows: 1
    :widths: 30 70

    *   - 字段
        - 含义
    *   - ``valuation_price``
        - 子公司股份的估值价
    *   - ``valuation_basis``
        - 按什么口径估的
    *   - ``valuation_source``
        - 估值来源
    *   - ``d_spin_per_share``
        - 折算到母公司每股的分拆价值
    *   - ``ratio_child_per_parent``
        - 每股母公司股份对应多少子公司股份

只取 ``valuation_price`` 而不看后两列，等于替这份数据假定了一个它并没有声明的口径。

共同参数
========

..  list-table::
    :header-rows: 1
    :widths: 22 78

    *   - 参数
        - 说明
    *   - ``order_book_ids``
        - 单个代码或代码列表
    *   - ``start_date`` / ``end_date``
        - 按 ``ex_date`` 过滤；省略则取全部历史
    *   - ``fields``
        - 只要某几列时用；省略返回全部
    *   - ``as_of``
        - 以该时点\ **已知**\ 的信息为准。公司行动也会被修订或撤销，回测里同样要传——
          含义见 :doc:`point_in_time`
    *   - ``market``
        - 省略则用服务端默认

和复权的关系
============

这些事件就是复权因子的成因。日常研究里你\ **不需要**\ 自己用它们去调整价格——直接用
:func:`~libfinance.get_price` 的 ``adjust_type`` 就行（见 :doc:`price`\ ）。

需要用到原始事件的场景通常是：

* 核对某天的价格跳空到底来自哪个事件；
* 研究分红、送转事件本身（事件研究法）；
* 自己实现一套特殊的复权口径。
