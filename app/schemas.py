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

    model_config = ConfigDict(from_attributes=True)


class StoryCreate(BaseModel):
    digest_id: int
    headline: str
    summary: str
    link: str
    source: str
    published_date: str
    topic_tags: str
    img_url: str

class StoryOut(BaseModel):
    id: int
    slug: str
    digest_id: int
    headline: str
    summary: str
    link: str
    source: str
    published_date: str
    topic_tags: str
    img_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)