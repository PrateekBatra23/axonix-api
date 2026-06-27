from fastapi import APIRouter, Depends
from ..database import get_db
from ..schemas import DigestCreate, DigestOut
from ..models import Digest
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/v1",
    tags=["digests"]
)

@router.get("/digests", response_model=list[DigestOut])
def get_digests(db: Session = Depends(get_db)):
    alldigest = db.query(Digest).order_by(Digest.publish_date.desc()).all()
    return alldigest

@router.post("/digests", response_model=DigestOut)
def post_digests(payload: DigestCreate, db: Session = Depends(get_db)):
    slug = str(payload.publish_date)
    new_digest = Digest(**payload.model_dump(), slug=slug)
    db.add(new_digest)
    db.commit()
    db.refresh(new_digest)
    return new_digest