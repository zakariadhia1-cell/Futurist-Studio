"""Blocks the call_api tool (and anything else that fetches an agent-supplied URL on the
server's behalf) from reaching internal/private network targets - without this, an agent
could be steered into hitting the API's own database, Redis, or other internal services
via a plausible-looking "fetch this URL" instruction.

F7 (docs/FIX_PLAN.md, S7 in docs/AUDIT_REPORT.md): the original design resolved and
validated the hostname once via `is_safe_url()`, returned a bool, and left the caller to
make its own httpx request afterwards - which re-resolves DNS independently when it
connects. An attacker-controlled domain with a low TTL can return a public IP for the
check and a private/loopback IP moments later for the real connection (DNS rebinding;
TOCTOU). `pinned_request()` closes that window: it resolves+validates once, then connects
directly to that validated IP (Host header + TLS SNI extension keep virtual hosting and
certificate verification working correctly against the original hostname, not the IP
literal), so there is no second DNS lookup for an attacker to race.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx


class UnsafeUrlError(Exception):
    """Raised by pinned_request() when a URL fails the SSRF safety check."""


def _is_safe_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)


def resolve_safe_ip(hostname: str) -> str | None:
    """Resolves hostname and returns one validated public IP to connect to, or None if
    resolution fails or any resolved address is private/internal (all addresses for a
    hostname are checked, not just the first, so a mixed public+private DNS answer is
    still rejected)."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return None
    if not infos:
        return None
    for _family, _type, _proto, _canonname, sockaddr in infos:
        if not _is_safe_ip(sockaddr[0]):
            return None
    return infos[0][4][0]


def is_safe_url(url: str) -> bool:
    """Boolean-only pre-check - on its own still vulnerable to DNS rebinding, since
    nothing stops a second, independent resolution at connect time. Kept for call sites
    that can't pin their own connection (e.g. a third-party SDK's transport - see the
    residual-risk note where the MCP sse transport uses this). Prefer `pinned_request()`
    for any call site that makes its own httpx request."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    return resolve_safe_ip(hostname) is not None


async def pinned_request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    """SSRF-safe request: validates the URL and connects to the pinned, validated IP
    directly. Raises UnsafeUrlError instead of returning a bool, since by the time this
    runs we're committed to making the request - a caller that ignored a False return
    would defeat the whole point."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Unsicheres URL-Schema: '{parsed.scheme or '(keins)'}'.")
    hostname = parsed.hostname
    if not hostname:
        raise UnsafeUrlError("URL enthaelt keinen Host.")

    safe_ip = resolve_safe_ip(hostname)
    if safe_ip is None:
        raise UnsafeUrlError("URL abgelehnt: kein oeffentliches Ziel oder nicht aufloesbar.")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    ip_netloc = f"[{safe_ip}]:{port}" if ":" in safe_ip else f"{safe_ip}:{port}"
    pinned_url = parsed._replace(netloc=ip_netloc).geturl()

    headers = httpx.Headers(kwargs.pop("headers", None) or {})
    # Always the validated hostname, never caller-suppliable - a caller-controlled Host
    # header here would let arbitrary agent-supplied headers steer virtual-hosting
    # behavior on the pinned IP, defeating the point of validating the hostname at all.
    headers["Host"] = hostname

    extensions = dict(kwargs.pop("extensions", None) or {})
    if parsed.scheme == "https":
        # Keeps TLS SNI - and therefore certificate hostname verification - against the
        # real hostname instead of the IP literal we're actually connecting to.
        extensions["sni_hostname"] = hostname

    return await client.request(method, pinned_url, headers=headers, extensions=extensions, **kwargs)
