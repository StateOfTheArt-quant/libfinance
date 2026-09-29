4 行业和概念信息
========================================

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
    * - :func:`~libfinance.get_index_weights`
      - 查询指数在指定交易日的成分股及权重
    * - :func:`~libfinance.get_concept_meta`
      - 发现可查询的概念名称和编号
    * - :func:`~libfinance.get_concept_weights`
      - 查询一个或多个概念在指定知识时点的成分权重

.. toctree::
    :maxdepth: 2

    industry
    weights
