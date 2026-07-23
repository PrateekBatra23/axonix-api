from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from slugify import slugify

from app.database import get_db
from app.models import Job
from app.schemas import JobAdminUpdate, JobOut
from app.auth_admin import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin-jobs"])


@router.patch("/jobs/{job_id}", response_model=JobOut, dependencies=[Depends(require_role("owner", "admin"))])
def admin_update_job(job_id: int, payload: JobAdminUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "company" in update_data:
        job.company_slug = slugify(update_data["company"])

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job