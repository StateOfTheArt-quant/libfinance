==========
指数代码表
==========

全部指数的代码、名称与编制基础信息。表格由 ``docs/_shared/generate_catalogs.py`` 从服务生成，反映的是\ **生成当天**\ 的目录；
你连的服务可能更新，以查询结果为准：

..  code-block:: python

    >>> import libfinance as lf
    >>> lf.all_instruments(type="index")              # 目录：代码、名称、市场、发布机构
    >>> lf.instruments("000300.XSHG")                 # 单个指数的基日、基点、发布日期
    >>> lf.all_instruments(type="index", as_of="2016-01-04")   # 那一天的目录

指数是什么、怎么用，见 :doc:`../concepts/classification`\ 。

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
        - 指数代码，可直接传给 :func:`~libfinance.get_price`\ 、\ :func:`~libfinance.get_index_constituents`
    *   - 发布机构
        - ``source``
        - 编制并发布指数的机构：\ ``CSI`` 中证指数、\ ``CNI`` 国证指数、\ ``SZSE`` 深交所、
          ``SPDJI`` 标普道琼斯、\ ``NASDAQ`` 纳斯达克、\ ``FTSE_RUSSELL`` 富时罗素；空白表示目录未登记发布机构
    *   - 基日 / 基点
        - ``base_date`` / ``base_value``
        - 指数从哪一天、从多少点开始计算。点位只在同一个指数内部可比，不同指数的点位高低没有意义
    *   - 发布日期
        - ``established_date``
        - 指数正式发布的日子。\ **发布日之前的点位是回算的**\ ，编制者当时并不知道这个指数会存在
    *   - 成分数
        - ``len(get_index_constituents(...))``
        - 最新一期的成分证券数量；空白表示服务没有这个指数的成分数据，只能取点位行情

有成分数据的指数
================

只有这些指数能拿来做\ **基准**\ 或\ **历史股票池**\ （成分与权重都按 ``as_of`` 回答那一天的事实）。

..  csv-table::
    :file: ../../../_shared/tables/catalog_index_constituents.csv
    :header: 代码, 名称, 市场, 发布机构, 基日, 基点, 发布日期, 成分数
    :widths: 14, 22, 6, 12, 12, 8, 12, 8

全部指数
========

..  dropdown:: 展开全部指数（约 1000 个）
    :icon: list-unordered

    ..  csv-table::
        :file: ../../../_shared/tables/catalog_index.csv
        :header: 代码, 名称, 市场, 发布机构, 基日, 基点, 发布日期, 成分数
        :widths: 14, 22, 6, 12, 12, 8, 12, 8
