#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行业分类：整张分类表，以及按行业取成分。"""
import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/industry.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

from libfinance import get_industry_mapping, get_industry

mapping = get_industry_mapping()
print("申万分类表：", mapping.shape)
print(mapping.head())

first = str(mapping.iloc[0]["first_industry_code"])
print("\n{} 的成分：".format(first))
print(get_industry(first)[:10])
