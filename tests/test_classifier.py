from app.classifier import classify
from app.models import RawEvidence

def raw(**kwargs):
    defaults = dict(
        name="Example",
        domain="example.com",
        dns_resolves=True,
        http_status=200,
        starting_url="https://example.com",
        final_url="https://example.com",
        redirect_chain=["https://example.com"],
        redirects_to_different_root=False,
        destination_root_domain="example.com",
        page_title="",
        meta_description="",
        visible_text_sample="",
        visible_word_count=0,
        sparse_content=True,
        fetch_error="",
    )
    defaults.update(kwargs)
    return RawEvidence(**defaults)

def test_godaddy_forsale_is_for_sale():
    r = raw(
        name="Courseback",
        domain="courseback.com",
        final_url="https://forsale.godaddy.com/forsale/courseback.com",
        redirect_chain=[
            "https://courseback.com",
            "https://forsale.godaddy.com/forsale/courseback.com",
        ],
        redirects_to_different_root=True,
        destination_root_domain="godaddy.com",
    )
    market = {
        "sale_marketplace_hits": ["godaddy"],
        "sale_url_hits": ["/forsale/"],
        "explicit_sale_phrase_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }
    result = classify(r, market, company)
    assert result.classification == "for sale"

def test_cross_domain_redirect_is_likely_for_sale():
    r = raw(
        final_url="https://otherbrand.com",
        redirect_chain=["https://example.com", "https://otherbrand.com"],
        redirects_to_different_root=True,
        destination_root_domain="otherbrand.com",
    )
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }
    result = classify(r, market, company)
    assert result.classification == "likely for sale"

def test_sparse_coming_soon_is_likely_for_sale():
    r = raw(visible_word_count=12, sparse_content=True)
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": ["coming soon"],
        "active_site_hits": [],
    }
    result = classify(r, market, company)
    assert result.classification == "likely for sale"

def test_active_company_is_not_for_sale():
    r = raw(visible_word_count=500, sparse_content=False)
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": ["pricing", "careers", "login", "customers"],
    }
    result = classify(r, market, company)
    assert result.classification == "not for sale"
