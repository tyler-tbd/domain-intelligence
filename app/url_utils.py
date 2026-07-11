import re
from urllib.parse import urlparse

def normalize_input(value: str) -> tuple[str, str]:
    cleaned = value.strip().lower()

    if cleaned.startswith(("http://", "https://")):
        host = urlparse(cleaned).netloc.split(":", 1)[0]
        host = host.removeprefix("www.")
        return value, host

    if cleaned.endswith(".com"):
        return value, re.sub(r"[^a-z0-9.-]", "", cleaned)

    slug = re.sub(r"[^a-z0-9]", "", cleaned)
    if not slug:
        raise ValueError("Input did not contain a usable brand name.")
    return value, f"{slug}.com"

def registrable_root(host: str) -> str:
    host = (host or "").lower().split(":", 1)[0].removeprefix("www.")
    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])

def root_from_url(url: str) -> str:
    return registrable_root(urlparse(url).netloc)
