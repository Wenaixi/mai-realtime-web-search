"""Brave 独立隐私搜索引擎实现。

- 拥有独立网页索引，无追踪隐私检索；
- 结构化提取网页标题、跳转链接与正文描述；
- 支持独立代理配置与无代理直连。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from .base import BaseSearchEngine, SearchResult, USER_AGENTS

logger = logging.getLogger(__name__)


class BraveEngine(BaseSearchEngine):
    """Brave 搜索引擎实现。"""

    BASE_URL: str = "https://search.brave.com/search"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Referer": "https://search.brave.com/",
        })

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        limit = max(1, min(num_results or self.max_results, 30))
        params = {
            "q": query,
            "source": "web",
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
                        logger.warning("Brave 搜索请求异常: status=%s", resp.status)
                        return []
                    html = await resp.text()
        except Exception as exc:
            logger.warning("Brave 搜索网络请求失败: %s", exc)
            return []

        soup = BeautifulSoup(html, "html.parser")
        results: List[SearchResult] = []
        seen_urls = set()

        items = soup.select("div.snippet, div[data-type='web'], div.fdb")
        for item in items:
            title_node = item.select_one("a.heading-title, .title, h2, a[href]")
            if not title_node:
                continue

            title = self.tidy_text(title_node.get_text(strip=True))
            url = title_node.get("href", "")
            if not url and title_node.parent:
                link = title_node.parent.select_one("a[href]")
                url = link.get("href", "") if link else ""

            url = url.strip()
            if not url or not url.startswith("http") or url in seen_urls:
                continue

            desc_node = item.select_one(".snippet-description, .snippet-content, .content, p")
            snippet = self.tidy_text(desc_node.get_text(strip=True)) if desc_node else ""

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
