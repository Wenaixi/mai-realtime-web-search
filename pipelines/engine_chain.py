"""多引擎搜索 fallback 链。

EngineChain 持有所有引擎实例 + 当次搜索的状态(last_success_engine /
last_tavily_answer)。SearchPipeline 通过它发起搜索。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Optional
import urllib.parse

from ..search_engines.anysearch import AnySearchEngine
from ..search_engines.baidu import BaiduEngine
from ..search_engines.bing import BingEngine
from ..search_engines.brave import BraveEngine
from ..search_engines.deepseek import DeepSeekEngine
from ..search_engines.duckduckgo import DuckDuckGoEngine
from ..search_engines.exa import ExaEngine
from ..search_engines.google import GoogleEngine
from ..search_engines.searxng import SearXNGEngine
from ..search_engines.sogou import SogouEngine
from ..search_engines.tavily import TavilyEngine
from ..search_engines.wikipedia import WikipediaEngine
from ..search_engines.you import (
    YouContentsClient,
    YouLiveNewsEngine,
    YouSearchEngine,
)

if TYPE_CHECKING:
    from ..config import EnginesSection, SearchBackendSection
    from ..search_engines.base import SearchResult

logger = logging.getLogger(__name__)


def _build_common_cfg(backend: "SearchBackendSection") -> dict[str, Any]:
    return {
        "timeout": backend.timeout,
        "proxy": backend.proxy or None,
        "max_results": backend.max_results,
    }


def _build_engine_dict(
    engine_name: str,
    engines: "EnginesSection",
    common: dict[str, Any],
) -> dict[str, Any]:
    """根据 engine_name 从 EnginesSection 提取该引擎需要的配置 dict。"""
    cfg: dict[str, Any] = {**common}
    base_name = engine_name.split("_")[0] if engine_name.startswith("you_") else engine_name
    dedicated_proxy = getattr(engines, f"{base_name}_proxy", getattr(engines, f"{engine_name}_proxy", "")).strip()
    if dedicated_proxy:
        if dedicated_proxy.lower() in ("direct", "none", "off"):
            cfg["proxy"] = None
        else:
            cfg["proxy"] = dedicated_proxy
    if engine_name == "google":
        cfg.update({"enabled": engines.google_enabled, "language": engines.google_language})
    elif engine_name == "bing":
        cfg.update({"enabled": engines.bing_enabled, "region": engines.bing_region})
    elif engine_name == "sogou":
        cfg.update({"enabled": engines.sogou_enabled})
    elif engine_name == "baidu":
        cfg.update({"enabled": engines.baidu_enabled})
    elif engine_name == "brave":
        cfg.update({"enabled": engines.brave_enabled})
    elif engine_name == "wikipedia":
        cfg.update({"enabled": engines.wikipedia_enabled, "language": engines.wikipedia_language})
    elif engine_name == "searxng":
        cfg.update(
            {
                "enabled": engines.searxng_enabled,
                "base_url": engines.searxng_base_url,
                "categories": engines.searxng_categories,
                "engines": engines.searxng_engines,
                "secret_key": engines.searxng_secret_key,
            }
        )
    elif engine_name == "duckduckgo":
        timelimit = engines.duckduckgo_timelimit
        cfg.update(
            {
                "enabled": engines.duckduckgo_enabled,
                "region": engines.duckduckgo_region,
                "backend": engines.duckduckgo_backend,
                "safesearch": engines.duckduckgo_safesearch,
                "timelimit": None if timelimit in ("", "none") else timelimit,
            }
        )
    elif engine_name == "tavily":
        cfg.update(
            {
                "enabled": engines.tavily_enabled,
                "api_keys": list(engines.tavily_api_keys),
                "search_depth": engines.tavily_search_depth,
                "include_raw_content": engines.tavily_include_raw_content,
                "include_answer": engines.tavily_include_answer,
                "topic": engines.tavily_topic,
                "turbo": engines.tavily_turbo,
            }
        )
    elif engine_name == "anysearch":
        cfg.update(
            {
                "enabled": engines.anysearch_enabled,
                "api_keys": list(engines.anysearch_api_keys),
                "tag": engines.anysearch_tag,
                "zone": "" if engines.anysearch_zone == "auto" else engines.anysearch_zone,
                "language": engines.anysearch_language,
                "params": json.loads(engines.anysearch_params) if engines.anysearch_params else {},
                "format": engines.anysearch_format,
            }
        )
    elif engine_name == "exa":
        cfg.update(
            {
                "enabled": engines.exa_enabled,
                "api_keys": list(engines.exa_api_keys),
                "search_type": engines.exa_search_type,
                "category": engines.exa_category,
                "include_domains": list(engines.exa_include_domains),
                "exclude_domains": list(engines.exa_exclude_domains),
                "start_published_date": engines.exa_start_published_date,
                "end_published_date": engines.exa_end_published_date,
                "user_location": engines.exa_user_location,
                "moderation": engines.exa_moderation,
                "objective": engines.exa_objective,
                "additional_queries": list(engines.exa_additional_queries),
                "include_highlights": engines.exa_include_highlights,
                "highlights_query": engines.exa_highlights_query,
                "highlights_max_characters": engines.exa_highlights_max_characters,
                "include_text": engines.exa_include_text,
                "text_max_characters": engines.exa_text_max_characters,
                "max_age_hours": engines.exa_max_age_hours,
                "livecrawl_timeout_ms": engines.exa_livecrawl_timeout_ms,
            }
        )
    elif engine_name == "deepseek":
        cfg.update(
            {
                "enabled": engines.deepseek_enabled,
                "api_keys": list(engines.deepseek_api_keys),
                "base_url": engines.deepseek_base_url,
                "model": engines.deepseek_model,
                "max_tokens": engines.deepseek_max_tokens,
            }
        )
    elif engine_name == "you":
        cfg.update(
            {
                "enabled": engines.you_enabled,
                "api_keys": list(engines.you_api_keys),
                "freshness": engines.you_freshness,
                "offset": engines.you_offset,
                "country": engines.you_country,
                "language": engines.you_language,
                "safesearch": engines.you_safesearch,
                "livecrawl": engines.you_livecrawl,
                "livecrawl_formats": engines.you_livecrawl_formats,
            }
        )
    elif engine_name == "you_news":
        cfg.update(
            {
                "enabled": engines.you_news_enabled,
                "api_keys": list(engines.you_api_keys),
            }
        )
    elif engine_name == "you_contents":
        cfg.update(
            {
                "enabled": engines.you_contents_enabled,
                "api_keys": list(engines.you_api_keys),
                "format": engines.you_contents_format,
                "force": engines.you_contents_force,
            }
        )
    elif engine_name == "you_images":
        cfg.update(
            {
                "enabled": engines.you_images_enabled,
                "api_keys": list(engines.you_api_keys),
            }
        )
    return cfg


class EngineChain:
    """多引擎搜索 fallback 链"""

    def __init__(self, engines: "EnginesSection", backend: "SearchBackendSection") -> None:
        self._engines_cfg = engines
        self._backend_cfg = backend

        common = _build_common_cfg(backend)
        # content_timeout 用于内容抓取(you_contents)
        contents_common = {**common, "timeout": backend.content_timeout or common["timeout"]}

        self.google = GoogleEngine(_build_engine_dict("google", engines, common))
        self.bing = BingEngine(_build_engine_dict("bing", engines, common))
        self.sogou = SogouEngine(_build_engine_dict("sogou", engines, common))
        self.baidu = BaiduEngine(_build_engine_dict("baidu", engines, common))
        self.brave = BraveEngine(_build_engine_dict("brave", engines, common))
        self.wikipedia = WikipediaEngine(_build_engine_dict("wikipedia", engines, common))
        self.searxng = SearXNGEngine(_build_engine_dict("searxng", engines, common))
        self.duckduckgo = DuckDuckGoEngine(_build_engine_dict("duckduckgo", engines, common))
        self.tavily = TavilyEngine(_build_engine_dict("tavily", engines, common))
        self.anysearch = AnySearchEngine(_build_engine_dict("anysearch", engines, common))
        self.exa = ExaEngine(_build_engine_dict("exa", engines, common))
        self.deepseek = DeepSeekEngine(_build_engine_dict("deepseek", engines, common))
        self.you = YouSearchEngine(_build_engine_dict("you", engines, common))
        self.you_news = YouLiveNewsEngine(_build_engine_dict("you_news", engines, common))
        self.you_contents = YouContentsClient(_build_engine_dict("you_contents", engines, contents_common))

        self.last_success_engine: Optional[str] = None
        self.last_tavily_answer: Optional[str] = None

    def _normalize_url(self, url: str) -> str:
        """SearXNG 风格 URL 归一化清洗：剥离追踪参数、小写域名与协议。"""
        try:
            parsed = urllib.parse.urlparse(url.strip())
            scheme = parsed.scheme.lower() or "https"
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = parsed.path.rstrip("/")
            # 过滤常见的点击监控与追踪 Query 参数
            q_list = urllib.parse.parse_qsl(parsed.query)
            clean_q = [
                (k, v) for k, v in q_list
                if not k.lower().startswith(("utm_", "spm", "_hs", "gclid", "fbclid", "ref_", "from_"))
            ]
            q_str = urllib.parse.urlencode(sorted(clean_q)) if clean_q else ""
            return f"{scheme}://{netloc}{path}" + (f"?{q_str}" if q_str else "")
        except Exception:
            return url.strip().rstrip("/")

    async def search_aggregated(
        self,
        query: str,
        num_results: int,
        *,
        engine_override: Optional[str] = None,
        tavily_topic: Optional[str] = None,
    ) -> tuple[list[SearchResult], str]:
        """SearXNG 风格的多引擎并发聚合、去重与加权排序检索。

        Args:
            query: 搜索关键词
            num_results: 期望返回的结果上限
            engine_override: 调用方或 AI 显式指定的单个引擎（如 baidu, wikipedia 等）
            tavily_topic: 可选的 Tavily topic 覆写

        Returns:
            Tuple[list[SearchResult], str]: 聚合去重排序后的搜索结果列表，以及命中的引擎标识说明
        """
        engines_cfg = self._engines_cfg
        default_engine = self._backend_cfg.default_engine

        all_engines_map: dict[str, Any] = {
            "deepseek": self.deepseek,
            "tavily": self.tavily,
            "anysearch": self.anysearch,
            "searxng": self.searxng,
            "exa": self.exa,
            "you": self.you,
            "you_news": self.you_news,
            "google": self.google,
            "bing": self.bing,
            "baidu": self.baidu,
            "sogou": self.sogou,
            "brave": self.brave,
            "duckduckgo": self.duckduckgo,
            "wikipedia": self.wikipedia,
        }

        # 1. 显式指定单引擎时，执行精准单源检索
        if engine_override and engine_override in all_engines_map:
            target_engine = all_engines_map[engine_override]
            if getattr(engines_cfg, f"{engine_override}_enabled", False):
                try:
                    kw = {"topic": tavily_topic} if engine_override == "tavily" and tavily_topic else {}
                    res = await target_engine.search(query, num_results, **kw)
                    if res:
                        self.last_success_engine = engine_override
                        return res, engine_override
                except Exception as exc:
                    logger.warning("指定引擎 %s 搜索异常: %s", engine_override, exc)

        # 2. 筛选所有启用的可用引擎
        active_engines: list[tuple[str, Any]] = []
        for name, engine in all_engines_map.items():
            if not getattr(engines_cfg, f"{name}_enabled", False):
                continue
            if name in {"deepseek", "tavily", "exa", "you", "you_news"} and hasattr(engine, "has_api_keys"):
                if not engine.has_api_keys():
                    continue
            active_engines.append((name, engine))

        if not active_engines:
            return [], ""

        # 3. SearXNG 核心思想：多可用引擎全并发异步查询
        async def _query_single(eng_name: str, eng_instance: Any) -> tuple[str, list[SearchResult]]:
            try:
                kw = {"topic": tavily_topic} if eng_name == "tavily" and tavily_topic else {}
                r = await eng_instance.search(query, num_results, **kw)
                return eng_name, (r or [])
            except Exception as exc:
                logger.warning("并发聚合检索中引擎 %s 异常: %s", eng_name, exc)
                return eng_name, []

        tasks = [_query_single(name, eng) for name, eng in active_engines]
        engine_responses = await asyncio.gather(*tasks, return_exceptions=False)

        # 4. SearXNG 结果去重与倒数排名融合评分 (Reciprocal Rank Fusion)
        merged_results: dict[str, dict[str, Any]] = {}
        successful_engines: list[str] = []

        for eng_name, r_list in engine_responses:
            if not r_list:
                continue
            successful_engines.append(eng_name)
            for rank_idx, item in enumerate(r_list, start=1):
                norm_key = self._normalize_url(item.url)
                if not norm_key:
                    norm_key = item.title.strip().lower()

                # 打分算法：排名越靠前得分越高；被多个引擎同时命中的结果累加得分
                score = 1.0 / rank_idx
                if eng_name == default_engine:
                    score *= 1.2  # 默认首选引擎额外权重大 20%

                if norm_key in merged_results:
                    merged_results[norm_key]["score"] += score
                    merged_results[norm_key]["engines"].append(eng_name)
                    # 保留更详尽的摘要
                    existing = merged_results[norm_key]["result"]
                    if len(item.snippet or "") > len(existing.snippet or ""):
                        existing.snippet = item.snippet
                    if len(item.content or "") > len(existing.content or ""):
                        existing.content = item.content
                else:
                    merged_results[norm_key] = {
                        "result": item,
                        "score": score,
                        "engines": [eng_name],
                    }

        if not merged_results:
            return [], ""

        # 5. 按融合得分降序排序并截取上限
        ranked_entries = sorted(merged_results.values(), key=lambda x: x["score"], reverse=True)
        final_results: list[SearchResult] = []
        for new_rank, entry in enumerate(ranked_entries[:num_results], start=1):
            r = entry["result"]
            r.rank = new_rank
            final_results.append(r)

        summary_name = f"searxng_aggregated({', '.join(successful_engines)})"
        self.last_success_engine = summary_name
        logger.info("SearXNG 聚合检索完成: 命中 %d 个引擎, 输出 %d 条高权结果", len(successful_engines), len(final_results))
        return final_results, summary_name

    async def search_with_fallback(
        self,
        query: str,
        num_results: int,
        *,
        tavily_topic: Optional[str] = None,
    ) -> tuple[list[SearchResult], str]:
        """向后兼容接口：自动路由到 SearXNG 并发聚合与去重排序检索。"""
        return await self.search_aggregated(query, num_results, tavily_topic=tavily_topic)
