from typing import List, Optional
from pydantic import BaseModel, Field

class InvestigateRequest(BaseModel):
    names: List[str] = Field(..., min_length=1, max_length=100)

class RawEvidence(BaseModel):
    name: str
    domain: str
    dns_resolves: bool
    http_status: Optional[int]
    starting_url: str
    final_url: str
    redirect_chain: List[str]
    redirects_to_different_root: bool
    destination_root_domain: str
    page_title: str
    meta_description: str
    visible_text_sample: str
    visible_word_count: int
    sparse_content: bool
    fetch_error: str = ""

class SignalBundle(BaseModel):
    sale_marketplace_hits: List[str] = Field(default_factory=list)
    sale_url_hits: List[str] = Field(default_factory=list)
    explicit_sale_phrase_hits: List[str] = Field(default_factory=list)
    broker_inquiry_hits: List[str] = Field(default_factory=list)
    parking_hits: List[str] = Field(default_factory=list)
    placeholder_hits: List[str] = Field(default_factory=list)
    active_site_hits: List[str] = Field(default_factory=list)

class InvestigationResult(BaseModel):
    name: str
    domain: str
    backend_classification: str
    backend_confidence: str
    backend_evidence: List[str] = Field(default_factory=list)
    dns_resolves: bool
    http_status: Optional[int]
    starting_url: str
    final_url: str
    redirect_chain: List[str]
    redirects_to_different_root: bool
    destination_root_domain: str
    sale_marketplace_hits: List[str] = Field(default_factory=list)
    sale_url_hits: List[str] = Field(default_factory=list)
    explicit_sale_phrase_hits: List[str] = Field(default_factory=list)
    broker_inquiry_hits: List[str] = Field(default_factory=list)
    parking_hits: List[str] = Field(default_factory=list)
    placeholder_hits: List[str] = Field(default_factory=list)
    active_site_hits: List[str] = Field(default_factory=list)
    page_title: str
    meta_description: str
    visible_word_count: int
    sparse_content: bool
    fetch_error: str = ""
