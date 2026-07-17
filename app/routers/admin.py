from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import User, Setting, ScrapeRun, Job, JobFlag, Digest, Story, AuditLog
from app.schemas import UserCreate, UserUpdate, UserOut, SettingOut, SettingUpdate, AdminSummary, SubsystemStatus
from app.auth_admin import require_role, hash_password

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _get_setting_value(db: Session, key: str, default: str = "0") -> str:
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else default


# ── Users (owner only) ──────────────────────────────────────────

@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_role("owner"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_role("owner"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("owner"))])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user


# ── Settings (owner/admin write, all authenticated read) ───────

@router.get("/settings", response_model=list[SettingOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_settings(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Setting)
    if category:
        q = q.filter(Setting.category == category)
    return q.order_by(Setting.category, Setting.key).all()


@router.patch("/settings/{key}", response_model=SettingOut, dependencies=[Depends(require_role("owner", "admin"))])
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    setting.value = payload.value
    setting.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(setting)
    return setting


# ── Dashboard summary (all authenticated read) ──────────────────

@router.get("/summary", response_model=AdminSummary, dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def get_summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    subsystems = []

    # Scraper health
    failure_hours = int(_get_setting_value(db, "scrape.failure_window_hours", "24"))
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

    # Job flags
    flag_threshold = int(_get_setting_value(db, "job.flag_review_threshold", "3"))
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

    # Active jobs volume
    min_jobs = int(_get_setting_value(db, "jobs.minimum_active_count", "10"))
    active_count = db.query(Job).filter(Job.is_active == True).count()
    if active_count >= min_jobs:
        subsystems.append(SubsystemStatus(name="jobs_content", status="green", detail=f"{active_count} active jobs"))
    else:
        subsystems.append(SubsystemStatus(name="jobs_content", status="red", detail=f"Only {active_count} active jobs"))

    # Digest freshness
    digest_hours = int(_get_setting_value(db, "digest.freshness_window_hours", "36"))
    latest_digest = db.query(Digest).order_by(Digest.created_at.desc()).first()
    if latest_digest and (now - latest_digest.created_at) < timedelta(hours=digest_hours):
        subsystems.append(SubsystemStatus(name="news_digest", status="green", detail=f"Last digest: {latest_digest.slug}"))
    else:
        subsystems.append(SubsystemStatus(name="news_digest", status="red", detail="No recent digest"))

    return AdminSummary(subsystems=subsystems, checked_at=now)

@router.get("/scrape-runs", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_scrape_runs(limit: int = 50, db: Session = Depends(get_db)):
    runs = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(limit).all()
    return runs


@router.get("/flags", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_flags(min_flags: int = 1, db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = (
        db.query(JobFlag.job_id, func.count(JobFlag.id).label("flag_count"))
        .filter(JobFlag.reason.is_(None))
        .group_by(JobFlag.job_id)
        .having(func.count(JobFlag.id) >= min_flags)
        .order_by(func.count(JobFlag.id).desc())
        .all()
    )
    return [{"job_id": r.job_id, "flag_count": r.flag_count} for r in results]


@router.get("/content-stats", dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def admin_content_stats(db: Session = Depends(get_db)):
    return {
        "total_digests": db.query(Digest).count(),
        "total_stories": db.query(Story).count(),
        "total_jobs": db.query(Job).count(),
        "active_jobs": db.query(Job).filter(Job.is_active == True).count(),
    }