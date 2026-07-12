import re

from .models import RawEvidence

SALE_MARKETPLACES = [
    "afternic", "sedo", "dan.com", "godaddy", "hugedomains",
    "brandbucket", "squadhelp", "atom.com", "saw.com",
    "domainmarket", "uniregistry", "buydomains", "daaz.com",
    "domainagents", "sav.com", "spaceship.com",
]

SALE_URL_HINTS = [
    "/forsale/", "/for-sale/", "domain-for-sale", "buy-domain",
    "makeoffer", "make-offer", "request-price", "lease-to-own",
]

SALE_PHRASES = [
    "this domain is for sale", "domain is for sale", "buy this domain",
    "make an offer", "get a price", "purchase this domain",
    "available for acquisition", "submit offer", "request price",
    "lease to own",
]

BROKER_INQUIRY_PHRASES = [
    "may still be available", "get this domain", "contact our domain broker",
    "inquire about this domain", "domain acquisition inquiry",
    "all inquiries", "all inquires", "domain inquiries", "domain inquires",
]

def find_hits(text: str, patterns: list[str]) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in patterns if pattern in lowered]

def detect_marketplace_signals(raw: RawEvidence) -> dict:
    combined = " ".join(
        [
            raw.domain,
            raw.final_url,
            " ".join(raw.redirect_chain),
            raw.page_title,
            raw.meta_description,
            raw.visible_text_sample,
        ]
    )

    broker_hits = find_hits(combined, BROKER_INQUIRY_PHRASES)
    same_domain_email = re.search(
        rf"\bdomain\s*@\s*(?:www\.)?{re.escape(raw.domain)}\b",
        combined,
        re.IGNORECASE,
    )
    if same_domain_email:
        broker_hits.append(same_domain_email.group(0).replace(" ", "").lower())

    return {
        "sale_marketplace_hits": find_hits(combined, SALE_MARKETPLACES),
        "sale_url_hits": find_hits(combined, SALE_URL_HINTS),
        "explicit_sale_phrase_hits": find_hits(combined, SALE_PHRASES),
        "broker_inquiry_hits": list(dict.fromkeys(broker_hits)),
    }
