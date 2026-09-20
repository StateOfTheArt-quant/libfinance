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
        - :func:`~libfinance.get_industry` / :func:`~libfinance.get_industry_mapping`
        - 全市场覆盖，三级层次
    *   - 概念板块
        - :func:`~libfinance.get_concept_weights`
        - 主题驱动，数量多，边界模糊

指数成分与权重
==============

..  code-block:: python

    >>> from libfinance import get_index_weights
    >>> get_index_weights(index_code="000300.XSHG", date="2024-03-08").head()
        index_code       date order_book_id   weight
    0  000300.XSHG 2024-03-08   000001.XSHE  0.00576
    1  000300.XSHG 2024-03-08   000002.XSHE  0.00383
    2  000300.XSHG 2024-03-08   000063.XSHE  0.00534
    3  000300.XSHG 2024-03-08   000069.XSHE  0.00085
    4  000300.XSHG 2024-03-08   000100.XSHE  0.00477

权重已经归一化：

..  code-block:: python

    >>> get_index_weights(index_code="000300.XSHG", date="2024-03-08")["weight"].sum()
    0.9999999996000001

..  note::

    **任意交易日都能问，不只是调样日。**

    指数公司只在调样日公布权重。非调样日的权重是这样得到的：取该日期之前最近一期的
    公布快照，按每只成分股从那天到目标日的\ **复权**\ 收益率重新加权，再归一化。

    用复权收益率是必需的——区间内如果有送转或拆股，用原始价的涨跌幅会把股本变动
    误读成收益。

省略 ``date`` 则返回最新一期。参数名是 ``index_code``\ （不是 ``index_id``\ ）。

返回值只有四列，不含指数名称和成分股名称——名称属于证券主数据，要的话用
:func:`~libfinance.instruments` 另取。

行业分类
========

目前只有\ **申万**\ 分类（\ ``source="sw"``\ ），三级结构：

..  code-block:: python

    >>> from libfinance import get_industry_mapping
    >>> get_industry_mapping().shape
    (346, 6)
    >>> get_industry_mapping().head(3)
      first_industry_code first_industry_name second_industry_code second_industry_name  \
    0              110000                农林牧渔               110100                  种植业
    1              110000                农林牧渔               110100                  种植业
    2              110000                农林牧渔               110100                  种植业

      third_industry_code third_industry_name
    0              110101                  种子
    1              110102                粮食种植
    2              110103               其他种植业

这是一张\ **分类表**\ （行业之间的层次关系），每行是一个三级行业。

反查某只股票属于哪个行业：

..  code-block:: python

    >>> from libfinance import get_instrument_industry
    >>> get_instrument_industry(["000001.XSHE", "600000.XSHG"], date="2024-03-08")
                  first_industry_code first_industry_name
    order_book_id
    000001.XSHE                480000                  银行
    600000.XSHG                480000                  银行

``level`` 控制返回到第几级（1/2/3，默认 1）。

正查某个行业下有哪些股票：

..  code-block:: python

    >>> from libfinance import get_industry
    >>> get_industry("480000")[:6]
    ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE',
     '002839.XSHE', '002936.XSHE']

..  important::

    行业归属会变。做历史回测时要传 ``date``\ ，否则用的是\ **今天**\ 的分类去划分历史上的
    股票——这同样是一种前视偏差。

概念板块
========

目前只有同花顺（\ ``source="THS"``\ ）一个来源。先查有哪些概念：

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
