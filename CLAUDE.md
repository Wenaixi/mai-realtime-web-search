# CLAUDE.md - 麦麦联网插件 (search plugin) (xxxxx7258_google-search-plugin)

## 1. 模块定位与系统职责
- **插件标识符**：`xxxxx7258_google-search-plugin`
- **当前生效版本**：`v4.1.1`
- **托管仓库**：[`Wenaixi/google-search-plugin`](https://github.com/Wenaixi/google-search-plugin)
- **核心定位**：支持 Bing、搜狗、AnySearch 多引擎聚合网络搜索、缩写翻译与自动降级能力。

## 2. 关键工程规范与配置说明
- **配置路径**：`config.toml`（所有业务调优与鉴权参数收敛于此）；
- **数据持久化**：优先遵循 MaiBot SDK 标准持久化规范，不直接向源码目录写入易失数据；
- **编码与日志规范**：严格遵循 PEP 8 风格，文档与代码注释杜绝 emoji，避免虚假套话。

## 3. 本地深度定制与稳定性修复
配置 Bing + 搜狗免代理国内直连通道，注入主人专属 AnySearch 密钥 (as_sk_43fc...)，关闭无代理易超时的 DuckDuckGo。

---

## 上游项目与开源溯源
- **原作者 / 组织**：`xxxxx7258 (晴空)`
- **官方上游仓库**：[https://github.com/xxxxx7258/google_search_plugin](https://github.com/xxxxx7258/google_search_plugin)
- **开源许可证**：`GPL-3.0`
- **分支演进模式**：本仓库作为主人的深度定制与生产维护分支（`Wenaixi/google-search-plugin`）。在保持与官方上游架构演进对齐的同时，锁死并持续维护针对本服务器生产环境的稳定性补丁与核心特性。
