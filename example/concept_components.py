from libfinance import get_concept_meta, get_concept_weights

concept_meta = get_concept_meta(source="THS")
print(concept_meta)

# 概念 id 取自上面那张元信息表。886074 曾经写在这里，但它不在表里 ——
# 服务端对未知 id 只返回空表，所以这个例子一直"能跑"却什么都没有。
concept_id = str(concept_meta["concept_id"].iloc[0])
print("取一个概念:", concept_id, concept_meta["concept_name"].iloc[0])
concept_weight = get_concept_weights(concept_ids=[concept_id], source="THS")
print(concept_weight)
