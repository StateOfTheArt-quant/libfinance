import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/index_component.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

import pandas as pd
from libfinance import get_index_weights


index_weight = get_index_weights(index_code="000300.XSHG", date="2022-09-20")
print(index_weight)

    
index_weight = get_index_weights(index_code="000300.XSHG", date="2022-07-20")
print(index_weight)
