"""Offline tests for new search engines: SearXNG, Baidu, Brave, and Wikipedia."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_PLUGINS_ROOT = Path(__file__).resolve().parents[2]
for root in (_PLUGIN_ROOT, _PLUGINS_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from search_engines.searxng import SearXNGEngine
from search_engines.baidu import BaiduEngine
from search_engines.brave import BraveEngine
from search_engines.wikipedia import WikipediaEngine


def mock_response(body: object = None, status: int = 200, *, is_json: bool = True, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status = status
    if is_json:
        resp.text = AsyncMock(return_value=json.dumps(body))
        resp.json = AsyncMock(return_value=body)
    else:
        resp.text = AsyncMock(return_value=text)
        resp.json = AsyncMock(side_effect=ValueError("Not JSON"))
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=resp)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


class NewSearchEnginesTests(unittest.IsolatedAsyncioTestCase):
    async def test_searxng_parses_json_results_properly(self) -> None:
        engine = SearXNGEngine({
            "base_url": "https://searx.example.org",
            "categories": "general",
            "engines": "google,bing",
            "secret_key": "tok-123",
        })
        fake_data = {
            "results": [
                {
                    "title": "SearXNG Official",
                    "url": "https://docs.searxng.org",
                    "content": "A privacy-respecting, hackable metasearch engine.",
                }
            ]
        }
        mock_ctx = mock_response(fake_data, status=200, is_json=True)
        with patch("aiohttp.ClientSession.get", return_value=mock_ctx):
            results = await engine.search("searxng", 5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "SearXNG Official")
        self.assertEqual(results[0].url, "https://docs.searxng.org")
        self.assertIn("privacy-respecting", results[0].snippet)

    async def test_searxng_handles_403_gracefully(self) -> None:
        engine = SearXNGEngine({"base_url": "https://searx.example.org"})
        mock_ctx = mock_response(None, status=403, is_json=False)
        with patch("aiohttp.ClientSession.get", return_value=mock_ctx):
            results = await engine.search("test", 5)
        self.assertEqual(results, [])

    async def test_wikipedia_parses_api_and_cleans_tags(self) -> None:
        engine = WikipediaEngine({"language": "zh"})
        fake_data = {
            "query": {
                "search": [
                    {
                        "title": "Python",
                        "snippet": "Python是一种跨平台的计算机<span class=\"searchmatch\">程序设计语言</span>。",
                    }
                ]
            }
        }
        mock_ctx = mock_response(fake_data, status=200, is_json=True)
        with patch("aiohttp.ClientSession.get", return_value=mock_ctx):
            results = await engine.search("Python", 5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python - 维基百科")
        self.assertIn("https://zh.wikipedia.org/wiki/Python", results[0].url)
        self.assertNotIn("<span", results[0].snippet)
        self.assertIn("程序设计语言", results[0].snippet)

    async def test_baidu_parses_html_containers(self) -> None:
        engine = BaiduEngine()
        html = """
        <html><body>
        <div class="result c-container">
            <h3 class="t"><a href="https://www.baidu.com/link?url=xyz">测试标题</a></h3>
            <div class="c-abstract">这是百度搜索正文摘要内容。</div>
        </div>
        </body></html>
        """
        mock_ctx = mock_response(status=200, is_json=False, text=html)
        with patch("aiohttp.ClientSession.get", return_value=mock_ctx):
            results = await engine.search("测试", 5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "测试标题")
        self.assertEqual(results[0].url, "https://www.baidu.com/link?url=xyz")
        self.assertEqual(results[0].snippet, "这是百度搜索正文摘要内容。")

    async def test_brave_parses_html_snippets(self) -> None:
        engine = BraveEngine()
        html = """
        <html><body>
        <div class="snippet">
            <a class="heading-title" href="https://brave.com/search">Brave Search</a>
            <div class="snippet-description">Private, independent web search.</div>
        </div>
        </body></html>
        """
        mock_ctx = mock_response(status=200, is_json=False, text=html)
        with patch("aiohttp.ClientSession.get", return_value=mock_ctx):
            results = await engine.search("brave", 5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Brave Search")
        self.assertEqual(results[0].url, "https://brave.com/search")
        self.assertEqual(results[0].snippet, "Private, independent web search.")


if __name__ == "__main__":
    unittest.main()
