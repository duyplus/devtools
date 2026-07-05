import ipaddress
import json
import socket
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


class IpCheckError(ValueError):
    def __init__(self, key):
        self.key = key
        self.params = {}
        super().__init__(key)


def get_client_ip(request):
    for header in ("CF-Connecting-IP", "X-Real-IP"):
        value = request.headers.get(header, "").split(",", 1)[0].strip()
        if _is_ip(value):
            return value
    if request.access_route:
        value = request.access_route[0]
        if _is_ip(value):
            return value
    return request.remote_addr or "127.0.0.1"


def check_ip_target(target, include_geo=True):
    target = (target or "").strip()
    if not target:
        raise IpCheckError("ip_checker.error.required")

    host = _target_host(target)
    resolved = _resolve_target_ips(host)
    parsed = ipaddress.ip_address(resolved["ipv4"] or resolved["ipv6"])
    result = {
        "target": target,
        "host": host,
        "ip": str(parsed),
        "version": f"IPv{parsed.version}",
        "ipv4": resolved["ipv4"],
        "ipv6": resolved["ipv6"],
        "geo": {},
    }
    if include_geo:
        result["geo"] = _lookup_geo(result["ip"])
    return result


def _target_host(target):
    direct = _strip_brackets(target)
    if _is_ip(direct):
        return direct
    parsed = urlparse(target if "://" in target else f"//{target}")
    host = parsed.hostname or target
    if not host or any(char.isspace() for char in host):
        raise IpCheckError("ip_checker.error.invalid")
    return _strip_brackets(host)


def _resolve_target_ips(host):
    if _is_ip(host):
        address = ipaddress.ip_address(host)
        return {
            "ipv4": str(address) if address.version == 4 else "",
            "ipv6": str(address) if address.version == 6 else "",
        }
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise IpCheckError("ip_checker.error.resolve") from exc
    addresses = []
    for record in records:
        address = record[4][0]
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise IpCheckError("ip_checker.error.resolve")
    result = {"ipv4": "", "ipv6": ""}
    for value in sorted(addresses, key=lambda item: (ipaddress.ip_address(item).version, item)):
        address = ipaddress.ip_address(value)
        key = "ipv4" if address.version == 4 else "ipv6"
        if not result[key]:
            result[key] = str(address)
    return result


def _lookup_geo(ip):
    if not _is_global_ip(ip):
        return {}
    return _lookup_geo_ip_api(ip) or _lookup_geo_ipwhois(ip)


def _lookup_geo_ip_api(ip):
    fields = "status,message,country,regionName,city,lat,lon,timezone,isp,org,as,query"
    try:
        with urlopen(f"http://ip-api.com/json/{ip}?fields={fields}", timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError, ValueError):
        return {}
    if data.get("status") != "success":
        return {}
    return {
        "city": data.get("city") or "",
        "region": data.get("regionName") or "",
        "country": data.get("country") or "",
        "isp": data.get("isp") or data.get("org") or data.get("as") or "",
        "timezone": data.get("timezone") or "",
        "latitude": data.get("lat") if data.get("lat") is not None else "",
        "longitude": data.get("lon") if data.get("lon") is not None else "",
    }


def _lookup_geo_ipwhois(ip):
    try:
        with urlopen(f"https://ipwho.is/{ip}", timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError, ValueError):
        return {}
    if not data.get("success", False):
        return {}
    connection = data.get("connection") or {}
    timezone = data.get("timezone") or {}
    return {
        "city": data.get("city") or "",
        "region": data.get("region") or "",
        "country": data.get("country") or "",
        "isp": connection.get("isp") or connection.get("org") or "",
        "timezone": timezone.get("id") if isinstance(timezone, dict) else "",
        "latitude": data.get("latitude") if data.get("latitude") is not None else "",
        "longitude": data.get("longitude") if data.get("longitude") is not None else "",
    }


def _is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def lookup_public_ips():
    return {
        "ipv4": _lookup_public_ip("https://api.ipify.org", 4),
        "ipv6": _lookup_public_ip("https://ipv6.icanhazip.com", 6),
    }


def _lookup_public_ip(url, version):
    try:
        with urlopen(url, timeout=1.5) as response:
            value = response.read().decode("utf-8").strip()
    except (OSError, URLError, TimeoutError, ValueError):
        return ""
    if not _is_ip(value):
        return ""
    address = ipaddress.ip_address(value)
    return str(address) if address.version == version else ""


def _is_global_ip(value):
    try:
        return ipaddress.ip_address(value).is_global
    except ValueError:
        return False


def _strip_brackets(value):
    return value.strip().removeprefix("[").removesuffix("]")
