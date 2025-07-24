from app.celery_app import celery_app
from app.config.base import get_db
from app.functions.task import audit_website
from app.models.core_model import Website, AuditResult
from app.config.base import SessionLocal
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.audit import AuditRequest, AuditStatus, AuditResultResponse, LighthouseScores
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.post("/audit", response_model=dict)
def start_audit(audit_request: AuditRequest, db: Session = Depends(get_db)):
    """Start a comprehensive audit of a website"""
    try:
        # Start the audit synchronously
        result = audit_website(
            website_url=str(audit_request.website_url),
            website_name=audit_request.website_name,
            include_mobile=audit_request.include_mobile,
            include_desktop=audit_request.include_desktop,
            max_pages=audit_request.max_pages or 100
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return {
            "message": "Audit completed successfully",
            "website_id": result["website_id"],
            "pages_found": result["pages_found"]
        }
        
    except Exception as e:
        logger.error(f"Error starting audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/{website_id}/status", response_model=AuditStatus)
def get_audit_status(website_id: str, db: Session = Depends(get_db)):
    """Get the status of an ongoing audit"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    total_audits = db.query(AuditResult).filter(AuditResult.website_id == website_id).count()
    completed_audits = db.query(AuditResult).filter(
        AuditResult.website_id == website_id,
        AuditResult.status == "completed"
    ).count()
    
    # Determine overall status
    if total_audits == 0:
        status = "pending"
    elif completed_audits == total_audits:
        status = "completed"
    else:
        status = "in_progress"
    
    return AuditStatus(
        id=website.id,
        website_url=website.url,
        status=status,
        total_pages=website.total_pages or 0,
        completed_audits=completed_audits,
        created_at=website.created_at
    )

@router.get("/audit/{website_id}/results", response_model=List[AuditResultResponse])
def get_audit_results(
    website_id: str,
    device_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get audit results for a website"""
    query = db.query(AuditResult).filter(AuditResult.website_id == website_id)
    
    if device_type:
        query = query.filter(AuditResult.device_type == device_type)
    
    results = query.offset((page - 1) * limit).limit(limit).all()
    
    return [
        AuditResultResponse(
            id=result.id,
            page_url=result.page_url,
            device_type=result.device_type,
            audit_date=result.audit_date,
            scores=LighthouseScores(
                performance=result.performance_score,
                accessibility=result.accessibility_score,
                best_practices=result.best_practices_score,
                seo=result.seo_score,
                pwa=result.pwa_score
            ),
            status=result.status,
            error_message=result.error_message
        )
        for result in results
    ]

@router.get("/audit/{audit_id}/full-report")
def get_full_report(audit_id: int, db: Session = Depends(get_db)):
    """Get the complete Lighthouse report for a specific audit"""
    result = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found")
    
    return JSONResponse(content=result.full_report)

@router.get("/websites", response_model=List[dict])
def list_websites(db: Session = Depends(get_db)):
    """List all audited websites"""
    websites = db.query(Website).all()
    return [
        {
            "id": website.id,
            "url": website.url,
            "name": website.name,
            "created_at": website.created_at,
            "last_crawled": website.last_crawled,
            "total_pages": website.total_pages
        }
        for website in websites
    ]

@router.get("/")
def root():
    return {
        "message": "Lighthouse Audit Tool API",
        "version": "1.0.0",
        "endpoints": {
            "POST /audit": "Start website audit",
            "GET /audit/{website_id}/status": "Get audit status",
            "GET /audit/{website_id}/results": "Get audit results",
            "GET /audit/{audit_id}/full-report": "Get full Lighthouse report",
            "GET /websites": "List all websites"
        }
    }