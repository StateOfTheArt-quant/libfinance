合约信息
========================================

.. currentmodule:: libfinance

先用 ``all_instruments`` 确定研究范围，再用 ``instruments`` 解析具体代码。
``order_book_id`` 是代码，\ ``name`` 是名称。目录里有四种类型——股票（stock）、指数（index）、行业（industry）、主题（theme），\ ``type`` 选类型，\ ``source`` 是编号机构：股票是交易所，指数是发布机构，行业是分类体系（申万 SW；GICS、ICB、NAICS、SIC），主题是主题目录（THS）。历史查询用 ``as_of`` 指定时点；股票、指数与申万行业有历史，美国行业分类与主题目前只有当前快照。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.all_instruments`
      - 按类型（股票、指数、行业、主题）、市场、编号机构或历史时点筛选证券
    * - :func:`~libfinance.instruments`
      - 按代码查询证券，一个列表可混合四种类型与中美市场

all_instruments — 按类型（股票、指数、行业、主题）、市场、编号机构或历史时点筛选证券
------------------------------------------------------------------------------------

.. autofunction:: all_instruments

**示例**

.. lf-examples:: all_instruments

结果解读：四种类型的返回形状相同，type、market、source 只改变范围；as_of 改变身份快照（申万 2021 年改版前 400 个行业节点，改版后 608 个）。

instruments — 按代码查询证券，一个列表可混合四种类型与中美市场
------------------------------------------------------------------------

.. autofunction:: instruments

**示例**

.. lf-examples:: instruments

结果解读：类型由代码决定，字符串输入得到单个对象，列表输入按输入顺序返回对象列表。历史查询展示当时的代码和身份；早于某类型发布的 as_of 报 CoverageError。

Instrument — 合约对象
----------------------------------------

.. autoclass:: libfinance.api.instrument.Instrument
    :members:
