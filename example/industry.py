#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行业分类：整张分类表，以及按行业取成分。"""
from libfinance import get_industry_mapping, get_industry

mapping = get_industry_mapping()
print("申万分类表：", mapping.shape)
print(mapping.head())

first = str(mapping.iloc[0]["first_industry_code"])
print("\n{} 的成分：".format(first))
print(get_industry(first)[:10])
