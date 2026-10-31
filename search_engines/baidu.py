"""百度搜索引擎实现。

基于 aiohttp + bs4 自实现，国内免代理直连。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from .base import BaseSearchEngine, SearchResult, USER_AGENTS

logger = logging.getLogger(__name__)


class BaiduEngine(BaseSearchEngine):
    """百度搜索引擎实现。"""

    BASE_URL: str = "https://www.baidu.com/s"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.baidu.com/",
        })

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        limit = max(1, min(num_results or self.max_results, 30))
        params = {
            "wd": query,
            "rn": str(limit),
            "ie": "utf-8",
        }

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
        headers = self.headers.copy()
        if USER_AGENTS:
            import random
            headers["User-Agent"] = random.choice(USER_AGENTS)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    proxy=self.proxy,
                ) as resp:
                    if resp.status >= 400:
                        logger.warning("百度搜索请求异常: status=%s", resp.status)
                        return []
                    html = await resp.text()
        except Exception as exc:
            logger.warning("百度搜索网络请求失败: %s", exc)
            return []

        soup = BeautifulSoup(html, "html.parser")
        results: List[SearchResult] = []
        seen_urls = set()

        containers = soup.select("div.result.c-container, div.c-container")
        for box in containers:
            title_node = box.select_one("h3.t a, h3 a")
            if not title_node:
                continue

            title = self.tidy_text(title_node.get_text(strip=True))
            url = title_node.get("href", "").strip()
            if not url or url in seen_urls:
                continue

            abstract_node = box.select_one(".c-abstract, .content-right_8Zs40, .c-span-last, .c-font-normal")
            snippet = self.tidy_text(abstract_node.get_text(strip=True)) if abstract_node else ""

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
