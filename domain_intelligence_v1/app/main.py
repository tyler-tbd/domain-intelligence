from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

from .config import API_KEY, DEFAULT_WORKERS
from .models import InvestigateRequest, InvestigationResult
from .service import investigate_name

app = FastAPI(
    title="Domain Intelligence API",
    version="1.0.0",
)

def require_api_key(x_api_key: Optional[str]) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server API key is not configured.",
        )
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/investigate", response_model=list[InvestigationResult])
def investigate(
    request: InvestigateRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    require_api_key(x_api_key)

    results = [None] * len(request.names)
    workers = min(DEFAULT_WORKERS, len(request.names))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(investigate_name, value): index
            for index, value in enumerate(request.names)
        }

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                name = request.names[index]
                results[index] = InvestigationResult(
                    name=name,
                    domain="",
                    classification="check manually",
                    confidence="low",
                    evidence=[f"Investigation failed: {exc}"],
                    dns_resolves=False,
                    http_status=None,
                    final_url="",
                    redirect_chain=[],
                    page_title="",
                    meta_description="",
                    visible_word_count=0,
                    sparse_content=True,
                )

    return [result for result in results if result is not None]
