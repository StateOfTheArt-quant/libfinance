==========
libfinance
==========

..  rst-class:: lang-switch

\[ `English <https://libfinance.readthedocs.io/en/latest/>`_ | 中文 \]

``libfinance`` 给量化研究者提供 A 股与美股的历史数据：行情、证券主数据、交易日历、
公司行动、财务、股本、行业分类、指数与概念成分，以及实时行情订阅。

这份文档帮助\ **会用 pandas 做研究的人\ **\ ，取到口径明确的数据，并且能判断**拿到的数字
是哪一天、哪一种口径下的值**——后面这件事决定了你的回测结果是否可信。

.. code-block:: python

    from libfinance import get_price

    df = get_price(["000001.XSHE", "600000.XSHG"], "2024-03-01", "2024-03-06")

一分钟看懂这行代码取到了什么，见 :doc:`getting_started/quickstart`\ 。


这里有什么数据
==============

..  list-table::
    :header-rows: 1
    :widths: 22 12 30 36

    *   - 数据
        - 市场
        - 主要函数
        - 说明
    *   - 交易日历
        - CN · US
        - :func:`~libfinance.get_trading_dates`
        - 交易日、区间取日、前后推 N 个交易日
    *   - 证券主数据
        - CN · US
        - :func:`~libfinance.all_instruments`
        - 代码、名称、类型、上市与退市日期
    *   - 日频行情
        - CN · US
        - :func:`~libfinance.get_price`
        - 开高低收、成交量额，可复权
    *   - 股本结构
        - CN
        - :func:`~libfinance.get_shares`
        - 逐交易日的总股本与流通股本
    *   - 分红 / 拆股 / 配股
        - CN · US
        - :func:`~libfinance.get_dividends`
        - 除权事件，价格跳空的来源
    *   - 分拆
        - US
        - :func:`~libfinance.get_spinoffs`
        - A 股不产生这类事件
    *   - 财务报表（PIT）
        - CN
        - :func:`~libfinance.get_pit_financials_ex`
        - 按季度取，带修订历史
    *   - 财务因子
        - CN
        - :func:`~libfinance.get_factor`
        - 季度财务衍生因子
    *   - 行业分类
        - CN
        - :func:`~libfinance.get_industry_mapping`
        - 申万三级分类
    *   - 指数成分与权重
        - CN
        - :func:`~libfinance.get_index_weights`
        - 任意交易日的成分权重
    *   - 概念板块成分
        - CN
        - :func:`~libfinance.get_concept_weights`
        - 同花顺概念分类
    *   - 实时行情
        - CN
        - :class:`~libfinance.subscribe.quote_api.QuoteApi`
        - 订阅推送

覆盖到哪一年、更新到哪一天，取决于你连的那个服务。\ **不要照抄文档里的日期**\ ，用
:doc:`data/freshness` 里的两个函数自己查。


从哪里开始读
============

..  grid:: 1 1 3 3
    :gutter: 3

    ..  grid-item-card:: 我只想取一段行情
        :link: getting_started/quickstart
        :link-type: doc

        安装 → 连接 → 第一次查询。
        然后看 :doc:`howto/price_panel`\ ，它把"取最近 N 个交易日"这件事里所有会踩的
        坑走了一遍。

    ..  grid-item-card:: 我要做回测
        :link: data/point_in_time
        :link-type: doc

        先读 :doc:`data/point_in_time` 与 :doc:`data/price`\ 。
        这两章决定了你的回测会不会用到当时还看不到的数字。

    ..  grid-item-card:: 我要实时行情
        :link: data/realtime
        :link-type: doc

        实时快照与订阅推送是两条不同的路径，
        :doc:`howto/subscribe` 给出可直接运行的订阅程序。

如果你已经在用了，遇到问题直接查 :doc:`howto/troubleshooting`——它按\ **症状**\ 编排：
你看到什么现象，就从哪一行开始。


三件事值得先知道
================

它们不是高级话题，是\ **默认行为**\ 。不知道的话，代码能跑，数字是错的。

..  dropdown:: 不传 ``adjust_type``\ ，你拿到的是前复权价
    :color: warning
    :icon: alert

    同一只股票、同一天，前复权收盘价 8.81，未复权 10.49——差 16%。这个默认值在 0.0.2
    改过，改之前是不复权。见 :doc:`data/price`\ 。

..  dropdown:: ``end_date`` 不能写今天
    :color: warning
    :icon: alert

    交易日历是提前发布的（能到年底），行情只到\ **最后一个已收盘交易日**\ 。拿今天当
    ``end_date`` 会被明确拒绝，而不是返回一张短一点的表。见 :doc:`data/freshness`\ 。

..  dropdown:: 财报会被追溯修订
    :color: warning
    :icon: alert

    同一个 2024 年二季度的净利润，这个库里存着 5 个版本，最新一版发布于 2026 年。
    回测里不传 ``as_of``\ ，你用的就是未来才存在的数字。见 :doc:`data/point_in_time`\ 。


..  toctree::
    :maxdepth: 2
    :caption: 开始使用
    :hidden:

    getting_started/installation
    getting_started/quickstart

..  toctree::
    :maxdepth: 2
    :caption: 数据说明
    :hidden:

    data/index

..  toctree::
    :maxdepth: 2
    :caption: 使用指南
    :hidden:

    howto/index

..  toctree::
    :maxdepth: 2
    :caption: API 参考
    :hidden:

    reference/contracts
    reference/market_data
    reference/fundamentals
    reference/classification
    5 公司行动信息 <reference/corporate_actions>
    6 实时行情 <reference/realtime>

.. toctree::
    :maxdepth: 1
    :caption: 字段与使用支持
    :hidden:

    reference/fields
    reference/errors

..  toctree::
    :maxdepth: 1
    :caption: 关于
    :hidden:

    about/changelog
    about/contributing
    about/citing
