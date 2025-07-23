from celery import Celery
import os

# Celery configuration
celery_app = Celery(
    "lighthouse_auditor",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.audit_website": {"queue": "audit"},
        "tasks.audit_single_page": {"queue": "page_audit"}
    }
)