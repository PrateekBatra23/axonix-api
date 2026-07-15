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
    scraped_at: datetime
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    jobs: list[JobOut]
    total: int
    has_more: bool