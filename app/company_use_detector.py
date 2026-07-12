from .models import RawEvidence

PARKING_PHRASES = [
    "related searches", "sponsored listings", "parkingcrew",
    "bodis", "domain parking", "parked free", "parklogic",
    "parking-lander", 'ap:"parking"', "wsimg.com/parking-lander",
]

PLACEHOLDER_PHRASES = [
    "coming soon", "under construction", "new website coming",
    "site coming soon", "future home of", "welcome to nginx",
    "apache2 default page", "website coming soon",
]

ACTIVE_SITE_PHRASES = [
    "privacy policy", "terms of service", "careers", "customers",
    "case studies", "documentation", "api", "login", "sign in",
    "book a demo", "pricing", "download", "support", "help center",
    "about us", "team", "security", "features", "solutions",
    "products", "enterprise",
]

def find_hits(text: str, patterns: list[str]) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in patterns if pattern in lowered]

def detect_company_use(raw: RawEvidence) -> dict:
    combined = " ".join(
        [
            raw.page_title,
            raw.meta_description,
            raw.visible_text_sample,
            raw.html_source_sample,
        ]
    )

    return {
        "parking_hits": find_hits(combined, PARKING_PHRASES),
        "placeholder_hits": find_hits(combined, PLACEHOLDER_PHRASES),
        "active_site_hits": find_hits(combined, ACTIVE_SITE_PHRASES),
    }
