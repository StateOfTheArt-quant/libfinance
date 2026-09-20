import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/shares.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

from libfinance import get_shares

# 单只股票全历史股本结构（省略日期 → 从首个事件到最后一个事件）
shares = get_shares(order_book_ids="600000.XSHG")
print(shares)

# 多只 + 指定日期范围 + 字段子集
shares = get_shares(
    order_book_ids=["000001.XSHE", "600000.XSHG"],
    start_date="2024-01-01",
    end_date="2024-06-30",
    fields=["total", "circulation_a"],
)
print(shares)
