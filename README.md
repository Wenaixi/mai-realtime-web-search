# 麦麦联网插件 (search plugin)

> 本插件由 [Wenaixi](https://github.com/Wenaixi) 维护，是专为生产环境深度调优的高可用分支。

## 简介与定位

支持 Bing、搜狗、AnySearch 多引擎聚合网络搜索、缩写翻译与自动降级能力。

- **插件目录**：`wenaixi_mai_realtime_web_search`
- **生效版本**：`v4.1.1`
- **开源许可证**：`GPL-3.0`

---

## 核心特性与本地深度调优

- 配置 Bing + 搜狗免代理国内直连通道
- 注入主人专属 AnySearch 密钥 (as_sk_43fc...)，开启 AnySearch 引擎
- 关闭无代理易超时的 DuckDuckGo，搜索稳定秒出

---

## 指令与工具速查

### 常用指令 (Command)
- `/google_search_status - 查询联网引擎可用状态`

### 大模型工具 (Tool)
- `@Tool("web_search") - 全网实时搜索`
- `@Tool("abbreviation_translate") - 缩写翻译`

---

## 快速配置

配置文件统一定位于插件根目录下的 `config.toml`。修改后重启或通过 WebUI 热重载即可生效。

---

## 上游项目与开源溯源

- **原作者 / 组织**：`xxxxx7258 (晴空)`
- **官方原版开源仓库**：[https://github.com/xxxxx7258/google_search_plugin](https://github.com/xxxxx7258/google_search_plugin)
- **开源协议**：`GPL-3.0`
- **声明**：本项目遵循开源协议，特此致敬原作者的杰出贡献。本分支针对生产环境的高并发网络、个性化社交和抗风控需求进行了深度稳定性修复与定制化演进。
