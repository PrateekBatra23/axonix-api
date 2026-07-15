from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import StoryCreate, StoryOut
from app.models import Story,Digest
from sqlalchemy.orm import Session
from slugify import slugify
from app.auth import require_api_key
from fastapi import APIRouter, Depends, Header, HTTPException
from app.utils.company import get_company_slug
router = APIRouter(
    prefix="/api/v1",
    tags=["stories"]
)

@router.get("/stories", response_model=list[StoryOut])
def get_stories(
    digest_id: int | None = None,
    tag: str | None = None,
    company: str | None = None,
    db: Session = Depends(get_db)
):
    q = db.query(Story)
    if digest_id:
        q = q.filter(Story.digest_id == digest_id)
    if tag:
        # Match tag anchored to comma boundaries
        q = q.filter(
            (Story.topic_tags == tag) |
            (Story.topic_tags.like(f"{tag},%")) |
            (Story.topic_tags.like(f"%,{tag}")) |
            (Story.topic_tags.like(f"%,{tag},%"))
        )
    if company:
        q = q.filter(Story.company_slug == company)
    return q.order_by(Story.id.desc()).all()


@router.post("/stories", response_model=StoryOut,status_code=201, dependencies=[Depends(require_api_key)])
def post_stories(payload: StoryCreate, db: Session = Depends(get_db)):
    digest = db.query(Digest).filter(Digest.id == payload.digest_id).first()
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")

    slug = slugify(payload.headline)
    existing = db.query(Story).filter(Story.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Story with this headline already exists")

    company_slug = get_company_slug(payload.source)
    new_story = Story(**payload.model_dump(), slug=slug, company_slug=company_slug)
    db.add(new_story)
    db.commit()
    db.refresh(new_story)
    return new_story

@router.get("/stories/{slug}", response_model=StoryOut)
def get_story_by_slug(slug: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.slug == slug).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story.digest_slug = story.digest.slug
    story.digest_publish_date = story.digest.publish_date
    return story