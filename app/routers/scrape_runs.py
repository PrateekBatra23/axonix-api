from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ScrapeRun
from app.schemas import ScrapeRunStart, ScrapeRunFinish, ScrapeRunOut, LatestRunOut
from app.auth import require_api_key
from app.auth_admin import require_role

router = APIRouter(prefix="/api/v1", tags=["scrape-runs"])


def get_latest_runs_per_pipeline(db: Session) -> list[LatestRunOut]:
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


# ── Pipeline writes (x-api-key) ───────────────────────────

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


# ── Pipeline-key-gated read (unchanged from current behavior, not touched this pass) ──

@router.get("/jobs/scrape-runs", response_model=list[ScrapeRunOut], dependencies=[Depends(require_api_key)])
def list_scrape_runs(pipeline_name: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(ScrapeRun)
    if pipeline_name:
        q = q.filter(ScrapeRun.pipeline_name == pipeline_name)
    return q.order_by(ScrapeRun.started_at.desc()).limit(limit).all()


# ── Public read (no auth) ─────────────────────────────────

@router.get("/jobs/scrape-runs/latest", response_model=list[LatestRunOut])
def latest_runs_per_pipeline(db: Session = Depends(get_db)):
    return get_latest_runs_per_pipeline(db)


# ── Admin dashboard read (JWT/role) ───────────────────────

@router.get("/admin/scrape-runs", response_model=list[ScrapeRunOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_scrape_runs_admin(pipeline_name: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(ScrapeRun)
    if pipeline_name:
        q = q.filter(ScrapeRun.pipeline_name == pipeline_name)
    return q.order_by(ScrapeRun.started_at.desc()).limit(limit).all()