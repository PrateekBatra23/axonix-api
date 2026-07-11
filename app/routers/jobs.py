from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.schemas import JobCreate, JobOut, JobListResponse
from app.models import Job
from app.auth import require_api_key
from slugify import slugify

router = APIRouter(
    prefix="/api/v1",
    tags=["jobs"]
)


@router.get("/jobs", response_model=JobListResponse)
def get_jobs(
    company: str | None = None,
    role_category: str | None = None,
    experience_level: str | None = None,
    employment_type: str | None = None,
    remote: bool | None = None,
    tag: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    q = db.query(Job).filter(
        Job.is_active == True,
        Job.posted_at >= thirty_days_ago,
    )

    if company:
        q = q.filter(Job.company_slug == company)
    if role_category:
        q = q.filter(Job.role_category == role_category)
    if experience_level:
        q = q.filter(Job.experience_level == experience_level)
    if employment_type:
        q = q.filter(Job.employment_type == employment_type)
    if remote is not None:
        q = q.filter(Job.remote == remote)
    if tag:
        q = q.filter(
            (Job.tags == tag)
            | (Job.tags.like(f"{tag},%"))
            | (Job.tags.like(f"%,{tag}"))
            | (Job.tags.like(f"%,{tag},%"))
        )

    total = q.count()
    jobs = q.order_by(Job.posted_at.desc()).offset(offset).limit(limit).all()
    has_more = (offset + len(jobs)) < total

    return JobListResponse(jobs=jobs, total=total, has_more=has_more)


@router.post("/jobs", response_model=JobOut, dependencies=[Depends(require_api_key)])
def post_job(payload: JobCreate, db: Session = Depends(get_db)):
    existing = db.query(Job).filter(
        Job.external_id == payload.external_id,
        Job.source == payload.source,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Job already exists")

    company_slug = slugify(payload.company)
    new_job = Job(**payload.model_dump(), company_slug=company_slug)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.patch("/jobs/{job_id}", response_model=JobOut, dependencies=[Depends(require_api_key)])
def patch_job(job_id: int, db: Session = Depends(get_db)):
    # placeholder — logic to be added later
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job