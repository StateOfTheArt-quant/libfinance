#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""概念板块：先发现有效 concept_id，再查询单个或多个概念的成分。

source='THS' 表示同花顺。as_of 是信息可见性截止日；旧参数名 date 已弃用。
"""
from libfinance import get_concept_meta, get_concept_weights

# [get_concept_meta]
# [get_concept_meta.1]
# 查询概念目录，再只保留名称与 id，避免把显示名称当成查询 id。
meta = get_concept_meta(source="THS")
print(meta.head())
# [/get_concept_meta.1]

# [get_concept_meta.2]
print(get_concept_meta(source="THS", fields=["concept_id", "concept_name"]).head())
# [/get_concept_meta.2]
# [/get_concept_meta]

# [get_concept_weights]
# [get_concept_weights.1]
# 1. concept_ids 始终传列表；id 来自目录，不硬编码可能已失效的编号。
meta = get_concept_meta(source="THS")
ids = meta["concept_id"].astype(str).head(2).tolist()
if ids:
    print(get_concept_weights(ids[:1], source="THS"))
    # 2. 多概念批量查询，按 concept_id 区分结果。
    print(get_concept_weights(ids, source="THS"))
    # 3. 限制当时已知的信息；若该概念在截止日尚不存在，可能返回空表。
    print(get_concept_weights(ids, source="THS", as_of="2024-06-28"))
# [/get_concept_weights.1]
# [/get_concept_weights]
