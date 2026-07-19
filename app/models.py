from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date, datetime, timezone

class Digest(Base):
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    publish_date = Column(Date, default=date.today)
    overall_summary = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    slug = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    stories = relationship("Story", back_populates="digest")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(Integer, ForeignKey("digests.id"))
    headline = Column(String)
    summary = Column(String)
    link = Column(String)
    source = Column(String)
    published_date = Column(String)
    slug = Column(String, unique=True, index=True)
    topic_tags = Column(String)
    img_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    company_slug = Column(String, nullable=True, index=True)
    digest = relationship("Digest", back_populates="stories")
    internal_source = Column(String, nullable=True)
    image_category = Column(String, nullable=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    company_slug = Column(String, nullable=True, index=True)
    location = Column(String)
    remote = Column(Boolean, default=False)
    employment_type = Column(String)
    experience_level = Column(String, nullable=True, index=True)
    role_category = Column(String, nullable=True, index=True)
    tags = Column(String, nullable=True)
    apply_url = Column(String)
    external_id = Column(String, index=True)
    source = Column(String)
    posted_at = Column(DateTime(timezone=True), nullable=True)  
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    pipeline_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_name = Column(String, index=True)
    trigger_type = Column(String, default="scheduled")
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, default="running", index=True)

    companies_scraped = Column(Integer, default=0)
    companies_with_active_jobs = Column(Integer, default=0)
    sources_failed = Column(String, nullable=True)
    jobs_found = Column(Integer, default=0)
    jobs_created = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)

    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class JobFlag(Base):
    __tablename__ = "job_flags"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    reason = Column(String, nullable=True)  # NULL = generic flag click, populated = reason given
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, index=True)  # "owner" | "admin" | "read_only"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token_hash = Column(String, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    value_type = Column(String, default="string")  # "string" | "int" | "float" | "bool"
    category = Column(String, index=True)  # "threshold" | "pipeline_config" | "general"
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    detail = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)   

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    group_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    theme_bg = Column(String, nullable=True)
    theme_text = Column(String, nullable=True)
    tracked = Column(Boolean, default=True)
    exclusive = Column(Boolean, default=False)
    page_visible = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

class ImageCategory(Base):
    __tablename__ = "image_categories"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    label = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    image_category_id = Column(Integer, ForeignKey("image_categories.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)