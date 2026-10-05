5 公司行动信息
========================================

.. currentmodule:: libfinance

四个公司行动函数使用同一组参数：证券、事件日期区间、字段与知识截止日。
市场由代码自动推断；混合市场列表按市场查询后合并。不支持的市场会明确报错。
``start_date/end_date`` 限制事件窗口，\ ``as_of`` 限制当时已知的信息。
分拆仅适用于美股。返回事件表，具体字段见 :doc:`fields`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_dividends`
      - 查询现金分红及送转分配事件
    * - :func:`~libfinance.get_splits`
      - 查询拆股与送转比例
    * - :func:`~libfinance.get_allotments`
      - 查询配股事件
    * - :func:`~libfinance.get_spinoffs`
      - 查询美股分拆事件及其估值依据
    * - :func:`~libfinance.get_ex_factor`
      - 查询单次及累计复权因子，核对复权依据与基准

get_dividends — 查询现金分红及送转分配事件
----------------------------------------------------------

.. autofunction:: get_dividends

**示例**

.. lf-examples:: get_dividends

结果解读：依次是全部历史、限定日期与字段、截至某日已知的事件、中美混合查询；\ ``order_book_id`` 区分证券，\ ``cash_per_share`` 是每股现金分红。

get_splits — 查询拆股与送转比例
--------------------------------------------

.. autofunction:: get_splits

**示例**

.. lf-examples:: get_splits

结果解读：\ ``ratio_from`` 股变为 ``ratio_to`` 股（10 股变 13 股即每 10 股转增 3 股）。A 股日常的送股与转增记在分红事件里（\ ``bonus_per_share``\ 、\ ``transfer_per_share``\ ）；A 股的拆股事件主要来自 2005–2006 年的股权分置改革。

get_allotments — 查询配股事件
----------------------------------------------

.. autofunction:: get_allotments

**示例**

.. lf-examples:: get_allotments

结果解读：缩小窗口后可能没有事件。空 DataFrame 与查询失败是不同情况。

get_spinoffs — 查询美股分拆事件及其估值依据
----------------------------------------------------------

.. autofunction:: get_spinoffs

**示例**

.. lf-examples:: get_spinoffs

结果解读：估值价格要和它的依据（\ ``valuation_basis``\ ）与来源（\ ``valuation_source``\ ）一起看；来源没有给出的字段为 ``None``\ 。

get_ex_factor — 查询单次及累计复权因子
------------------------------------------------------------

.. autofunction:: get_ex_factor

因子解释与计算图见 :doc:`../concepts/exfactor`\ 。同日多项行动已合成到同一除权日；
本接口读取当前数据版本，无需 market。累计因子在完整历史上计算后按日期筛选，
不随 start_date 重置；跨越未定价事件时会报错。

**结果字段**

.. list-table::
    :header-rows: 1
    :widths: 24 18 58

    * - 索引 / 列
      - 类型
      - 含义
    * - ``ex_date`` （索引）
      - DatetimeIndex
      - 除权日；同一日期可以包含不同证券的记录。
    * - ``order_book_id``
      - str
      - 完整证券标识符，用于区分混合市场与多证券结果。
    * - ``ex_factor``
      - float
      - 该除权日的单次因子；同日多项行动已合成。
    * - ``ex_cum_factor``
      - float
      - 从当前数据版本内该证券首个事件起，累乘至本行除权日的因子。

中美市场使用相同的累计规则：首个事件之前以 1 为基准，包含本日事件。
不同证券的历史覆盖不同，不能通过累计值大小比较收益。
计算某段时间的复权比例，应使用同一证券、同一数据版本下两个时点的累计因子比值。

**示例**

.. lf-examples:: get_ex_factor

结果解读：假设 2023-07-21 之前的累计因子为 5，本次因子为 1.04，
则当日累计值为 ``5 × 1.04 = 5.2``\ 。仅查询 2023 年 7 月仍返回 5.2，
不会变成 1.04；下一次事件后的累计值为 ``5.2 × 1.05 = 5.46``\ 。

