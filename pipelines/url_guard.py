"""URL 安全校验：SSRF 防护。

在抓取任何用户提供的 URL 之前调用，拒绝：
- 非 http/https scheme（file/ftp/gopher 等一律拒）；
- 解析后命中回环 / 私网 / 链路本地 / 云元数据段的地址；
- 无法解析的主机名。

设计要点：校验的是 **DNS 解析后的真实 IP**，而不是 hostname 字符串——否则
``evil.example``（A 记录指向 127.0.0.1）可以绕过；解析结果逐一检查，避免
DNS 返回多个记录时漏掉其中一个内网地址。调用方还应在 HTTP 客户端上
关闭自动重定向，并对每个重定向跳转目标再次执行本校验。
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# 云厂商元数据服务常用地址（部分不在标准私网段内）。
_BLOCKED_IPS = frozenset({
    ipaddress.ip_address("169.254.169.254"),  # AWS/GCP/Azure/阿里云 元数据
    ipaddress.ip_address("100.100.100.200"),  # 阿里云元数据
})

_ALLOWED_SCHEMES = ("http", "https")


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """判断单个 IP 是否落入禁止访问的范围。"""
    if ip in _BLOCKED_IPS:
        return True  # 云厂商元数据服务等特殊地址
    if ip.is_loopback or ip.is_private or ip.is_link_local:
        return True
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    # IPv4-mapped IPv6（::ffff:127.0.0.1）也要按 IPv4 判定一遍
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_blocked_ip(ip.ipv4_mapped)
    return False


def validate_url(url: str) -> tuple[bool, str]:
    """校验待抓取 URL 是否安全。

    Args:
        url: 用户提供的 URL。

    Returns:
        (ok, reason)：ok 为 False 时 reason 说明拒绝原因。
    """
    try:
        parsed = urlparse(url)
    except Exception as exc:  # noqa: BLE001
        return False, f"URL 解析失败: {exc}"

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return False, f"仅支持 http/https，拒绝 scheme={parsed.scheme!r}"

    host = (parsed.hostname or "").strip()
    if not host:
        return False, "URL 缺少主机名"

    # 直接是 IP 字面量：不必 DNS 解析
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _is_blocked_ip(literal):
            return False, f"拒绝访问内部地址: {host}"
        return True, ""

    # 域名：解析全部地址后逐一检查
    try:
        infos = socket.getaddrinfo(host, parsed.port or None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        return False, f"主机名解析失败: {host}: {exc}"

    if not infos:
        return False, f"主机名无解析结果: {host}"

    for _family, _type, _proto, _canon, sockaddr in infos:
        addr = sockaddr[0]
        try:
            ip = ipaddress.ip_address(addr.split("%", 1)[0])
        except ValueError:
            continue
        if _is_blocked_ip(ip):
            return False, f"拒绝访问内部地址: {host} -> {ip}"

    return True, ""
