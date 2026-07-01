from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import StoryCreate, StoryOut
from app.models import Story,Digest
from sqlalchemy.orm import Session
from slugify import slugify
from app.auth import require_api_key
from fastapi import APIRouter, Depends, Header, HTTPException
router = APIRouter(
    prefix="/api/v1",
    tags=["stories"]
)

@router.get("/stories", response_model=list[StoryOut])
def get_stories(db: Session = Depends(get_db)):
    stories = db.query(Story).order_by(Story.id.desc()).all()
    return stories

@router.post("/stories", response_model=StoryOut, dependencies=[Depends(require_api_key)])
@router.post("/stories", response_model=StoryOut, dependencies=[Depends(require_api_key)])
def post_stories(payload: StoryCreate, db: Session = Depends(get_db)):
    digest = db.query(Digest).filter(Digest.id == payload.digest_id).first()
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    slug = slugify(payload.headline)
    # Handle duplicate slugs
    existing = db.query(Story).filter(Story.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Story with this headline already exists")

    new_story = Story(**payload.model_dump(), slug=slug)
    db.add(new_story)
    db.commit()
    db.refresh(new_story)
    return new_story