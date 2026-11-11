"""url_guard SSRF 防护的单元测试。

锁定：公网 URL 放行、回环/私网/链路本地/云元数据一律拒绝、
非 http/https scheme 拒绝、IPv4-mapped IPv6 回环拒绝。
"""

import pytest

from pipelines.url_guard import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/page",
        "http://www.baidu.com/",
        "https://news.sina.com.cn/a/b.html",
    ],
)
def test_allows_public_urls(url: str) -> None:
    ok, reason = validate_url(url)
    assert ok, f"公网 URL 应放行: {url} ({reason})"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080/",
        "http://localhost/admin",
        "http://192.168.1.1/x",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://100.100.100.200/",
        "http://[::1]/x",
        "http://[::ffff:127.0.0.1]/x",
    ],
)
def test_blocks_internal_targets(url: str) -> None:
    ok, _reason = validate_url(url)
    assert not ok, f"内部地址必须拒绝: {url}"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://evil.example/x",
        "gopher://127.0.0.1:6379/_INFO",
    ],
)
def test_blocks_non_http_schemes(url: str) -> None:
    ok, _reason = validate_url(url)
    assert not ok, f"非 http/https 必须拒绝: {url}"
