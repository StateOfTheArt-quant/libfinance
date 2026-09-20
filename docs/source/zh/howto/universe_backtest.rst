====================
构造历史股票池
====================

**目标**\ ：构造"2024 年 3 月 8 日那天，沪深 300 里的银行股"这样一个股票池，并且不带
未来信息。

关键点只有一个：\ **每一步都要把日期传进去**\ 。不传日期就是用今天的成分、今天的行业
分类去划分历史——那是前视偏差。

完整例子
========

..  code-block:: python

    from libfinance import get_index_weights, get_instrument_industry, get_price

    AS_OF = "2024-03-08"

    # 1. 那一天的指数成分与权重
    w = get_index_weights(index_code="000300.XSHG", date=AS_OF)

    # 2. 那一天的行业归属（注意 date=AS_OF，不是今天）
    ind = get_instrument_industry(list(w["order_book_id"]), date=AS_OF)

    # 3. 取出银行股
    banks = ind[ind["first_industry_name"] == "银行"].index.tolist()

    # 4. 带上权重
    sub = w[w["order_book_id"].isin(banks)].sort_values("weight", ascending=False)

运行结果：

..  code-block:: text

    >>> len(w), w["weight"].sum()
    (300, 1.0)

    >>> ind["first_industry_name"].value_counts().head(5)
    电子      30
    电力设备    29
    非银金融    27
    医药生物    24
    银行      22

    >>> len(banks)
    22

    >>> sub.head(3)
     index_code       date order_book_id  weight
    000300.XSHG 2024-03-08   600036.XSHG 0.02225
    000300.XSHG 2024-03-08   601166.XSHG 0.01358
    000300.XSHG 2024-03-08   601398.XSHG 0.01048

然后取这批股票的行情：

..  code-block:: python

    px = get_price(banks, "2024-03-01", "2024-03-08")["close"].unstack("order_book_id")

三种股票池口径
==============

..  list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - 口径
        - 怎么取
        - 注意
    *   - 指数成分
        - :func:`~libfinance.get_index_weights`
        - 任意交易日都能问，不只调样日。权重已归一
    *   - 行业
        - :func:`~libfinance.get_industry`
        - 传 ``date``\ ；\ ``level`` 控制到第几级
    *   - 概念板块
        - :func:`~libfinance.get_concept_weights`
        - ``concept_id`` 要从 :func:`~libfinance.get_concept_meta` 查，
          写死的 id 可能已经失效

按行业直接取全市场成分（不限于指数内）：

..  code-block:: python

    >>> from libfinance import get_industry
    >>> get_industry("480000", date="2024-03-08")[:4]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE']

怎么确认没带未来信息
====================

..  list-table::
    :header-rows: 1
    :widths: 40 60

    *   - 检查
        - 预期
    *   - 权重表里的 ``date`` 列
        - 等于（或早于）你要的那一天
    *   - 成分数量
        - 符合该指数的规模（沪深 300 应为 300）
    *   - 权重加总
        - 约等于 1
    *   - 池子里有没有当时还没上市的票
        - 用 :func:`~libfinance.instruments` 带 ``date`` 核对 ``listed_date``

..  warning::

    **别把股票池写死在代码里。** 指数成分会调样、行业归属会变、概念板块会新增和废弃。
    每个回测日期都重新取一次，才是当时那个池子。

滚动构造
========

要逐月构造池子，就在每个调仓日重新取一次：

..  code-block:: python

    from libfinance import get_trading_dates, get_index_weights

    dates = get_trading_dates("2024-01-01", "2024-06-30")
    rebalance = [d for d in dates if d.day <= 5][:6]   # 每月初

    universe = {}
    for d in rebalance:
        day = d.strftime("%Y-%m-%d")
        universe[day] = get_index_weights(index_code="000300.XSHG", date=day)

财务数据的前视偏差是另一个话题，见 :doc:`pit_backtest`\ 。
