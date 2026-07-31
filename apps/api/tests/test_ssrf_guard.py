import ipaddress

import httpx
import pytest

from app.orchestrator.tools.ssrf_guard import (
    UnsafeUrlError,
    follow_redirects_safely,
    is_safe_url,
    pinned_request,
    resolve_safe_ip,
)


def test_rejects_loopback():
    assert is_safe_url("http://localhost:8000/") is False
    assert is_safe_url("http://127.0.0.1/") is False


def test_rejects_private_ranges():
    assert is_safe_url("http://10.0.0.5/") is False
    assert is_safe_url("http://192.168.1.1/") is False


def test_rejects_link_local_metadata_endpoint():
    # 169.254.169.254 is the AWS/GCP/Azure cloud metadata endpoint - a classic SSRF target.
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False


def test_rejects_non_http_schemes():
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://8.8.8.8/") is False


def test_accepts_public_ip_literal():
    assert is_safe_url("http://8.8.8.8/") is True


def test_resolve_safe_ip_rejects_private_and_missing_hosts():
    assert resolve_safe_ip("localhost") is None
    assert resolve_safe_ip("this-host-does-not-exist.invalid") is None


def test_resolve_safe_ip_accepts_a_public_ip_literal():
    assert resolve_safe_ip("8.8.8.8") == "8.8.8.8"


class _CapturingTransport(httpx.MockTransport):
    """Records the actual outgoing request (URL, headers, extensions) instead of just
    returning canned data - what pinned_request() needs to prove is what the request
    that leaves the process looks like, not what comes back."""

    def __init__(self):
        self.captured: httpx.Request | None = None
        super().__init__(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.captured = request
        return httpx.Response(200, json={"ok": True})


@pytest.mark.asyncio
async def test_pinned_request_connects_to_the_resolved_ip_not_the_hostname():
    transport = _CapturingTransport()
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        resp = await pinned_request(client, "GET", "https://dns.google/resolve?name=example.com")
    assert resp.status_code == 200
    assert transport.captured is not None
    # dns.google resolves to more than one IP (8.8.8.8/8.8.4.4/...) and which one
    # getaddrinfo() returns first isn't guaranteed - assert the connection target is
    # *an IP*, not that resolution picked a specific one.
    connected_host = transport.captured.url.host
    ipaddress.ip_address(connected_host)  # raises ValueError if this isn't an IP at all
    assert connected_host != "dns.google"
    assert transport.captured.headers["host"] == "dns.google"
    assert transport.captured.extensions["sni_hostname"] == "dns.google"
    assert transport.captured.url.path == "/resolve"
    assert str(transport.captured.url.params) == "name=example.com"


@pytest.mark.asyncio
async def test_pinned_request_ignores_caller_supplied_host_header():
    transport = _CapturingTransport()
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        await pinned_request(client, "GET", "https://dns.google/", headers={"Host": "attacker.example"})
    assert transport.captured.headers["host"] == "dns.google"


@pytest.mark.asyncio
async def test_pinned_request_rejects_private_targets_without_making_a_request():
    transport = _CapturingTransport()
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        with pytest.raises(UnsafeUrlError):
            await pinned_request(client, "GET", "http://127.0.0.1:6379/")
        with pytest.raises(UnsafeUrlError):
            await pinned_request(client, "GET", "http://169.254.169.254/latest/meta-data/")
        with pytest.raises(UnsafeUrlError):
            await pinned_request(client, "GET", "ftp://example.com/")
    assert transport.captured is None


class _ScriptedRedirectTransport(httpx.MockTransport):
    """Keys responses by the Host *header* (not the connection host, which
    pinned_request always rewrites to a resolved IP) - lets one mock simulate a
    multi-hop redirect chain across real, DNS-resolvable hostnames."""

    def __init__(self, script: dict[str, httpx.Response]):
        self.script = script
        self.requests: list[httpx.Request] = []
        super().__init__(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.script.get(request.headers.get("host", ""), httpx.Response(404))


@pytest.mark.asyncio
async def test_follow_redirects_safely_returns_directly_when_no_redirect():
    transport = _ScriptedRedirectTransport({"example.com": httpx.Response(200, text="hi")})
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        resp = await follow_redirects_safely(client, "GET", "https://example.com/")
    assert resp.status_code == 200
    assert resp.text == "hi"
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_follow_redirects_safely_follows_and_re_pins_each_hop():
    transport = _ScriptedRedirectTransport(
        {
            "example.com": httpx.Response(302, headers={"location": "https://dns.google/final"}),
            "dns.google": httpx.Response(200, text="final page"),
        }
    )
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        resp = await follow_redirects_safely(client, "GET", "https://example.com/start")
    assert resp.status_code == 200
    assert resp.text == "final page"
    assert len(transport.requests) == 2
    assert transport.requests[0].headers["host"] == "example.com"
    assert transport.requests[1].headers["host"] == "dns.google"
    # Both hops actually connected to a resolved IP, not the hostname - proves the
    # second hop went through pinned_request again, not httpx's own redirect handling.
    for req in transport.requests:
        ipaddress.ip_address(req.url.host)


@pytest.mark.asyncio
async def test_follow_redirects_safely_rejects_a_redirect_to_a_private_target():
    """The exact bypass S4 describes: the first hop is a legitimate public URL: the
    attacker's own server, which then redirects to an internal target as the "page
    content". A guard that only checks the initial URL would follow it straight in."""
    transport = _ScriptedRedirectTransport(
        {"example.com": httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data/"})}
    )
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        with pytest.raises(UnsafeUrlError):
            await follow_redirects_safely(client, "GET", "https://example.com/start")
    # The malicious second hop never reached the transport - rejected before connecting.
    assert len(transport.requests) == 1


@pytest.mark.asyncio
async def test_follow_redirects_safely_gives_up_after_too_many_hops():
    transport = _ScriptedRedirectTransport(
        {
            "example.com": httpx.Response(302, headers={"location": "https://dns.google/next"}),
            "dns.google": httpx.Response(302, headers={"location": "https://example.com/next"}),
        }
    )
    async with httpx.AsyncClient(transport=transport, timeout=10) as client:
        with pytest.raises(UnsafeUrlError):
            await follow_redirects_safely(client, "GET", "https://example.com/start")
