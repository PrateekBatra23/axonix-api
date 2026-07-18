from fastapi import APIRouter, Depends
from ..database import get_db
from ..schemas import DigestCreate, DigestOut,DigestListResponse
from ..models import Digest
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.auth import require_api_key
from fastapi import APIRouter, Depends, Header, HTTPException
router = APIRouter(
    prefix="/api/v1",
    tags=["digests"]
)

@router.get("/digests", response_model=DigestListResponse)
def get_digests(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(Digest).order_by(Digest.publish_date.desc())
    total = q.count()
    digests = q.offset(offset).limit(limit).all()
    has_more = (offset + len(digests)) < total
    return DigestListResponse(digests=digests, total=total, has_more=has_more)

@router.post("/digests", response_model=DigestOut, status_code=201,dependencies=[Depends(require_api_key)])
def post_digests(payload: DigestCreate, db: Session = Depends(get_db)):
    slug = str(payload.publish_date)
    existing = db.query(Digest).filter(Digest.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Digest for this date already exists")
    
    new_digest = Digest(**payload.model_dump(), slug=slug)
    db.add(new_digest)
    db.commit()
    db.refresh(new_digest)
    return new_digest
@router.get("/digests/{slug}", response_model=DigestOut)
def get_digest_by_slug(slug: str, db: Session = Depends(get_db)):
    digest = db.query(Digest).filter(Digest.slug == slug).first()
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    return digest