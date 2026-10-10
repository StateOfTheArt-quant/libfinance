==========
libfinance
==========

..  rst-class:: lang-switch

\[ `English <https://libfinance.readthedocs.io/en/latest/>`_ | 中文 \]

量化研究的结论依赖历史数据，而历史数据有三类常见的失真：证券代码会更名、复用，不同市场之间还会重号；财务报表在披露后会被修订，回测若读取最新版本，就用上了当时无从获得的信息；分红、拆股等公司行动改变价格的可比性，复权口径不一致会直接扭曲收益。研究与生产又常常分别使用 Python 与 C++，两套接口的细微差别会让同一策略在迁移后得到不同的结果。

``libfinance`` 是面向量化研究与回测的金融数据客户端，覆盖 A 股与美股，提供 Python 与 C++ 两种实现。它以统一的证券标识、按时点（point-in-time）的数据版本和逐事件计算的复权因子组织行情、证券目录、交易日历、公司行动、股本、财务、行业 / 指数 / 主题成分与日频因子等数据；两个市场、两种语言遵循同一份接口契约，调用方式一致，差异只来自数据本身。

数据设计的四条约定：

* **统一的证券标识符**\ ：\ ``<trading_code>.<namespace>``\ ，如 ``600000.XSHG``\ 、\ ``000001.XSHE``\ 、\ ``AAPL.US``\ 。
  命名空间区分不同市场的同号代码，代码按历史时点解析，更名与代码复用不会串到别的证券。
* **point-in-time 机制 as_of**\ ：按历史时点还原证券池、选取当时已披露的财务版本，避免未来信息与幸存者偏差。
* **高质量的复权因子 exfactor**\ ：由公司行动逐事件计算，提供不复权、前复权、后复权三种口径；
  ``get_ex_factor`` 给出单次与累计因子，价格的每一次调整都可追溯。
* **Python 与 C++ 统一的函数设计**\ ：两种客户端按同一份契约实现，函数名、参数顺序与默认值、校验与报错、
  返回的列一一对应；同一组调用经两种客户端发给同一服务端逐项比对。

详见 :doc:`concepts/security_identifiers`\ 、\ :doc:`concepts/point_in_time`\ 、\ :doc:`concepts/exfactor` 与
:doc:`concepts/python_cpp`\ 。

.. code-block:: python

    from libfinance import get_price

    # 一次调用混查两个市场：代码自带市场
    bars = get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05", adjust_type="none")

这次调用返回什么、怎样读，见 :doc:`getting_started/quickstart`\ 。


A 股与美股共用一套术语
==========================

统一体现在三个层面。

..  list-table::
    :header-rows: 1
    :widths: 22 46 32

    *   - 层面
        - 统一的内容
        - 例
    *   - 证券标识
        - 写法都是 ``<trading_code>.<namespace>``\ ；命名空间的粒度取决于该市场消除歧义所需的范围
        - ``600000.XSHG``\ 、\ ``AAPL.US``
    *   - 函数与参数
        - 两个市场调用同一组函数，参数名相同，\ ``as_of`` 与 ``adjust_type`` 的含义一致
        - ``get_price``\ 、\ ``instruments``\ 、\ ``get_dividends``
    *   - 返回结构
        - 列名与索引一致；某个市场不适用或未提供的字段取 ``NaN``\ ，不另设一张表
        - 美股的 ``turnover``\ 、\ ``limit_up``\ 、\ ``limit_down``

需要显式指定市场的，只有不涉及具体证券的查询：交易日历、全市场目录、数据覆盖范围。
按证券查询时，命名空间已经给出了市场信息，列表里也可以混合两个市场的代码。

..  code-block:: python

    from libfinance import instruments, get_trading_dates

    instruments(["000001.XSHE", "AAPL.US"])            # 命名空间已给出市场
    get_trading_dates("2024-01-01", "2024-01-31", market="us")   # 不涉及具体证券

统一的是术语和调用约定，数据本身的差异依然存在：配股只有 A 股，分拆只有美股，主题目录（THS）只有
A 股；美股没有涨跌停，也没有提供成交额。
逐个接口的情况见 :doc:`howto/us_market`\ 。


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
    *   - 复权因子
        - CN · US
        - :func:`~libfinance.get_ex_factor`
        - 逐除权日的单次及累计因子
    *   - 股本结构
        - CN · US
        - :func:`~libfinance.get_shares`
        - 逐交易日的总股本与流通股本
    *   - 分红 / 拆股 / 配股
        - CN · US
        - :func:`~libfinance.get_dividends`
        - 除权事件，价格跳空的来源；配股只有 A 股
    *   - 分拆
        - US
        - :func:`~libfinance.get_spinoffs`
        - A 股不产生这类事件
    *   - 财务报表（PIT）
        - CN · US
        - :func:`~libfinance.get_pit_financials_ex`
        - 按季度取，带修订历史
    *   - 财务衍生指标
        - CN · US
        - :func:`~libfinance.get_financial_metrics`
        - 按交易日的财务衍生指标
    *   - 行业分类
        - CN · US
        - :func:`~libfinance.get_instrument_industry`
        - 申万、GICS 等分类体系；成员与权重见 :func:`~libfinance.get_industry_constituents`
    *   - 指数成分与权重
        - CN · US
        - :func:`~libfinance.get_index_constituents`
        - 中证、标普等；权重见 :func:`~libfinance.get_index_weights`
    *   - 主题成分与权重
        - CN
        - :func:`~libfinance.get_theme_constituents`
        - THS 主题；权重见 :func:`~libfinance.get_theme_weights`
    *   - 日频因子
        - CN
        - :func:`~libfinance.get_factor_exposure`
        - alpha158、qlib，Barra CNE5 风格 / 行业因子，CNE5 与 CNE6 描述符；见 :doc:`data/factors` 与 :doc:`reference/factor_dictionary`
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
        :link: concepts/point_in_time
        :link-type: doc

        先读 :doc:`concepts/point_in_time` 与 :doc:`concepts/exfactor`\ 。
        这两章决定了你的回测会不会用到当时还看不到的数字。

    ..  grid-item-card:: 我要实时行情
        :link: data/realtime
        :link-type: doc

        实时快照与订阅推送是两条不同的路径，
        :doc:`howto/subscribe` 给出可直接运行的订阅程序。

如果你已经在用了，遇到问题直接查 :doc:`howto/troubleshooting`——它按\ **症状**\ 编排：
你看到什么现象，就从哪一行开始。


两件事值得先知道
================

它们不是高级话题，是\ **默认行为**\ 。不知道的话，代码能跑，数字是错的。

..  dropdown:: 不传 ``adjust_type``\ ，你拿到的是前复权价
    :color: warning
    :icon: alert

    同一只股票、同一天，前复权收盘价 8.81，未复权 10.49——差 16%。通过 ``adjust_type`` 显式选择价格口径。见 :doc:`data/price`\ 。

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

.. toctree::
    :maxdepth: 1
    :caption: 概念设计
    :titlesonly:
    :hidden:

    concepts/security_identifiers
    concepts/point_in_time
    concepts/exfactor
    concepts/python_cpp

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
    7 因子 <reference/factors>

.. toctree::
    :maxdepth: 1
    :caption: 字段与使用支持
    :hidden:

    reference/fields
    reference/factor_dictionary
    reference/errors

..  toctree::
    :maxdepth: 1
    :caption: 关于
    :hidden:

    about/changelog
    about/contributing
    about/citing
