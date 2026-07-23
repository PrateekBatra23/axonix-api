import random
from sqlalchemy.orm import Session

from app.models import Company, ImageCategory, Image, Story,FallbackLog


_untracked_id_cache = None


def _get_untracked_company_id(db: Session) -> int | None:
    global _untracked_id_cache
    if _untracked_id_cache is None:
        row = db.query(Company).filter(Company.slug == "untracked").first()
        if row:
            _untracked_id_cache = row.id
    return _untracked_id_cache


def _images_excluding_used(db: Session, company_id: int, category_id: int, used_ids: set[int]):
    q = db.query(Image).filter(
        Image.company_id == company_id,
        Image.image_category_id == category_id,
        Image.is_active == True,
    )
    if used_ids:
        q = q.filter(~Image.id.in_(used_ids))
    return q.all()

def resolve_story_image(db: Session, company_slug: str | None, image_category_key: str | None, digest_id: int) -> int | None:
    """
    Resolves exactly one Image.id to permanently attach to a new story.
    Priority: (company, category) -> (company, general) -> (Untracked, general).
    Never repeats an image already used by another story in the same digest.
    """
    # Step 1 — resolve category, fallback to "general"
    category = None
    if image_category_key:
        category = db.query(ImageCategory).filter(ImageCategory.key == image_category_key).first()

    general_category = db.query(ImageCategory).filter(ImageCategory.key == "general").first()

    if not category:
        category = general_category

    if not category:
        return None  # neither the requested category nor "general" exist yet

    # Step 2 — resolve company, fallback to Untracked
    company = db.query(Company).filter(
        Company.slug == company_slug,
        Company.is_active == True,
    ).first() if company_slug else None    
    untracked_id = _get_untracked_company_id(db)
    company_id = company.id if company else untracked_id

    # Images already used by other stories in this same digest
    used_ids = set(
        row[0] for row in
        db.query(Story.image_id).filter(Story.digest_id == digest_id, Story.image_id.isnot(None)).all()
    )

    # Step 3 — (company, resolved category)
    candidates = _images_excluding_used(db, company_id, category.id, used_ids)
    if candidates:
        return random.choice(candidates).id

    # Step 4 — (company, general), only if we haven't already tried general above
    if general_category and general_category.id != category.id:
        candidates = _images_excluding_used(db, company_id, general_category.id, used_ids)
        if candidates:
            return random.choice(candidates).id

    # Step 5 — (Untracked, general), only if company wasn't already Untracked
    if general_category and untracked_id and company_id != untracked_id:
        candidates = _images_excluding_used(db, untracked_id, general_category.id, used_ids)
        if candidates:
            return random.choice(candidates).id

    db.add(FallbackLog(
        fallback_type="no_image_resolved",
        entity_type="story",
        entity_id=None,
        detail=f"No image found for company_slug={company_slug}, category={image_category_key}",
    ))
    return None