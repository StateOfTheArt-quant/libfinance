====================
主题（概念）代码表
====================

同花顺（THS）主题，也就是 A 股常说的"概念板块"。表格由 ``docs/_shared/generate_catalogs.py`` 从服务生成，
反映的是\ **生成当天**\ 的目录：

..  code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="theme")                  # 目录
    >>> lf.get_theme_constituents("300008.THS")           # 一个主题的成分
    >>> lf.get_instrument_themes("600000.XSHG")           # 一只股票属于哪些主题

..  warning::

    主题的历史很短：服务里的主题数据从"生效日期"一列的日子开始，更早的 ``as_of`` 会报
    ``CoverageError``\ 。拿今天的主题名单去回测过去，名单本身就带着未来信息
    （很多主题是事后才设立、成分是事后才确认的）。见 :doc:`../concepts/classification`\ 。

列的含义
========

..  list-table::
    :header-rows: 1
    :widths: 18 30 52

    *   - 列
        - 对应字段
        - 含义
    *   - 代码
        - ``order_book_id``
        - 主题代码，写法 ``<编号>.THS``
    *   - 名称
        - ``name``
        - 主题名称
    *   - 成分数
        - ``len(get_theme_constituents(...))``
        - 最新一期的成分股数量。一只股票可以同时属于很多个主题
    *   - 生效日期
        - ``effective_from``
        - 当前这一版成分从哪天起生效，也是能查到的最早日期

全部主题
========

..  csv-table::
    :file: ../../../_shared/tables/catalog_theme_ths.csv
    :header: 代码, 名称, 成分数, 生效日期
    :widths: 20, 40, 15, 25
