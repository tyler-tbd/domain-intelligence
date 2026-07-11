import csv
from pathlib import Path

FEEDBACK_PATH = Path("data/domain_feedback_master.csv")

def load_overrides() -> dict[str, str]:
    if not FEEDBACK_PATH.exists():
        return {}

    result = {}
    with FEEDBACK_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            domain = row.get("domain", "").strip().lower()
            classification = row.get("corrected_classification", "").strip().lower()
            if domain and classification:
                result[domain] = classification
    return result
