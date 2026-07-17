from pydantic import BaseModel, ConfigDict
from datetime import date, datetime

class DigestCreate(BaseModel):
    publish_date: date
    overall_summary: str

class DigestOut(BaseModel):
    id: int
    slug: str
    publish_date: date
    overall_summary: str
    created_at: datetime
    story_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class StoryCreate(BaseModel):
    digest_id: int
    headline: str
    summary: str
    link: str
    source: str
    internal_source: str | None = None  # optional
    published_date: str
    topic_tags: str
    img_url: str
    image_category: str | None = None 


class StoryOut(BaseModel):
    id: int
    slug: str
    digest_id: int
    digest_slug: str | None = None
    digest_publish_date: date | None = None
    headline: str
    summary: str
    link: str
    source: str
    internal_source: str | None = None
    company_slug: str | None = None
    image_category: str | None = None
    published_date: str
    topic_tags: str
    img_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    remote: bool = False
    employment_type: str
    experience_level: str | None = None
    role_category: str | None = None
    tags: str | None = None
    apply_url: str
    external_id: str
    source: str
    pipeline_run_id: int | None = None
    posted_at: datetime| None = None


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    company_slug: str | None = None
    location: str
    remote: bool
    employment_type: str
    experience_level: str | None = None
    role_category: str | None = None
    tags: str | None = None
    apply_url: str
    external_id: str
    source: str
    posted_at: datetime| None = None
    pipeline_run_id: int | None = None   # new
    scraped_at: datetime
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LatestRunOut(BaseModel):
    pipeline_name: str
    run_id: int
    started_at: datetime

class JobListResponse(BaseModel):
    jobs: list[JobOut]
    total: int
    has_more: bool
    last_scrapes: list[LatestRunOut] = []

class ScrapeRunStart(BaseModel):
    pipeline_name: str
    trigger_type: str = "scheduled"
    started_at: datetime

class ScrapeRunFinish(BaseModel):
    finished_at: datetime
    status: str  # "success" | "failed"
    companies_scraped: int = 0
    sources_failed: str | None = None
    jobs_found: int = 0
    jobs_created: int = 0
    jobs_failed: int = 0
    error_message: str | None = None

class ScrapeRunOut(BaseModel):
    id: int
    pipeline_name: str
    trigger_type: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: int | None = None
    status: str
    companies_scraped: int
    companies_with_active_jobs: int = 0
    sources_failed: str | None = None
    jobs_found: int
    jobs_created: int
    jobs_failed: int
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlagReasonCreate(BaseModel):
    reason: str

class JobFlagsOut(BaseModel):
    job_id: int
    total_flags: int
    reasons: dict[str, int]

class JobBatchResponse(BaseModel):
    received: int
    created: int
    failed: int
    errors: list[dict] = []