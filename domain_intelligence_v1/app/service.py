from .evidence_collector import collect_evidence
from .marketplace_detector import detect_marketplace_signals
from .company_use_detector import detect_company_use
from .classifier import classify

def investigate_name(value: str):
    raw = collect_evidence(value)
    market = detect_marketplace_signals(raw)
    company = detect_company_use(raw)
    return classify(raw, market, company)
