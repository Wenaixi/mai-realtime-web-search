# 麦麦全网实时联网综合搜索 (wenaixi_mai_realtime_web_search)

[![Release](https://img.shields.io/github/v/release/Wenaixi/mai-realtime-web-search?style=flat-square&color=blue&label=release)](https://github.com/Wenaixi/mai-realtime-web-search/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/Wenaixi/mai-realtime-web-search/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Wenaixi/mai-realtime-web-search/actions)
[![License](https://img.shields.io/badge/license-AGPL-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue?style=flat-square)](https://www.python.org/)
[![MaiBot](https://img.shields.io/badge/MaiBot-1.2%2B-orange?style=flat-square)](https://docs.mai-mai.org)

> 本插件由 [Wenaixi](https://github.com/Wenaixi) 维护，是专为生产环境深度调优的高可用多引擎聚合搜索分支。

## 简介与定位

支持 13 大搜索引擎多维聚合检索（涵盖国内免代理、官方 API、海外隐私引擎、维基百科与 SearXNG 元搜索实例），具备自动降级容灾与单引擎独立代理调度能力。

- **插件目录**：`wenaixi_mai_realtime_web_search`
- **插件标识符**：`wenaixi.mai_realtime_web_search`
- **开源许可证**：`GPL-3.0`

---

## 聚合引擎生态矩阵 (13 大引擎)

| 类别 | 包含搜索引擎 | 特性说明 |
| :--- | :--- | :--- |
| **国内免代理** | **Bing (默认)**、**百度 (Baidu)**、**搜狗 (Sogou)** | 国内外免代理直连秒级响应，中文生活与长尾资讯覆盖全面 |
| **官方直连 API** | **AnySearch**、**DeepSeek 联网搜索** | 结构化搜索，自带摘要与格式清洗 |
| **权威知识库** | **维基百科 (Wikipedia)** | MediaWiki 官方 API，权威百科条目结构化提取，纯净无噪 |
| **元搜索实例** | **SearXNG** | 直连自建或公开 SearXNG 实例，一键聚合 70+ 引擎生态 |
| **独立与隐私** | **Brave Search**、**DuckDuckGo** | 独立网页索引，无用户追踪保护隐私 |
| **专业 AI 检索** | **Tavily**、**Exa**、**You.com** | 面向 LLM 设计的高质量研究型与语义检索接口 |

---

## 单引擎独立代理配置指南

在 `config.toml` 中，每个搜索引擎均包含独立的 `[engine]_proxy` 配置项：

- **默认行为**：所有引擎的 `[engine]_proxy` 默认留空 `""`，不走代理直连网络，零多余开销；
- **单独配置代理**：若某个海外引擎（如 Google、DuckDuckGo、Brave、维基百科等）需要代理，只需在该引擎下直接填写代理地址即可（例如：`google_proxy = "http://10.150.1.139:7890"`）；
- **强制免代理直连**：若全局配置了 `search_backend.proxy`，但想让特定引擎走直连，可填写 `"direct"` 或 `"none"`。

---

## 指令与工具速查

### 常用指令 (Command)
- `/google_search_status - 查询联网引擎可用状态`

### 大模型工具 (Tool)
- `@Tool("web_search") - 全网实时搜索与正文提取`
- `@Tool("abbreviation_translate") - 缩写翻译 (神奇海螺)`

---

## 上游项目与开源溯源

- **原作者 / 组织**：`xxxxx7258 (晴空)`
- **官方原版开源仓库**：[https://github.com/xxxxx7258/google_search_plugin](https://github.com/xxxxx7258/google_search_plugin)
- **开源协议**：`GPL-3.0`
- **声明**：本项目遵循开源协议，特此致敬原作者的杰出贡献。本分支针对生产环境的高并发网络、个性化社交和抗风控需求进行了深度稳定性修复与定制化演进。