from app.config.celery_app import celery_app
from app.config.base import get_db
from app.utils.crawler import WebsiteCrawler
from app.utils.lighthouse_runner import LighthouseRunner
from app.models.core_model import SessionLocal, Website, AuditResult
from datetime import datetime
import logging
from fastapi import APIRouter, FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models.core_model import AuditRequest, AuditStatus, AuditResultResponse, LighthouseScores
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


@celery_app.task
def audit_website(website_url: str, website_name: str, include_mobile: bool, include_desktop: bool, max_pages: int):
    """Main task to audit entire website"""
    db = SessionLocal()
    
    try:
        # Create or get website record
        website = db.query(Website).filter(Website.url == website_url).first()
        if not website:
            website = Website(
                url=website_url,
                name=website_name or website_url,
                created_at=datetime.utcnow()
            )
            db.add(website)
            db.commit()
            db.refresh(website)
        
        # Crawl website to get all pages
        crawler = WebsiteCrawler(website_url, max_pages)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pages = loop.run_until_complete(crawler.crawl())
        loop.close()
        
        # Update website with page count
        website.total_pages = len(pages)
        website.last_crawled = datetime.utcnow()
        db.commit()
        
        # Queue individual page audits
        for page_url in pages:
            if include_desktop:
                audit_single_page.delay(website.id, page_url, "desktop")
            if include_mobile:
                audit_single_page.delay(website.id, page_url, "mobile")
                
        return {"status": "success", "pages_found": len(pages), "website_id": website.id}
        
    except Exception as e:
        logger.error(f"Error auditing website {website_url}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def audit_single_page(website_id: int, page_url: str, device_type: str):
    """Task to audit a single page"""
    db = SessionLocal()
    
    try:
        # Create audit result record
        audit_result = AuditResult(
            website_id=website_id,
            page_url=page_url,
            device_type=device_type,
            audit_date=datetime.utcnow(),
            status="pending"
        )
        db.add(audit_result)
        db.commit()
        db.refresh(audit_result)
        
        # Run Lighthouse audit
        runner = LighthouseRunner()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        report = loop.run_until_complete(runner.run_audit(page_url, device_type))
        loop.close()
        
        if report:
            # Extract scores
            scores = runner.extract_scores(report)
            
            # Update audit result
            audit_result.performance_score = scores.get('performance')
            audit_result.accessibility_score = scores.get('accessibility')
            audit_result.best_practices_score = scores.get('best_practices')
            audit_result.seo_score = scores.get('seo')
            audit_result.pwa_score = scores.get('pwa')
            audit_result.full_report = report
            audit_result.status = "completed"
        else:
            audit_result.status = "failed"
            audit_result.error_message = "Lighthouse audit failed"
        
        db.commit()
        
        return {"status": audit_result.status, "audit_id": audit_result.id}
        
    except Exception as e:
        logger.error(f"Error auditing page {page_url}: {e}")
        if 'audit_result' in locals():
            audit_result.status = "failed"
            audit_result.error_message = str(e)
            db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()



# app = FastAPI(
#     title="Lighthouse Audit Tool",
#     description="Comprehensive website auditing tool using Lighthouse",
#     version="1.0.0"
# )

@router.post("/audit", response_model=dict)
async def start_audit(audit_request: AuditRequest, db: Session = Depends(get_db)):
    """Start a comprehensive audit of a website"""
    try:
        # Start the audit task
        task = audit_website.delay(
            website_url=str(audit_request.website_url),
            website_name=audit_request.website_name,
            include_mobile=audit_request.include_mobile,
            include_desktop=audit_request.include_desktop,
            max_pages=audit_request.max_pages or 100
        )
        
        return {
            "message": "Audit started successfully",
            "task_id": task.id,
            "website_url": str(audit_request.website_url)
        }
        
    except Exception as e:
        logger.error(f"Error starting audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/{website_id}/status", response_model=AuditStatus)
async def get_audit_status(website_id: int, db: Session = Depends(get_db)):
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
async def get_audit_results(
    website_id: int,
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
async def get_full_report(audit_id: int, db: Session = Depends(get_db)):
    """Get the complete Lighthouse report for a specific audit"""
    result = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found")
    
    return JSONResponse(content=result.full_report)

@router.get("/websites", response_model=List[dict])
async def list_websites(db: Session = Depends(get_db)):
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
async def root():
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