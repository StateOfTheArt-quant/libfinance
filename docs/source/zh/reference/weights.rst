指数与主题成分
========================================

.. currentmodule:: libfinance

指数（\ ``000300.XSHG``\ 、``SPX.US``\ ）与主题（\ ``300900.THS``\ ）以 ``order_book_id`` 命名，规则与证券相同；
目录分别是 ``all_instruments(type="index")`` 与 ``all_instruments(type="theme")``\ 。每个函数都按 ``as_of``
回答"那一天的事实"。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
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

指数
----

.. autofunction:: get_instrument_indices

.. autofunction:: get_index_constituents

.. autofunction:: get_index_weights

:download:`下载完整示例 <../../../../example/python/09_index.py>`

主题
----

.. autofunction:: get_instrument_themes

.. autofunction:: get_theme_constituents

.. autofunction:: get_theme_weights

:download:`下载完整示例 <../../../../example/python/10_theme.py>`
