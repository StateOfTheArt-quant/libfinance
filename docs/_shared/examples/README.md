# 示例快照

参考页每个示例的代码与它**实际的输出**（Python 与 C++ 各一份），由 `../update_examples.py` 运行
`docs/examples/python/` 与 `docs/examples/cpp/` 的脚本（参考页专用，不是仓库根目录的 `example/`）生成；页面上的 `.. lf-examples:: <函数>` 从这里读取。

- `python.json` / `cpp.json`：`<函数>.<序号>` → 标题、代码、输出、服务地址、数据版本、生成日期。
- `titles_en.json`：英文站的示例标题（中文标题取自脚本的标记行）。

不要手改快照：改脚本，然后在仓库根目录运行

    python docs/_shared/update_examples.py --host <服务地址> --port <端口> [--cpp-docker <带 Arrow C++ 的镜像>]

运行失败的示例保留上一次成功的代码与输出，脚本会列出它们；脚本里删掉的示例会从快照里移除。
