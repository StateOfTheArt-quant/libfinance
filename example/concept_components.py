#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libfinance import get_concept_meta, get_concept_weights

concept_meta = get_concept_meta(source="THS")
print(concept_meta)

# AI语料 "309126"
concept_weight = get_concept_weights(concept_ids=["309126"], source="THS")
print(concept_weight)

