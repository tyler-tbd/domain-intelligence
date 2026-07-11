import socket
import re
from urllib.parse import urljoin

import dns.resolver
import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as browser_requests

from .config import (
    DEFAULT_TIMEOUT,
    MAX_REDIRECTS,
    MAX_TEXT_CHARS,
    USER_AGENT,
)
from .models import RawEvidence
from .url_utils import normalize_input, registrable_root, root_from_url

def dns_resolves(domain: str) -> bool:
    for record_type in ("A", "AAAA"):
        try:
            if dns.resolver.resolve(domain, record_type, lifetime=3):
                return True
        except Exception:
            pass
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

def fetch_redirect_chain(session, start_url: str, timeout: float):
    chain = []
    current = start_url
    response = None
    error = ""

    for _ in range(MAX_REDIRECTS + 1):
        chain.append(current)
        try:
            response = session.get(
                current,
                timeout=timeout,
                allow_redirects=False,
            )
        except Exception as exc:
            error = str(exc)
            break

        location = ""
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location", "").strip()
        elif response.status_code == 200 and response.text:
            # Domain landers commonly use a tiny JavaScript or meta-refresh
            # redirect while keeping the original domain in the address bar.
            patterns = [
                r"window\.location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]",
                r"location\.replace\(\s*['\"]([^'\"]+)['\"]\s*\)",
                r"http-equiv=['\"]refresh['\"][^>]*content=['\"][^;]+;\s*url=([^'\" >]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    break
        else:
            break

        if not location:
            break

        next_url = urljoin(current, location)
        if next_url in chain:
            break
        current = next_url

    return response, chain, error

def parse_page(response):
    title = ""
    meta_description = ""
    body_text = ""
    parse_error = ""
    if response is None:
        return title, meta_description, body_text, parse_error
    try:
        soup = BeautifulSoup(response.text or "", "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(" ", strip=True)[:200]
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            meta_description = str(meta.get("content")).strip()[:500]
        body_text = soup.get_text(" ", strip=True)
    except Exception as exc:
        parse_error = f"parse_error={exc}"
    return title, meta_description, body_text, parse_error

def browser_like_fetch(start_url: str, timeout: float):
    response = browser_requests.get(
        start_url,
        timeout=timeout,
        allow_redirects=True,
        impersonate="chrome",
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    chain = [str(item.url) for item in response.history] + [str(response.url)]
    return response, chain

def collect_evidence(value: str, timeout: float = DEFAULT_TIMEOUT) -> RawEvidence:
    original_name, domain = normalize_input(value)
    resolves = dns_resolves(domain)

    session = requests.Session()
    session.headers.update(
        {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    )

    response = None
    chain = []
    error = ""
    starting_url = ""

    for candidate in (f"https://{domain}", f"http://{domain}"):
        starting_url = candidate
        response, chain, error = fetch_redirect_chain(session, candidate, timeout)
        if response is not None:
            break

    title, meta_description, body_text, parse_error = parse_page(response)
    if parse_error:
        error = f"{error}; {parse_error}".strip("; ")

    # Some marketplace landers return an empty response to generic HTTP clients
    # while serving complete HTML to real browsers. Retry only empty successful
    # pages with a browser TLS fingerprint so ordinary investigations stay cheap.
    if response is not None and response.status_code == 200 and not body_text.strip():
        try:
            fallback_response, fallback_chain = browser_like_fetch(starting_url, timeout)
            fallback_title, fallback_meta, fallback_text, fallback_error = parse_page(
                fallback_response
            )
            if fallback_text.strip() or fallback_title or fallback_meta:
                response = fallback_response
                chain = fallback_chain
                title = fallback_title
                meta_description = fallback_meta
                body_text = fallback_text
            if fallback_error:
                error = f"{error}; {fallback_error}".strip("; ")
        except Exception as exc:
            error = f"{error}; browser_fetch_error={exc}".strip("; ")

    final_url = chain[-1] if chain else starting_url
    source_root = registrable_root(domain)
    destination_root = root_from_url(final_url)
    cross_root = bool(destination_root and destination_root != source_root)

    word_count = len(body_text.split())

    return RawEvidence(
        name=original_name,
        domain=domain,
        dns_resolves=resolves,
        http_status=response.status_code if response is not None else None,
        starting_url=starting_url,
        final_url=final_url,
        redirect_chain=chain,
        redirects_to_different_root=cross_root,
        destination_root_domain=destination_root,
        page_title=title,
        meta_description=meta_description,
        visible_text_sample=body_text[:MAX_TEXT_CHARS],
        visible_word_count=word_count,
        sparse_content=word_count < 120,
        fetch_error=error[:500],
    )
