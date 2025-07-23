from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    DateTime,
    String,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(object):
    is_archived = Column("IsArchived", Boolean, default=False)
    archived_at = Column("ArchivedAt", DateTime(timezone=True), nullable=True)
    created_at = Column("CreatedAt", DateTime(timezone=True), default=datetime.utcnow())
    updated_at = Column("UpdatedAt", DateTime(timezone=True), default=datetime.utcnow())
    archived_by = Column("ArchivedBy", String(100), nullable=True)
    created_by = Column("CreatedBy", String(100), nullable=True)
    updated_by = Column("UpdatedBy", String(100), nullable=True)


class User(Base, BaseModel):
    __tablename__ = "User"

    user_id = Column(
        "UserId", UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    email = Column("Email", String, unique=True, index=True)
    hashed_password = Column("HashedPassword", String)
    is_active = Column("IsActive", Boolean, default=True)

    # Composite Index (email, is_active)
    __table_args__ = (Index("idx_email_active", "Email", "IsActive"),)
