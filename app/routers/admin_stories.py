from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Story, Image
from app.schemas import StoryAdminUpdate, StoryOut, StoryStubOut
from app.auth_admin import require_role
from app.routers.stories import _attach_theme_and_image

router = APIRouter(prefix="/api/v1/admin", tags=["admin-stories"])


@router.get("/images/{image_id}/stories", response_model=list[StoryStubOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def get_image_stories(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    stories = db.query(Story).filter(Story.image_id == image_id).all()
    return stories


@router.patch("/stories/{story_id}", response_model=StoryOut, dependencies=[Depends(require_role("owner", "admin"))])
def admin_update_story(story_id: int, payload: StoryAdminUpdate, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "image_id" in update_data and update_data["image_id"] is not None:
        image = db.query(Image).filter(Image.id == update_data["image_id"]).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

    for field, value in update_data.items():
        setattr(story, field, value)

    db.commit()
    db.refresh(story)

    if story.digest:
        story.digest_slug = story.digest.slug
        story.digest_publish_date = story.digest.publish_date

    _attach_theme_and_image(db, story)
    return story