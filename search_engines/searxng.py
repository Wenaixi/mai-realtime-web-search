"""SearXNG 实例聚合搜索引擎实现。

- 支持直连自建或公开的 SearXNG 元搜索实例；
- 支持按 categories（默认 general）和底层 engines 筛选聚合源；
- 支持传入可选的访问令牌或 Secret Key；
- 原生支持单独配置代理与无代理直连。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import aiohttp

from .base import BaseSearchEngine, SearchResult

logger = logging.getLogger(__name__)


class SearXNGEngine(BaseSearchEngine):
    """SearXNG 实例元搜索引擎实现。"""

    DEFAULT_BASE_URL = "http://127.0.0.1:8888"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.base_url = str(self.config.get("base_url") or self.DEFAULT_BASE_URL).rstrip("/")
        self.categories = str(self.config.get("categories") or "general").strip()
        self.engines_filter = str(self.config.get("engines") or "").strip()
        self.secret_key = str(self.config.get("secret_key") or "").strip()
        self.language = str(self.config.get("language") or "zh-CN").strip()

        self.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        })
        if self.secret_key:
            self.headers["Authorization"] = f"Bearer {self.secret_key}"

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        if not self.base_url:
            logger.warning("SearXNG base_url 未配置，跳过搜索")
            return []

        limit = max(1, min(num_results or self.max_results, 30))
        params: Dict[str, Any] = {
            "q": query,
            "format": "json",
            "categories": self.categories or "general",
            "language": self.language or "zh-CN",
        }
        if self.engines_filter:
            params["engines"] = self.engines_filter

        endpoint = urljoin(f"{self.base_url}/", "search")
        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    endpoint,
                    params=params,
                    headers=self.headers,
                    proxy=self.proxy,
                ) as resp:
                    if resp.status == 403:
                        logger.warning("SearXNG 实例返回 403 Forbidden（可能未开启 format=json）: %s", self.base_url)
                        return []
                    if resp.status >= 400:
                        logger.warning("SearXNG 请求异常: status=%s, url=%s", resp.status, self.base_url)
                        return []

                    text = await resp.text()
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        logger.warning("SearXNG 返回内容非 JSON 格式")
                        return []

        except Exception as exc:
            logger.warning("SearXNG 请求失败: %s", exc)
            return []

        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            return []

        results: List[SearchResult] = []
        seen_urls = set()

        for item in raw_results:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            title = self.tidy_text(str(item.get("title") or ""))
            snippet = self.tidy_text(str(item.get("content") or ""))

            if not title and not snippet:
                continue

            seen_urls.add(url)
            results.append(
                SearchResult(
                    title=title or url,
                    url=url,
                    snippet=snippet,
                    content=snippet,
                    rank=len(results) + 1,
                )
            )
            if len(results) >= limit:
                break

        return results
