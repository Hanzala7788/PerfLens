from uuid import uuid4
from app.utils.crawler import WebsiteCrawler
from app.utils.lighthouse_runner import extract_scores, run_lighthouse_audit
from app.models.core_model import Website, AuditResult
from app.config.base import SessionLocal, get_db
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.audit import AuditRequest, AuditStatus, AuditResultResponse, LighthouseScores
from typing import List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

def audit_website(website_url: str, website_name: str, include_mobile: bool, include_desktop: bool, max_pages: int):
    """
    Main function to audit an entire website.
    It crawls the website, updates the website record, and then
    triggers audits for each discovered page.

    Args:
        website_url (str): The URL of the website to audit.
        website_name (str): The name of the website (defaults to URL if not provided).
        include_mobile (bool): Whether to perform mobile audits.
        include_desktop (bool): Whether to perform desktop audits.
        max_pages (int): The maximum number of pages to crawl.

    Returns:
        dict: A dictionary indicating the status of the overall audit,
              number of pages found, and the website ID.
    """
    db = SessionLocal()  # Initialize database session

    try:
        # Create or retrieve the website record from the database
        website = db.query(Website).filter(Website.url == website_url).first()
        if not website:
            # If website does not exist, create a new record
            website = Website(
                id=str(uuid4()),  # Assign a unique UUID as string
                url=website_url,
                name=website_name or website_url,
                created_at=datetime.utcnow()
            )
            db.add(website)
            db.commit()  # Commit the new website record
            db.refresh(website)  # Refresh to get the latest state, including the ID

        # Initialize and run the website crawler
        crawler = WebsiteCrawler(website_url, max_pages)
        pages = crawler.crawl()  # Synchronous crawl operation

        # Update the website record with crawling results
        website.total_pages = len(pages)
        website.last_crawled = datetime.utcnow()
        db.commit()  # Commit updates to the website record

        # Sequentially audit each page
        for page_url in pages:
            if include_desktop:
                result = audit_single_page(website.id, page_url, "desktop", db)
            if include_mobile:
                audit_single_page(website.id, page_url, "mobile", db)

        return {"status": "success", "pages_found": len(pages), "website_id": website.id}

    except Exception as e:
        # Log any errors that occur during the main audit process
        logger.error(f"Error auditing website {website_url}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure the database session is closed
        db.close()

def audit_single_page(website_id: str, page_url: str, device_type: str, db: Session):
    """
    Function to audit a single page using Lighthouse.
    It creates an audit result record, runs the Lighthouse audit,
    and updates the record with the audit scores and full report.

    Args:
        website_id (str): The ID of the website this page belongs to.
        page_url (str): The URL of the page to audit.
        device_type (str): The device type for the audit ("mobile" or "desktop").
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary indicating the status of the single page audit
              and the audit result ID.
    """
    try:
        # Create a new audit result record with a 'pending' status
        audit_result = AuditResult(
            website_id=website_id,
            page_url=page_url,
            device_type=device_type,
            audit_date=datetime.utcnow(),
            status="pending"
        )
        db.add(audit_result)
        db.commit()  # Commit the new audit result record
        db.refresh(audit_result)  # Refresh to get the latest state, including the ID

        report = run_lighthouse_audit(page_url, device_type)
        scores = extract_scores(report)
        print("Lighthouse Scores:", scores)

        if report:
            # If a report is successfully generated, extract scores
            scores = extract_scores(report)

            # Update the audit result record with the scores and full report
            audit_result.performance_score = scores.get('performance')
            audit_result.accessibility_score = scores.get('accessibility')
            audit_result.best_practices_score = scores.get('best_practices')
            audit_result.seo_score = scores.get('seo')
            audit_result.pwa_score = scores.get('pwa')
            audit_result.full_report = report
            audit_result.status = "completed"  # Set status to completed
        else:
            # If no report, set status to failed
            audit_result.status = "failed"
            audit_result.error_message = "Lighthouse audit failed or returned no report"

        db.commit()  # Commit updates to the audit result record

        return {"status": audit_result.status, "audit_id": audit_result.id}

    except Exception as e:
        # Log any errors that occur during the single page audit
        logger.error(f"Error auditing page {page_url}: {e}")
        if audit_result:
            # If an audit_result record was created, update its status to failed
            audit_result.status = "failed"
            audit_result.error_message = str(e)
            db.commit()  # Commit the failed status
        return {"status": "error", "message": str(e)}