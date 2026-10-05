1 合约信息和交易日历
========================================

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.all_instruments`
      - 筛选某市场、某类型或历史时点的合约范围
    * - :func:`~libfinance.instruments`
      - 按一个或多个代码查询详细身份，支持跨市场列表
    * - :func:`~libfinance.get_trading_dates`
      - 查询日期区间内的交易日
    * - :func:`~libfinance.is_trading_date`
      - 判断某一天是否开市
    * - :func:`~libfinance.get_previous_trading_date`
      - 向前偏移 n 个交易日
    * - :func:`~libfinance.get_next_trading_date`
      - 向后偏移 n 个交易日
    * - :func:`~libfinance.get_n_trading_dates_until`
      - 取截至某日的最近 n 个交易日
    * - :func:`~libfinance.count_trading_dates`
      - 统计区间内的交易日数量
    * - :func:`~libfinance.get_all_trading_dates`
      - 取得当前日历包含的全部交易日
    * - :func:`~libfinance.get_calendar_coverage`
      - 确认日历有效区间，避免越界查询

.. toctree::
    :maxdepth: 2

    instrument
    calendar
    index_meta
