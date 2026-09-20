#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/instrument.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

from libfinance import instruments, all_instruments


stock_instrument_df = all_instruments(type="CS")
print(len(stock_instrument_df))
print(stock_instrument_df)

instrument_list = instruments(order_book_ids=["000001.XSHE","000300.XSHG"])
print(instrument_list)