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
    img_url = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    company_slug = Column(String, nullable=True, index=True)
    digest = relationship("Digest", back_populates="stories")
    internal_source = Column(String, nullable=True)
    image_category = Column(String, nullable=True)

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