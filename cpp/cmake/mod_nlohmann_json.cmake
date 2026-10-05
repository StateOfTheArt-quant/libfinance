include_guard(GLOBAL)

# nlohmann/json：能力清单、lock、调用参数都是 JSON。
# 用 ordered_json 保持键的声明顺序，lock 才能与 schema v4 的字段顺序逐字一致。
macro(load_nlohmann_json root_dir release_version)
    set(JSON_Install         ON  CACHE BOOL "" FORCE)
    set(JSON_BuildTests      OFF CACHE BOOL "" FORCE)
    set(JSON_MultipleHeaders OFF CACHE BOOL "" FORCE)

    load_or_download_library(
        nlohmann_json
        nlohmann_json::nlohmann_json
        ${root_dir}
        ${release_version}
        https://github.com/nlohmann/json.git
    )
endmacro()
