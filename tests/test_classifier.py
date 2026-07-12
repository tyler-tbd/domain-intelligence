from app.classifier import classify
from app.evidence_collector import fetch_redirect_chain
from app.marketplace_detector import detect_marketplace_signals
from app.company_use_detector import detect_company_use
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
    assert result.backend_classification == "for sale"
    assert result.sale_marketplace_hits == ["godaddy"]
    assert result.sale_url_hits == ["/forsale/"]

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
    assert result.backend_classification == "likely for sale"
    assert result.redirects_to_different_root is True
    assert result.destination_root_domain == "otherbrand.com"

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
    assert result.backend_classification == "likely for sale"
    assert result.placeholder_hits == ["coming soon"]

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
    assert result.backend_classification == "not for sale"
    assert result.active_site_hits == ["pricing", "careers", "login", "customers"]

def test_response_contains_all_structured_evidence_arrays():
    r = raw(fetch_error="blocked")
    market = {
        "sale_marketplace_hits": ["sedo"],
        "sale_url_hits": ["make-offer"],
        "explicit_sale_phrase_hits": ["buy this domain"],
        "broker_inquiry_hits": [],
    }
    company = {
        "parking_hits": ["related searches"],
        "placeholder_hits": ["coming soon"],
        "active_site_hits": ["pricing"],
    }

    result = classify(r, market, company)

    assert result.sale_marketplace_hits == ["sedo"]
    assert result.sale_url_hits == ["make-offer"]
    assert result.explicit_sale_phrase_hits == ["buy this domain"]
    assert result.parking_hits == ["related searches"]
    assert result.placeholder_hits == ["coming soon"]
    assert result.active_site_hits == ["pricing"]
    assert result.fetch_error == "blocked"

def test_tentative_broker_lander_is_likely_for_sale():
    r = raw(
        name="Withstand",
        domain="withstand.com",
        page_title="withstand.com",
        visible_text_sample=(
            "GoDaddy withstand.com This domain is registered, but may still "
            "be available. Get this domain. Powered by Afternic."
        ),
        visible_word_count=18,
        sparse_content=True,
    )
    market = {
        "sale_marketplace_hits": ["afternic", "godaddy"],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
        "broker_inquiry_hits": ["may still be available", "get this domain"],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }

    result = classify(r, market, company)

    assert result.backend_classification == "likely for sale"
    assert result.backend_confidence == "high"
    assert result.broker_inquiry_hits == [
        "may still be available",
        "get this domain",
    ]

def test_javascript_lander_redirect_is_followed():
    class Response:
        def __init__(self, status_code, text, headers=None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {}

    class Session:
        def get(self, url, **kwargs):
            if url == "https://withstand.com":
                return Response(
                    200,
                    '<script>window.onload=function(){window.location.href="/lander"}</script>',
                )
            return Response(200, "Get this domain. Powered by Afternic.")

    response, chain, error = fetch_redirect_chain(
        Session(), "https://withstand.com", 1
    )

    assert error == ""
    assert response.status_code == 200
    assert chain == ["https://withstand.com", "https://withstand.com/lander"]

def test_non_http_javascript_redirect_is_ignored():
    class Response:
        status_code = 200
        text = '<script>window.location.href="about:blank"</script> All inquires — domain@track.com'
        headers = {}

    class Session:
        def get(self, url, **kwargs):
            return Response()

    response, chain, error = fetch_redirect_chain(
        Session(), "https://track.com", 1
    )

    assert error == ""
    assert response.status_code == 200
    assert chain == ["https://track.com"]

def test_sparse_same_domain_inquiry_email_is_broker_signal():
    r = raw(
        name="Track",
        domain="track.com",
        page_title="track.com Domain Name",
        meta_description="track.com domain name",
        visible_text_sample="All inquires — domain@track.com",
        visible_word_count=4,
        sparse_content=True,
    )

    market = detect_marketplace_signals(r)
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }
    result = classify(r, market, company)

    assert result.backend_classification == "likely for sale"
    assert "all inquires" in result.broker_inquiry_hits
    assert "domain@track.com" in result.broker_inquiry_hits

def test_godaddy_parking_bundle_is_likely_for_sale():
    r = raw(
        name="Acetrack",
        domain="acetrack.com",
        final_url="https://acetrack.com/lander",
        redirect_chain=["https://acetrack.com", "https://acetrack.com/lander"],
        html_source_sample=(
            '<script>window._trfd.push({ap:"parking"})</script>'
            '<script src="https://img1.wsimg.com/parking-lander/static/js/main.js"></script>'
        ),
        visible_word_count=0,
        sparse_content=True,
    )
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
        "broker_inquiry_hits": [],
    }
    company = detect_company_use(r)

    result = classify(r, market, company)

    assert result.backend_classification == "likely for sale"
    assert "parking-lander" in result.parking_hits

def test_unreachable_domain_is_likely_for_sale():
    r = raw(
        domain="ardent.com",
        dns_resolves=True,
        http_status=None,
        visible_word_count=0,
        fetch_error="Connection timed out",
    )
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
        "broker_inquiry_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }

    result = classify(r, market, company)

    assert result.backend_classification == "likely for sale"
    assert result.backend_confidence == "low"

def test_ten_words_or_fewer_is_likely_unless_directly_for_sale():
    r = raw(visible_word_count=10, sparse_content=True)
    market = {
        "sale_marketplace_hits": [],
        "sale_url_hits": [],
        "explicit_sale_phrase_hits": [],
        "broker_inquiry_hits": [],
    }
    company = {
        "parking_hits": [],
        "placeholder_hits": [],
        "active_site_hits": [],
    }

    result = classify(r, market, company)
    assert result.backend_classification == "likely for sale"

    market["explicit_sale_phrase_hits"] = ["this domain is for sale"]
    result = classify(r, market, company)
    assert result.backend_classification == "for sale"
