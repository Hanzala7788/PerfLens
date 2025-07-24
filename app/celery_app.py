# app/celery_app.py

from celery import Celery
import os

celery_app = Celery(
    "lighthouse_auditor",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=["app.functions.task", "app.routers.v1.audit.audit"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.functions.tasks.audit_website": {"queue": "audit"},
        "app.functions.tasks.audit_single_page": {"queue": "page_audit"},
        "app.routers.v1.audit.audit.audit_website": {"queue": "audit"}
    },
    # ADD THIS LINE:
    broker_pool_limit=2, # Limit broker connections for Celery. Adjust as needed (e.g., 1 to 5)
    # This also affects the backend, as it often uses the same connection pool logic.
)