from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Boolean,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from app.models.user import BaseModel

Base = declarative_base()


class Website(Base, BaseModel):
    __tablename__ = "websites"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_crawled = Column(DateTime)
    total_pages = Column(Integer, default=0)

class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, index=True)
    page_url = Column(String, index=True)
    device_type = Column(String)  # 'mobile' or 'desktop'
    audit_date = Column(DateTime, default=datetime.utcnow)
    
    # Lighthouse scores
    performance_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)
    best_practices_score = Column(Float, nullable=True)
    seo_score = Column(Float, nullable=True)
    pwa_score = Column(Float, nullable=True)
    
    # Full Lighthouse report JSON
    full_report = Column(JSON, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    