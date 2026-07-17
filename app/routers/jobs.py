from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from slugify import slugify

from app.database import get_db
from app.models import Job, ScrapeRun, JobFlag
from app.schemas import (
    JobCreate, JobOut, JobListResponse,
    ScrapeRunStart, ScrapeRunFinish, ScrapeRunOut, LatestRunOut,
    FlagReasonCreate, JobFlagsOut,JobBatchResponse
)
from app.auth import require_api_key

router = APIRouter(
    prefix="/api/v1",
    tags=["jobs"]
)

def _get_latest_runs_per_pipeline(db: Session) -> list[LatestRunOut]:
    subq = (
        db.query(
            ScrapeRun.pipeline_name,
            func.max(ScrapeRun.started_at).label("max_started_at")
        )
        .filter(ScrapeRun.status == "success")
        .group_by(ScrapeRun.pipeline_name)
        .subquery()
    )

    results = (
        db.query(ScrapeRun.pipeline_name, ScrapeRun.id, ScrapeRun.started_at)
        .join(
            subq,
            (ScrapeRun.pipeline_name == subq.c.pipeline_name)
            & (ScrapeRun.started_at == subq.c.max_started_at)
        )
        .all()
    )

    return [
        LatestRunOut(pipeline_name=r.pipeline_name, run_id=r.id, started_at=r.started_at)
        for r in results
    ]

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
        (
            (Job.posted_at >= thirty_days_ago) |
            ((Job.posted_at.is_(None)) & (Job.scraped_at >= thirty_days_ago))
        ),
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
    jobs = (
        q.order_by(func.coalesce(Job.posted_at, Job.scraped_at).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    has_more = (offset + len(jobs)) < total

    last_scrapes = _get_latest_runs_per_pipeline(db)

    return JobListResponse(
        jobs=jobs,
        total=total,
        has_more=has_more,
        last_scrapes=last_scrapes,
    )



@router.post("/jobs", response_model=JobOut,status_code=201, dependencies=[Depends(require_api_key)])
def post_job(payload: JobCreate, db: Session = Depends(get_db)):
    if payload.posted_at is not None:
        existing = db.query(Job).filter(
            Job.external_id == payload.external_id,
            Job.source == payload.source,
            Job.posted_at == payload.posted_at,
        ).first()
    else:
        existing = db.query(Job).filter(
            Job.external_id == payload.external_id,
            Job.source == payload.source,
            Job.posted_at.is_(None),
        ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Job already exists")

    company_slug = slugify(payload.company)
    new_job = Job(**payload.model_dump(), company_slug=company_slug)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.get("/jobs/companies")
def get_job_companies(all: bool = False, db: Session = Depends(get_db)):
    query = db.query(
        Job.company_slug,
        Job.company,
        func.count(Job.id).label("job_count")
    ).filter(Job.company_slug.isnot(None))

    if not all:
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.filter(
            Job.is_active == True,
            (
                (Job.posted_at >= thirty_days_ago) |
                ((Job.posted_at.is_(None)) & (Job.scraped_at >= thirty_days_ago))
            ),
        )

    results = (
        query.group_by(Job.company_slug, Job.company)
        .order_by(func.count(Job.id).desc())
        .all()
    )

    return [
        {"company_slug": r.company_slug, "company": r.company, "job_count": r.job_count}
        for r in results
    ]
@router.patch("/jobs/{job_id}", response_model=JobOut, dependencies=[Depends(require_api_key)])
def patch_job(job_id: int, db: Session = Depends(get_db)):
    # placeholder — logic to be added later
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/companies")
def get_job_companies(all: bool = False, db: Session = Depends(get_db)):
    query = db.query(
        Job.company_slug,
        Job.company,
        func.count(Job.id).label("job_count")
    ).filter(Job.company_slug.isnot(None))

    if not all:
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.filter(
            Job.is_active == True,
            (
                (Job.posted_at >= thirty_days_ago) |
                ((Job.posted_at.is_(None)) & (Job.scraped_at >= thirty_days_ago))
            ),
        )

    results = (
        query.group_by(Job.company_slug, Job.company)
        .order_by(func.count(Job.id).desc())
        .all()
    )

    return [
        {"company_slug": r.company_slug, "company": r.company, "job_count": r.job_count}
        for r in results
    ]

@router.get("/jobs/scrape-runs", response_model=list[ScrapeRunOut], dependencies=[Depends(require_api_key)])
def list_scrape_runs(pipeline_name: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(ScrapeRun)
    if pipeline_name:
        q = q.filter(ScrapeRun.pipeline_name == pipeline_name)
    return q.order_by(ScrapeRun.started_at.desc()).limit(limit).all()

@router.post("/jobs/scrape-runs", response_model=ScrapeRunOut, status_code=201, dependencies=[Depends(require_api_key)])
def start_scrape_run(payload: ScrapeRunStart, db: Session = Depends(get_db)):
    run = ScrapeRun(
        pipeline_name=payload.pipeline_name,
        trigger_type=payload.trigger_type,
        started_at=payload.started_at,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.patch("/jobs/scrape-runs/{run_id}", response_model=ScrapeRunOut, dependencies=[Depends(require_api_key)])
def finish_scrape_run(run_id: int, payload: ScrapeRunFinish, db: Session = Depends(get_db)):
    run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    run.finished_at = payload.finished_at
    run.status = payload.status
    run.companies_scraped = payload.companies_scraped
    run.companies_with_active_jobs = payload.companies_with_active_jobs
    run.sources_failed = payload.sources_failed
    run.jobs_found = payload.jobs_found
    run.jobs_created = payload.jobs_created
    run.jobs_failed = payload.jobs_failed
    run.error_message = payload.error_message

    if run.started_at and run.finished_at:
        run.duration_seconds = int((run.finished_at - run.started_at).total_seconds())

    db.commit()
    db.refresh(run)
    return run




@router.get("/jobs/scrape-runs/latest", response_model=list[LatestRunOut])
def get_latest_runs_per_pipeline(db: Session = Depends(get_db)):
    return _get_latest_runs_per_pipeline(db)


@router.post("/jobs/{job_id}/flag", status_code=201)
def flag_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    flag = JobFlag(job_id=job_id, reason=None)
    db.add(flag)
    db.commit()
    return {"status": "flagged"}


@router.post("/jobs/{job_id}/flag-reason", status_code=201)
def flag_job_reason(job_id: int, payload: FlagReasonCreate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    flag = JobFlag(job_id=job_id, reason=payload.reason)
    db.add(flag)
    db.commit()
    return {"status": "reason recorded"}


@router.get("/jobs/{job_id}/flags", response_model=JobFlagsOut, dependencies=[Depends(require_api_key)])
def get_job_flags(job_id: int, db: Session = Depends(get_db)):
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

    return JobFlagsOut(job_id=job_id, total_flags=total_flags, reasons=reasons)

@router.post("/jobs/batch", response_model=JobBatchResponse, status_code=201, dependencies=[Depends(require_api_key)])
def create_jobs_batch(payload: list[JobCreate], db: Session = Depends(get_db)):
    received = len(payload)
    created = 0
    failed = 0
    errors = []
    batch_commit_size = 50

    for job_data in payload:
        try:
            if job_data.posted_at is not None:
                existing = db.query(Job).filter(
                    Job.external_id == job_data.external_id,
                    Job.source == job_data.source,
                    Job.posted_at == job_data.posted_at,
                ).first()
            else:
                existing = db.query(Job).filter(
                    Job.external_id == job_data.external_id,
                    Job.source == job_data.source,
                    Job.posted_at.is_(None),
                ).first()

            if existing:
                continue  # duplicate — not an error, just skipped

            company_slug = slugify(job_data.company)
            new_job = Job(**job_data.model_dump(), company_slug=company_slug)
            db.add(new_job)
            created += 1

            if created % batch_commit_size == 0:
                db.commit()

        except Exception as e:
            failed += 1
            errors.append({"external_id": job_data.external_id, "error": str(e)})
            db.rollback()

    db.commit()

    return JobBatchResponse(received=received, created=created, failed=failed, errors=errors)