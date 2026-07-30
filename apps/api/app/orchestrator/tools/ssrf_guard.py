"""Blocks the call_api tool (and anything else that fetches an agent-supplied URL on the
server's behalf) from reaching internal/private network targets - without this, an agent
could be steered into hitting the API's own database, Redis, or other internal services
via a plausible-looking "fetch this URL" instruction."""
import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for family, _, _, _, sockaddr in infos:
        try:
            ip = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
    return True
