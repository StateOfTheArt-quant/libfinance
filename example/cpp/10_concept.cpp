// 概念板块：先发现有效 concept_id，再查询单个或多个概念的成分（Python：example/python/10_concept.py）。
//
// source "THS" 表示同花顺；as_of 是信息可见性截止日。
#include "show.hpp"

int main() {
  return run([] {
    // [get_concept_meta]
    // 查询概念目录，再只保留名称与 id，避免把显示名称当成查询 id。
    const lf::Table meta = lf::get_concept_meta("THS");
    show(meta);
    show(lf::get_concept_meta("THS", {"concept_id", "concept_name"}));
    // [/get_concept_meta]

    // [get_concept_weights]
    // 1. concept_ids 始终传列表；id 来自目录，不硬编码可能已失效的编号。
    std::vector<std::string> ids;
    const auto column = meta ? meta->GetColumnByName("concept_id") : nullptr;
    for (int64_t i = 0; column && i < column->length() && ids.size() < 2; ++i) {
      const auto scalar = column->GetScalar(i);
      if (scalar.ok() && (*scalar)->is_valid) ids.push_back((*scalar)->ToString());
    }
    if (!ids.empty()) {
      show(lf::get_concept_weights({ids.front()}, std::nullopt, "THS"));
      // 2. 多概念批量查询，按 concept_id 区分结果。
      show(lf::get_concept_weights(ids, std::nullopt, "THS"));
      // 3. 限制当时已知的信息；若该概念在截止日尚不存在，可能返回空表。
      show(lf::get_concept_weights(ids, "2024-06-28", "THS"));
    }
    // [/get_concept_weights]
  });
}
