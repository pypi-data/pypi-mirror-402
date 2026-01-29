import ipaddress
from urllib.parse import urlparse
import socket

def is_allowed_target(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    host = parsed.hostname
    if host in ("localhost",):
        return True

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except Exception:
        return False

    return ip.is_loopback or ip.is_private