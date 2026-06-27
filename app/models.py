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

    digest = relationship("Digest", back_populates="stories")