import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/concept_components.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

from libfinance import get_concept_meta, get_concept_weights

concept_meta = get_concept_meta(source="THS")
print(concept_meta)

# 概念 id 取自上面那张元信息表。886074 曾经写在这里，但它不在表里 ——
# 服务端对未知 id 只返回空表，所以这个例子一直"能跑"却什么都没有。
concept_id = str(concept_meta["concept_id"].iloc[0])
print("取一个概念:", concept_id, concept_meta["concept_name"].iloc[0])
concept_weight = get_concept_weights(concept_ids=[concept_id], source="THS")
print(concept_weight)
