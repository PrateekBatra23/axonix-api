from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import ScrapeRun, Job, JobFlag, Digest, Story
from app.schemas import AdminSummary, SubsystemStatus
from app.auth_admin import require_role
from app.routers.settings import get_setting_value
from app.models import NewsRun
router = APIRouter(prefix="/api/v1/admin", tags=["dashboard"])


@router.get("/summary", response_model=AdminSummary, dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def get_summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    subsystems = []

    failure_hours = int(get_setting_value(db, "scrape.failure_window_hours", "24"))
    latest_run = (
        db.query(ScrapeRun)
        .filter(ScrapeRun.status == "success")
        .order_by(ScrapeRun.started_at.desc())
        .first()
    )
    if latest_run and (now - latest_run.started_at) < timedelta(hours=failure_hours):
        subsystems.append(SubsystemStatus(name="scraper", status="green", detail=f"Last successful run: {latest_run.started_at.isoformat()}"))
    else:
        subsystems.append(SubsystemStatus(name="scraper", status="red", detail="No successful scrape within threshold window"))

    flag_threshold = int(get_setting_value(db, "job.flag_review_threshold", "3"))
    flagged_job = (
        db.query(JobFlag.job_id, func.count(JobFlag.id).label("cnt"))
        .filter(JobFlag.reason.is_(None))
        .group_by(JobFlag.job_id)
        .having(func.count(JobFlag.id) >= flag_threshold)
        .first()
    )
    if flagged_job:
        subsystems.append(SubsystemStatus(name="flags", status="red", detail=f"Job {flagged_job.job_id} has {flagged_job.cnt} flags"))
    else:
        subsystems.append(SubsystemStatus(name="flags", status="green", detail="No jobs above flag threshold"))

    min_jobs = int(get_setting_value(db, "jobs.minimum_active_count", "10"))
    active_count = db.query(Job).filter(Job.is_active == True).count()
    if active_count >= min_jobs:
        subsystems.append(SubsystemStatus(name="jobs_content", status="green", detail=f"{active_count} active jobs"))
    else:
        subsystems.append(SubsystemStatus(name="jobs_content", status="red", detail=f"Only {active_count} active jobs"))

    digest_hours = int(get_setting_value(db, "digest.freshness_window_hours", "36"))
    latest_digest = db.query(Digest).order_by(Digest.created_at.desc()).first()
    if latest_digest and (now - latest_digest.created_at) < timedelta(hours=digest_hours):
        subsystems.append(SubsystemStatus(name="news_digest", status="green", detail=f"Last digest: {latest_digest.slug}"))
    else:
        subsystems.append(SubsystemStatus(name="news_digest", status="red", detail="No recent digest"))

    news_run_hours = int(get_setting_value(db, "news.failure_window_hours", "30"))
    latest_news_run = (
        db.query(NewsRun)
        .filter(NewsRun.status == "success")
        .order_by(NewsRun.started_at.desc())
        .first()
    )
    if latest_news_run and (now - latest_news_run.started_at) < timedelta(hours=news_run_hours):
        subsystems.append(SubsystemStatus(name="news_pipeline", status="green", detail=f"Last successful run: {latest_news_run.started_at.isoformat()}"))
    else:
        subsystems.append(SubsystemStatus(name="news_pipeline", status="red", detail="No successful news pipeline run within threshold window"))

    return AdminSummary(subsystems=subsystems, checked_at=now)


@router.get("/flags", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_flags(min_flags: int = 1, db: Session = Depends(get_db)):
    results = (
        db.query(JobFlag.job_id, func.count(JobFlag.id).label("flag_count"))
        .filter(JobFlag.reason.is_(None))
        .group_by(JobFlag.job_id)
        .having(func.count(JobFlag.id) >= min_flags)
        .order_by(func.count(JobFlag.id).desc())
        .all()
    )
    return [{"job_id": r.job_id, "flag_count": r.flag_count} for r in results]


@router.get("/jobs/{job_id}/flags", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_job_flags(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    total_flags = db.query(JobFlag).filter(
        JobFlag.job_id == job_id,
        JobFlag.reason.is_(None),
    ).count()

    reason_rows = (
        db.query(JobFlag.reason, func.count(JobFlag.id))
        .filter(JobFlag.job_id == job_id, JobFlag.reason.isnot(None))
        .group_by(JobFlag.reason)
        .all()
    )
    reasons = {reason: count for reason, count in reason_rows}

    return {"job_id": job_id, "total_flags": total_flags, "reasons": reasons}


@router.get("/content-stats", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_content_stats(db: Session = Depends(get_db)):
    return {
        "total_digests": db.query(Digest).count(),
        "total_stories": db.query(Story).count(),
        "total_jobs": db.query(Job).count(),
        "active_jobs": db.query(Job).filter(Job.is_active == True).count(),
    }