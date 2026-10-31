"""
搜索引擎模块

提供统一的搜索引擎抽象接口和具体实现
"""

from .anysearch import AnySearchEngine
from .baidu import BaiduEngine
from .base import BaseSearchEngine, SearchResult
from .bing import BingEngine
from .brave import BraveEngine
from .deepseek import DeepSeekEngine
from .duckduckgo import DuckDuckGoEngine
from .exa import ExaEngine
from .google import GoogleEngine
from .searxng import SearXNGEngine
from .sogou import SogouEngine
from .tavily import TavilyEngine
from .wikipedia import WikipediaEngine
from .you import YouContentsClient, YouImagesEngine, YouLiveNewsEngine, YouSearchEngine

__all__ = [
    "BaseSearchEngine",
    "SearchResult",
    "AnySearchEngine",
    "BaiduEngine",
    "BingEngine",
    "BraveEngine",
    "DeepSeekEngine",
    "DuckDuckGoEngine",
    "ExaEngine",
    "GoogleEngine",
    "SearXNGEngine",
    "SogouEngine",
    "TavilyEngine",
    "WikipediaEngine",
    "YouSearchEngine",
    "YouLiveNewsEngine",
    "YouContentsClient",
    "YouImagesEngine",
]
