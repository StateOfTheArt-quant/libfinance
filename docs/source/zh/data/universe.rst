====================
股票池：三种口径
====================

"选出一批股票"有三种常见口径，它们的来源和更新节奏都不一样：

..  list-table::
    :header-rows: 1
    :widths: 20 30 50

    *   - 口径
        - 函数
        - 特点
    *   - 指数成分
        - :func:`~libfinance.get_index_weights`
        - 有权重，规则透明，定期调样
    *   - 行业分类
        - :func:`~libfinance.get_industry_constituents` / :func:`~libfinance.get_instrument_industry`
        - 全市场覆盖，多级层次，多种分类体系
    *   - 概念板块
        - :func:`~libfinance.get_theme_constituents`, :func:`~libfinance.get_theme_weights`
        - 主题驱动，数量多，边界模糊

指数成分与权重
==============

..  code-block:: python

    >>> from libfinance import get_index_weights
    >>> w = get_index_weights("000300.XSHG", as_of="2024-02-29")
    >>> w[["order_book_id", "weight", "source", "basis", "date"]].head()
      order_book_id   weight source   basis       date
    0   000001.XSHE  0.00576    CSI  origin 2024-02-29
    1   000002.XSHE  0.00383    CSI  origin 2024-02-29
    2   000063.XSHE  0.00534    CSI  origin 2024-02-29
    3   000069.XSHE  0.00085    CSI  origin 2024-02-29
    4   000100.XSHE  0.00477    CSI  origin 2024-02-29

权重已经归一化：

..  code-block:: python

    >>> w["weight"].sum()
    1.0

..  note::

    **任意交易日都能问，不只是调样日。**

    指数公司只在调样日公布权重。非调样日的权重是这样得到的：取该日期之前最近一期的
    公布快照，按每只成分股从那天到目标日的\ **复权**\ 收益率重新加权，再归一化。

    用复权收益率是必需的——区间内如果有送转或拆股，用原始价的涨跌幅会把股本变动
    误读成收益。

省略 ``as_of`` 则返回最新一期。指数用它的 ``order_book_id`` 指定（\ ``000300.XSHG``\ 、\ ``SPX.US``\ ）。
每行说明权重的来历：\ ``basis`` 为 ``origin``\ （数据源发布）或 ``reconstructed``\ （按编制方法重构），
``date`` 是该权重所属的快照日（漂移得到的为 ``as_of``\ ，\ ``quality_flags`` 带 ``DRIFTED``\ ）。

返回值不含指数名称和成分股名称——名称属于证券主数据，要的话用
:func:`~libfinance.instruments` 另取。

行业分类
========

行业以 ``order_book_id``\ （\ ``<分类代码>.<分类体系>``\ ）命名：申万银行是 ``480000.SW``\ ，GICS 能源是 ``10.GICS``\ 。
``source`` 是分类体系（\ ``SW``\ 、``GICS``\ ……），``level`` 是层级。

查某只股票属于哪些行业：

..  code-block:: python

    >>> from libfinance import get_instrument_industry
    >>> get_instrument_industry(["000001.XSHE", "600000.XSHG"], source="SW", level=1, as_of="2024-03-08")
      order_book_id related_order_book_id source market  level
    0   000001.XSHE             480000.SW     SW     CN      1
    1   600000.XSHG             480000.SW     SW     CN      1

省略 ``source`` / ``level`` 则返回全部分类体系、全部层级。``related_order_book_id`` 就是行业代码。

反过来，查某个行业下有哪些股票，以及它们的权重：

..  code-block:: python

    >>> from libfinance import get_industry_constituents, get_industry_weights
    >>> get_industry_constituents("480000.SW", as_of="2024-03-08")[:6]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE',
     '002839.XSHE', '002936.XSHE']
    >>> get_industry_weights("480000.SW", as_of="2024-03-08")   # 每行带 methodology

..  important::

    行业归属会变。做历史回测时要传 ``as_of``\ ，否则用的是\ **今天**\ 的分类去划分历史上的
    股票——这同样是一种前视偏差。

概念板块
========

目前只有 ``source="THS"`` 一个来源。先查有哪些概念：

..  code-block:: python

    >>> from libfinance import get_concept_meta
    >>> get_concept_meta(source="THS").head(3)
      source concept_id concept_name established_date  component_number
    0    THS     300008        新能源汽车              NaN               NaN
    1    THS     300013          大飞机              NaN               NaN
    2    THS     300018         参股保险              NaN               NaN

再按 ``concept_id`` 取成分：

..  code-block:: python

    >>> from libfinance import get_concept_weights
    >>> get_concept_weights(concept_ids=["300008"], source="THS").head(3)
      source concept_id       date order_book_id    weight
    0    THS     300008 2026-09-15   000009.XSHE  0.000943
    1    THS     300008 2026-09-15   000021.XSHE  0.000943
    2    THS     300008 2026-09-15   000062.XSHE  0.000943

..  warning::

    **概念 id 必须来自 :func:`~libfinance.get_concept_meta`\ 。** 传一个不存在的 id
    会返回空表——从调用方看，"这个概念今天没有成分"和"这个 id 根本不存在"长得一模
    一样。客户端为此会给一句警告：

    ..  code-block:: python

        >>> get_concept_weights(concept_ids=["886074"], source="THS")
        UserWarning: 未知的 concept_id: 886074（source='THS'）。用 get_concept_meta()
                     查可用的概念。
        Empty DataFrame

    别把概念 id 写死在代码里，从元信息表里查出来。

``as_of`` 同样适用：以该时点\ **已知**\ 的成分为准。构造历史股票池时要传，理由见
:doc:`point_in_time`\ 。
