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
    img_url: str  | None = None
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
    img_url: str | None = None
    theme_bg: str | None = None
    theme_text: str | None = None
    image_url: str | None = None
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
    companies_with_active_jobs: int| None = None
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
    companies_with_active_jobs: int | None = None
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

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    password: str
    role: str  # "owner" | "admin" | "read_only"

class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    category: str
    description: str | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SettingUpdate(BaseModel):
    value: str


class SubsystemStatus(BaseModel):
    name: str
    status: str  # "green" | "red"
    detail: str

class AdminSummary(BaseModel):
    subsystems: list[SubsystemStatus]
    checked_at: datetime

class DigestListResponse(BaseModel):
    digests: list[DigestOut]
    total: int
    has_more: bool

class CompanyCreate(BaseModel):
    name: str
    group_id: int | None = None
    theme_bg: str | None = None
    theme_text: str | None = None
    tracked: bool = True
    exclusive: bool = False
    page_visible: bool = False

class CompanyUpdate(BaseModel):
    name: str | None = None
    group_id: int | None = None
    theme_bg: str | None = None
    theme_text: str | None = None
    tracked: bool | None = None
    exclusive: bool | None = None
    page_visible: bool | None = None

class CompanyOut(BaseModel):
    id: int
    slug: str
    name: str
    group_id: int | None = None
    theme_bg: str | None = None
    theme_text: str | None = None
    tracked: bool
    exclusive: bool
    page_visible: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyPublicOut(BaseModel):
    slug: str
    name: str
    theme_bg: str | None = None
    theme_text: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CompanyBulkCreate(BaseModel):
    names: list[str]

class CompanyBulkResponse(BaseModel):
    created: int
    skipped: int
    errors: list[dict] = []
class ImageCategoryCreate(BaseModel):
    key: str
    label: str

class ImageCategoryOut(BaseModel):
    id: int
    key: str
    label: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ImageCreate(BaseModel):
    url: str
    company_id: int
    image_category_id: int

class ImageOut(BaseModel):
    id: int
    url: str
    company_id: int
    image_category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)