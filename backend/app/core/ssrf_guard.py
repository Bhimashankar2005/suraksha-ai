import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional

# Prohibited private and special IP ranges (IPv4 and IPv6)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),          # Private RFC 1918
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier Grade NAT
    ipaddress.ip_network("127.0.0.0/8"),         # Loopback
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),       # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),        # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),        # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),      # Private RFC 1918
    ipaddress.ip_network("198.51.100.0/24"),     # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),      # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),            # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),           # IPv6 Link-Local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
}

def is_ip_restricted(ip_str: str) -> bool:
    """Check if an IP address belongs to loopback, private, link-local, or cloud metadata ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return True
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        return True

def validate_url_and_check_ssrf(url_string: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates the URL syntax and strictly defends against Server-Side Request Forgery (SSRF).
    Returns: (is_safe: bool, normalized_domain: str, block_reason: str)
    """
    if not url_string or not isinstance(url_string, str):
        return False, None, "Empty or invalid URL input."

    url_clean = url_string.strip()
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        url_clean = "https://" + url_clean

    try:
        parsed = urlparse(url_clean)
    except Exception as e:
        return False, None, f"Malformed URL structure: {str(e)}"

    if parsed.scheme not in ["http", "https"]:
        return False, None, f"Prohibited URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, None, "URL does not contain a valid destination hostname."

    hostname = hostname.lower().strip()

    # 1. Block immediate prohibited hostnames
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost") or hostname.endswith(".local") or hostname.endswith(".internal"):
        return False, hostname, f"SSRF Protection: Access to internal or loopback host '{hostname}' is blocked."

    # 2. Check if host is direct IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if is_ip_restricted(str(ip)):
            return False, hostname, f"SSRF Protection: Access to private or link-local IP '{hostname}' is blocked."
    except ValueError:
        pass  # Hostname is a standard domain, not a direct IP literal

    # 3. Prevent octal, hex, or integer encoded IP obfuscations (e.g. http://0177.0.0.1 or http://2130706433)
    parts = hostname.split(".")
    if all(p.isdigit() for p in parts) and len(parts) in [1, 2, 3, 4]:
        try:
            # Reconstruct and check
            raw_int = int(parts[0]) if len(parts) == 1 else None
            if raw_int is not None:
                ip = ipaddress.ip_address(raw_int)
                if is_ip_restricted(str(ip)):
                    return False, hostname, f"SSRF Protection: Obfuscated integer IP '{hostname}' resolves to restricted range."
        except Exception:
            pass

    return True, hostname, None

