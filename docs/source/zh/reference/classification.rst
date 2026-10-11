4 行业和概念信息
========================================

指数、行业、主题（概念）是三种给股票分组的方式，规则和用途各不相同，见 :doc:`../concepts/classification`\ 。
全部代码见 :doc:`index_meta`\ 、\ :doc:`industry_meta`\ 、\ :doc:`theme_meta`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_instrument_industry`
      - 查询证券在指定日期属于哪些行业
    * - :func:`~libfinance.get_industry_constituents`
      - 反向查询某行业在指定日期包含哪些证券
    * - :func:`~libfinance.get_industry_weights`
      - 查询某行业成分的权重（带 methodology）
    * - :func:`~libfinance.get_instrument_indices`
      - 查询证券在指定日期属于哪些指数
    * - :func:`~libfinance.get_index_constituents`
      - 查询指数在指定日期包含哪些证券
    * - :func:`~libfinance.get_index_weights`
      - 查询指数成分的权重（带 methodology）
    * - :func:`~libfinance.get_instrument_themes`
      - 查询证券在指定日期属于哪些主题
    * - :func:`~libfinance.get_theme_constituents`
      - 查询主题在指定日期包含哪些证券
    * - :func:`~libfinance.get_theme_weights`
      - 查询主题成分的权重（带 methodology）

.. toctree::
    :maxdepth: 2

    industry
    weights
    index_meta
    industry_meta
    theme_meta
