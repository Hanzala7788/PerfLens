from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DeviceType(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"

class AuditRequest(BaseModel):
    website_url: HttpUrl
    website_name: Optional[str] = None
    include_mobile: bool = True
    include_desktop: bool = True
    max_pages: Optional[int]

class AuditStatus(BaseModel):
    id: int
    website_url: str
    status: str
    total_pages: int
    completed_audits: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None

class LighthouseScores(BaseModel):
    performance: Optional[float]
    accessibility: Optional[float]
    best_practices: Optional[float]
    seo: Optional[float]
    pwa: Optional[float]

class AuditResultResponse(BaseModel):
    id: int
    page_url: str
    device_type: str
    audit_date: datetime
    scores: LighthouseScores
    status: str
    error_message: Optional[str] = None

class GeminiReportRequest(BaseModel):
    website_url: HttpUrl
    device_type: str = "desktop" # "desktop" or "mobile"
    report_format: str = "markdown" # Could support "html", "pdf" later
    gemini_instructions: Optional[str] = None

class GeminiReportResponse(BaseModel):
    url: str
    device_type: str
    status: str
    message: str
    report_url: Optional[str] = None
    markdown_report: Optional[str] = None 