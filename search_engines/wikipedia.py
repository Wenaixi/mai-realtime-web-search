"""维基百科知识条目搜索引擎实现。

- 采用 MediaWiki Action API (action=query&list=search)；
- 支持多语言站点切换（默认 zh 中文维基百科）；
- 提取条目标题、URL 与清洗后的正文文本摘要；
- 支持独立代理配置与无代理直连。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import aiohttp

from .base import BaseSearchEngine, SearchResult

logger = logging.getLogger(__name__)

# 用于去除 MediaWiki snippet 中的 span.searchmatch 标签
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class WikipediaEngine(BaseSearchEngine):
    """维基百科搜索引擎实现。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.language = str(self.config.get("language") or "zh").strip().lower()
        self.base_url = f"https://{self.language}.wikipedia.org/w/api.php"
        self.headers.update({
            "Accept": "application/json",
            "User-Agent": "MaiBot-WebSearch/4.1.1 (https://github.com/Wenaixi/mai-realtime-web-search; bot@wenxi.dev)",
        })

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        limit = max(1, min(num_results or self.max_results, 30))
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "1",
            "format": "json",
            "srlimit": str(limit),
        }

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    proxy=self.proxy,
                ) as resp:
                    if resp.status >= 400:
                        logger.warning("维基百科请求异常: status=%s", resp.status)
                        return []
                    data = await resp.json()
        except Exception as exc:
            logger.warning("维基百科网络请求失败: %s", exc)
            return []

        search_items = data.get("query", {}).get("search", [])
        if not isinstance(search_items, list):
            return []

        results: List[SearchResult] = []
        for item in search_items:
            if not isinstance(item, dict):
                continue
            title = self.tidy_text(str(item.get("title") or ""))
            if not title:
                continue

            raw_snippet = str(item.get("snippet") or "")
            clean_snippet = self.tidy_text(_HTML_TAG_RE.sub("", raw_snippet))

            url = f"https://{self.language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"

            results.append(
                SearchResult(
                    title=f"{title} - 维基百科",
                    url=url,
                    snippet=clean_snippet,
                    content=clean_snippet,
                    rank=len(results) + 1,
                )
            )
            if len(results) >= limit:
                break

        return results
