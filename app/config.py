import os

API_KEY = os.environ.get("DOMAIN_API_KEY", "")
MAX_NAMES = 100
MAX_REDIRECTS = 10
MAX_TEXT_CHARS = 7000
DEFAULT_TIMEOUT = 8.0
DEFAULT_WORKERS = 10
USER_AGENT = (
    "Mozilla/5.0 (compatible; DomainIntelligence/1.0; "
    "+https://example.com/domain-intelligence)"
)
