========
数据说明
========

这一部分讲\ **口径**\ ：每一类数据是什么、边界在哪里、哪些默认行为会改变你算出来的数字。

不了解这些，代码照样能跑——错的是结果，而且不会有任何报错提示你。所以即使你只想快点
取到数，也建议先扫一遍 :doc:`price` 和 :doc:`freshness` 这两章的结论框。

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 章节
        - 它帮你避免的错误
    *   - :doc:`instruments`
        - 代码写对了但查不到；已退市的股票"消失"了
    *   - :doc:`calendar`
        - 把非交易日当成交易日；区间静默变短
    *   - :doc:`price`
        - 用了前复权价却以为是真实成交价；成交量对不上
    *   - :doc:`freshness`
        - 把今天当 ``end_date``\ ，整个查询被拒
    *   - :doc:`point_in_time`
        - 回测用到了当时还没披露的财务数字
    *   - :doc:`corporate_actions`
        - 看到价格跳空，以为是数据错了
    *   - :doc:`fundamentals`
        - 季度口径与单位理解错
    *   - :doc:`universe`
        - 股票池带了未来信息，或权重不归一
    *   - :doc:`realtime`
        - 断线重连后订阅悄悄丢失

..  toctree::
    :maxdepth: 1

    instruments
    calendar
    price
    freshness
    point_in_time
    corporate_actions
    fundamentals
    universe
    realtime
