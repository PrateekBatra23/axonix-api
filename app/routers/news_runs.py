from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from slugify import slugify

from app.database import get_db
from app.models import NewsRun, Digest, Story, FallbackLog
from app.schemas import (
    NewsRunStart, NewsRunFinishFailure, NewsRunOut,
    StoryBulkCreate, StoryBulkResponse,
)
from app.auth import require_scope
from app.auth_admin import require_role
from app.utils.company import get_company_slug
from app.utils.image_resolution import resolve_story_image

router = APIRouter(prefix="/api/v1", tags=["news-runs"])


# ── Pipeline: start a run ─────────────────────────────────

@router.post("/digests/news-runs/start", response_model=NewsRunOut, status_code=201, dependencies=[Depends(require_scope("digests_stories"))])
def start_news_run(payload: NewsRunStart, db: Session = Depends(get_db)):
    run = NewsRun(
        pipeline_name=payload.pipeline_name,
        trigger_type=payload.trigger_type,
        started_at=payload.started_at,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


# ── Pipeline: report a failure BEFORE any content was produced ──

@router.patch("/digests/news-runs/{run_id}", response_model=NewsRunOut, dependencies=[Depends(require_scope("digests_stories"))])
def fail_news_run(run_id: int, payload: NewsRunFinishFailure, db: Session = Depends(get_db)):
    run = db.query(NewsRun).filter(NewsRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="News run not found")

    run.status = payload.status
    run.error_message = payload.error_message
    run.finished_at = datetime.now(timezone.utc)

    if run.started_at:
        run.duration_seconds = int((run.finished_at - run.started_at).total_seconds())

    db.commit()
    db.refresh(run)
    return run


# ── Pipeline: bulk-post stories, closes the run automatically ──

@router.post("/stories/bulk", response_model=StoryBulkResponse, status_code=201, dependencies=[Depends(require_scope("digests_stories"))])
def create_stories_bulk(payload: StoryBulkCreate, db: Session = Depends(get_db)):
    news_run = db.query(NewsRun).filter(NewsRun.id == payload.news_run_id).first()
    if not news_run:
        raise HTTPException(status_code=404, detail="News run not found")

    # ── Tier 1: requested digest_id ──
    digest = db.query(Digest).filter(Digest.id == payload.digest_id).first()

    # ── Tier 2: fall back to the digest this news_run already produced ──
    if not digest:
        digest = db.query(Digest).filter(Digest.pipeline_run_id == payload.news_run_id).first()
        if digest:
            db.add(FallbackLog(
                fallback_type="digest_self_corrected",
                entity_type="digest",
                entity_id=digest.id,
                detail=f"Requested digest_id {payload.digest_id} not found; recovered via news_run_id linkage",
                news_run_id=payload.news_run_id,
            ))

    # ── Tier 3: fall back to the permanent "unassigned" digest ──
    used_unassigned = False
    if not digest:
        digest = db.query(Digest).filter(Digest.slug == "unassigned").first()
        if not digest:
            raise HTTPException(
                status_code=500,
                detail="No valid digest found and 'unassigned' fallback digest is missing — seed it first"
            )
        used_unassigned = True
        db.add(FallbackLog(
            fallback_type="unassigned_digest_used",
            entity_type="digest",
            entity_id=digest.id,
            detail=f"Requested digest_id {payload.digest_id} not found and no digest exists for news_run_id {payload.news_run_id}; batch reassigned to unassigned digest",
            news_run_id=payload.news_run_id,
        ))

    received = len(payload.stories)
    created = 0
    created_but_flagged = 0
    failed = 0
    errors = []

    for story_data in payload.stories:
        try:
            slug = slugify(story_data.headline)
            is_flagged = used_unassigned

            existing = db.query(Story).filter(Story.slug == slug).first()
            if existing:
                suffix = 2
                candidate_slug = f"{slug}-{suffix}"
                while db.query(Story).filter(Story.slug == candidate_slug).first():
                    suffix += 1
                    candidate_slug = f"{slug}-{suffix}"
                slug = candidate_slug
                is_flagged = True

            company_slug = get_company_slug(story_data.source, db=db, news_run_id=payload.news_run_id)
            image_id = resolve_story_image(db, company_slug, story_data.image_category, digest.id)

            new_story = Story(
                **story_data.model_dump(),
                digest_id=digest.id,
                slug=slug,
                company_slug=company_slug,
                image_id=image_id,
                is_active=not is_flagged,
            )
            db.add(new_story)
            db.flush()  # get new_story.id without a full commit yet

            if is_flagged:
                created_but_flagged += 1
                if not used_unassigned:
                    # only log duplicate-slug specifically here; the unassigned-digest
                    # case was already logged once above at the batch level
                    db.add(FallbackLog(
                        fallback_type="duplicate_slug",
                        entity_type="story",
                        entity_id=new_story.id,
                        detail=f"Duplicate slug, suffixed to '{slug}'",
                        news_run_id=payload.news_run_id,
                    ))
            else:
                created += 1

            if image_id is None:
                db.add(FallbackLog(
                    fallback_type="no_image_resolved",
                    entity_type="story",
                    entity_id=new_story.id,
                    detail=f"No image found for company={company_slug}, category={story_data.image_category}",
                    news_run_id=payload.news_run_id,
                ))

        except Exception as e:
            failed += 1
            errors.append({"headline": story_data.headline, "error": str(e)})
            db.rollback()

    db.commit()

    # ── Close out the run ──
    news_run.finished_at = datetime.now(timezone.utc)
    news_run.status = "success" if (created + created_but_flagged) > 0 or received == 0 else "failed"
    news_run.stories_found = received
    news_run.stories_created = created + created_but_flagged
    news_run.stories_failed = failed
    news_run.sources_attempted = payload.sources_attempted
    news_run.sources_failed = payload.sources_failed

    if news_run.started_at:
        news_run.duration_seconds = int((news_run.finished_at - news_run.started_at).total_seconds())

    db.commit()

    return StoryBulkResponse(
        news_run_id=payload.news_run_id,
        status=news_run.status,
        received=received,
        created=created,
        created_but_flagged=created_but_flagged,
        failed=failed,
        errors=errors,
        run_finished_at=news_run.finished_at,
        duration_seconds=news_run.duration_seconds,
    )


# ── Dashboard: admin read ─────────────────────────────────

@router.get("/admin/news-runs", response_model=list[NewsRunOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_news_runs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(NewsRun).order_by(NewsRun.started_at.desc()).limit(limit).all()