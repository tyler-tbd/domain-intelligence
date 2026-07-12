from .models import InvestigationResult, RawEvidence
from .feedback_store import load_overrides

def classify(raw: RawEvidence, market: dict, company: dict) -> InvestigationResult:
    evidence = []
    overrides = load_overrides()

    if raw.domain.lower() in overrides:
        classification = overrides[raw.domain.lower()]
        confidence = "high"
        evidence.append("Exact reviewed-domain override applied.")
    elif (
        market.get("broker_inquiry_hits", [])
        and not market["explicit_sale_phrase_hits"]
    ):
        classification = "likely for sale"
        confidence = "high" if market["sale_marketplace_hits"] else "medium"
        evidence.append(
            "Brokered acquisition inquiry detected: "
            + ", ".join(market.get("broker_inquiry_hits", [])[:5])
        )
    elif (
        market["sale_marketplace_hits"]
        or market["sale_url_hits"]
        or market["explicit_sale_phrase_hits"]
    ):
        classification = "for sale"
        confidence = "high"
        if market["sale_marketplace_hits"]:
            evidence.append(
                "Marketplace detected: "
                + ", ".join(market["sale_marketplace_hits"][:5])
            )
        if market["sale_url_hits"]:
            evidence.append(
                "Sale URL pattern detected: "
                + ", ".join(market["sale_url_hits"][:5])
            )
        if market["explicit_sale_phrase_hits"]:
            evidence.append(
                "Explicit sale language detected: "
                + ", ".join(market["explicit_sale_phrase_hits"][:5])
            )
    elif (
        not raw.dns_resolves
        or raw.http_status is None
        or bool(raw.fetch_error)
        or raw.visible_word_count <= 10
    ):
        classification = "likely for sale"
        confidence = "low" if (
            not raw.dns_resolves or raw.http_status is None or raw.fetch_error
        ) else "medium"
        if not raw.dns_resolves:
            evidence.append("Domain does not currently resolve in DNS.")
        elif raw.http_status is None or raw.fetch_error:
            evidence.append("Website did not respond or could not be reached.")
        else:
            evidence.append(
                f"Extremely sparse page with {raw.visible_word_count} visible words."
            )
    elif raw.redirects_to_different_root:
        classification = "likely for sale"
        confidence = "medium"
        evidence.append(
            f"Redirects to different root domain: {raw.destination_root_domain}"
        )
    elif company["placeholder_hits"] and raw.sparse_content:
        classification = "likely for sale"
        confidence = "medium"
        evidence.append("Sparse placeholder/coming-soon page detected.")
    elif company["parking_hits"]:
        classification = "likely for sale"
        confidence = "medium"
        evidence.append(
            "Parking signals detected: "
            + ", ".join(company["parking_hits"][:5])
        )
    elif len(company["active_site_hits"]) >= 3 and raw.visible_word_count >= 120:
        classification = "not for sale"
        confidence = "medium"
        evidence.append(
            "Strong operating-company signals: "
            + ", ".join(company["active_site_hits"][:8])
        )
    else:
        classification = "check manually"
        confidence = "low" if raw.fetch_error else "medium"
        evidence.append("Automated evidence is incomplete or ambiguous.")

    if raw.final_url:
        evidence.append(f"Final URL: {raw.final_url}")
    if raw.page_title:
        evidence.append(f"Title: {raw.page_title}")
    if raw.fetch_error:
        evidence.append(f"Fetch error: {raw.fetch_error}")

    return InvestigationResult(
        name=raw.name,
        domain=raw.domain,
        backend_classification=classification,
        backend_confidence=confidence,
        backend_evidence=evidence,
        dns_resolves=raw.dns_resolves,
        http_status=raw.http_status,
        starting_url=raw.starting_url,
        final_url=raw.final_url,
        redirect_chain=raw.redirect_chain,
        redirects_to_different_root=raw.redirects_to_different_root,
        destination_root_domain=raw.destination_root_domain,
        sale_marketplace_hits=market["sale_marketplace_hits"],
        sale_url_hits=market["sale_url_hits"],
        explicit_sale_phrase_hits=market["explicit_sale_phrase_hits"],
        broker_inquiry_hits=market.get("broker_inquiry_hits", []),
        parking_hits=company["parking_hits"],
        placeholder_hits=company["placeholder_hits"],
        active_site_hits=company["active_site_hits"],
        page_title=raw.page_title,
        meta_description=raw.meta_description,
        visible_word_count=raw.visible_word_count,
        sparse_content=raw.sparse_content,
        fetch_error=raw.fetch_error,
    )
