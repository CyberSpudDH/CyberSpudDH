import ipaddress
import re
from urllib.parse import urlparse, urlunparse

HEX32 = re.compile(r"^[a-fA-F0-9]{32}$")
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s\"'>]+")


WEIGHTS = {"sha256": 10, "md5": 8, "domain": 6, "url": 6, "ip": 4, "email": 4, "username": 3, "hostname": 3}


def normalize_value(obs_type: str, value: str) -> str | None:
    value = str(value).strip()
    if not value:
        return None
    if obs_type == "ip":
        return str(ipaddress.ip_address(value))
    if obs_type == "domain":
        return value.rstrip(".").lower().encode("idna").decode("ascii")
    if obs_type == "url":
        p = urlparse(value)
        host = (p.hostname or "").rstrip(".").lower().encode("idna").decode("ascii")
        port = ""
        if p.port and not ((p.scheme == "http" and p.port == 80) or (p.scheme == "https" and p.port == 443)):
            port = f":{p.port}"
        netloc = f"{host}{port}"
        return urlunparse((p.scheme.lower() or "http", netloc, p.path or "/", "", p.query, ""))
    if obs_type == "sha256":
        v = value.lower()
        return v if HEX64.match(v) else None
    if obs_type == "md5":
        v = value.lower()
        return v if HEX32.match(v) else None
    if obs_type == "email":
        m = EMAIL_RE.search(value)
        return m.group(0).lower() if m else None
    if obs_type == "username":
        return value.replace("\\\\", "\\").lower()
    if obs_type == "hostname":
        return value.rstrip(".").lower()
    return None


def extract_observables(payload: dict) -> list[dict]:
    out: list[dict] = []

    key_map = {
        "src_ip": ("ip", "src_ip"), "dst_ip": ("ip", "dst_ip"), "ip": ("ip", "ip"),
        "domain": ("domain", "domain"), "url": ("url", "url"), "sha256": ("sha256", "file_hash"),
        "md5": ("md5", "file_hash"), "email": ("email", "user"), "user": ("username", "user"),
        "username": ("username", "user"), "host": ("hostname", "host"), "hostname": ("hostname", "host"),
    }

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in key_map and isinstance(v, (str, int, float)):
                    t, role = key_map[k]
                    nv = normalize_value(t, str(v))
                    if nv:
                        out.append({"type": t, "value": nv, "role": role, "context": {"key": k}})
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)
        elif isinstance(obj, str):
            for m in URL_RE.findall(obj):
                nv = normalize_value("url", m)
                if nv:
                    out.append({"type": "url", "value": nv, "role": "url", "context": {}})
            for m in EMAIL_RE.findall(obj):
                out.append({"type": "email", "value": m.lower(), "role": "user", "context": {}})

    walk(payload)

    dedup = {(o["type"], o["value"], o.get("role")): o for o in out}
    return list(dedup.values())
