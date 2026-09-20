:orphan:

API 参考
========================================

按研究任务分为六类。展开分类查看函数名与用途，点击函数进入参数、返回值和场景示例。
示例日期需落在当前服务的数据覆盖范围内，数值与行数以实际查询结果为准。

.. dropdown:: 1 合约信息和交易日历
    :color: primary
    :icon: book

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

    :doc:`contracts`

.. dropdown:: 2 行情信息
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 函数 / 类
          - 解决的问题
        * - :func:`~libfinance.get_price`
          - 查询日频价格与成交量，选择字段和复权口径
        * - :func:`~libfinance.get_price_coverage`
          - 确认行情更新上界，构造最近交易日窗口

    :doc:`market_data`

.. dropdown:: 3 基本面信息
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 函数 / 类
          - 解决的问题
        * - :func:`~libfinance.get_pit_financials_ex`
          - 按季度查询财报，限制披露时点并查看修订版本
        * - :func:`~libfinance.get_factor`
          - 查询 TTM 等财务衍生因子
        * - :func:`~libfinance.get_shares`
          - 查询总股本、流通股本与自由流通股本的历史变化

    :doc:`fundamentals`

.. dropdown:: 4 行业和概念信息
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 函数 / 类
          - 解决的问题
        * - :func:`~libfinance.get_industry_mapping`
          - 发现行业代码、名称与分类层级
        * - :func:`~libfinance.get_instrument_industry`
          - 查询股票在指定日期属于哪个行业
        * - :func:`~libfinance.get_industry`
          - 反向查询某行业包含哪些股票
        * - :func:`~libfinance.get_index_weights`
          - 查询指数在指定交易日的成分股及权重
        * - :func:`~libfinance.get_concept_meta`
          - 发现可查询的概念名称和编号
        * - :func:`~libfinance.get_concept_weights`
          - 查询一个或多个概念在指定知识时点的成分权重

    :doc:`classification`

.. dropdown:: 5 公司行动信息
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 函数 / 类
          - 解决的问题
        * - :func:`~libfinance.get_dividends`
          - 查询现金分红及送转分配事件
        * - :func:`~libfinance.get_splits`
          - 查询拆股与送转比例
        * - :func:`~libfinance.get_allotments`
          - 查询配股事件
        * - :func:`~libfinance.get_spinoffs`
          - 查询美股分拆事件及其估值依据

    :doc:`corporate_actions`

.. dropdown:: 6 实时行情
    :color: primary
    :icon: book

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 函数 / 类
          - 解决的问题
        * - :func:`~libfinance.get_last_quotes`
          - 一次查询单只或多只证券的最新快照
        * - :class:`~libfinance.subscribe.quote_api.QuoteApi`
          - 连接、订阅与退订
        * - :class:`~libfinance.subscribe.quote_api.QuoteSpi`
          - 处理订阅回执与行情回调

    :doc:`realtime`

字段与使用支持
----------------------------------------

:doc:`fields` · :doc:`errors`
