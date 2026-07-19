from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from slugify import slugify

from app.database import get_db
from app.models import Company, ImageCategory, Image, Story
from app.schemas import (
    CompanyCreate, CompanyUpdate, CompanyOut, CompanyPublicOut,
    ImageCategoryCreate, ImageCategoryOut,
    ImageCreate, ImageUpdate, ImageOut,
)
from app.auth_admin import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin-companies"])
public_router = APIRouter(prefix="/api/v1", tags=["companies"])


# ── Admin: Companies ─────────────────────────────────────

@router.get("/companies", response_model=list[CompanyOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_companies_admin(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.name).all()


@router.post("/companies", response_model=CompanyOut, status_code=201, dependencies=[Depends(require_role("owner", "admin"))])
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Company with this name already exists")

    slug = slugify(payload.name)
    new_company = Company(**payload.model_dump(), slug=slug)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


@router.patch("/companies/{company_id}", response_model=CompanyOut, dependencies=[Depends(require_role("owner", "admin"))])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/companies/{company_id}", dependencies=[Depends(require_role("owner"))])
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.slug == "untracked":
        raise HTTPException(status_code=400, detail="Cannot delete the Untracked fallback company")

    db.delete(company)
    db.commit()
    return {"status": "deleted"}


# ── Admin: Image Categories ───────────────────────────────

@router.get("/image-categories", response_model=list[ImageCategoryOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_image_categories(db: Session = Depends(get_db)):
    return db.query(ImageCategory).order_by(ImageCategory.key).all()


@router.post("/image-categories", response_model=ImageCategoryOut, status_code=201, dependencies=[Depends(require_role("owner", "admin"))])
def create_image_category(payload: ImageCategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(ImageCategory).filter(ImageCategory.key == payload.key).first()
    if existing:
        raise HTTPException(status_code=409, detail="Image category with this key already exists")

    new_category = ImageCategory(**payload.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.delete("/image-categories/{category_id}", dependencies=[Depends(require_role("owner"))])
def delete_image_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ImageCategory).filter(ImageCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Image category not found")

    in_use = db.query(Image).filter(Image.image_category_id == category_id).first()
    if in_use:
        raise HTTPException(status_code=400, detail="Cannot delete a category that has images assigned to it")

    db.delete(category)
    db.commit()
    return {"status": "deleted"}


# ── Admin: Images ──────────────────────────────────────────

@router.get("/images", response_model=list[ImageOut], dependencies=[Depends(require_role("owner", "admin", "read_only"))])
def list_images(company_id: int | None = None, image_category_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Image)
    if company_id:
        q = q.filter(Image.company_id == company_id)
    if image_category_id:
        q = q.filter(Image.image_category_id == image_category_id)
    images = q.order_by(Image.created_at.desc()).all()

    image_ids = [img.id for img in images]
    usage_counts = dict(
        db.query(Story.image_id, func.count(Story.id))
        .filter(Story.image_id.in_(image_ids))
        .group_by(Story.image_id)
        .all()
    ) if image_ids else {}

    for img in images:
        img.usage_count = usage_counts.get(img.id, 0)

    return images


@router.post("/images", response_model=ImageOut, status_code=201, dependencies=[Depends(require_role("owner", "admin"))])
def create_image(payload: ImageCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    category = db.query(ImageCategory).filter(ImageCategory.id == payload.image_category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Image category not found")

    new_image = Image(**payload.model_dump())
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


@router.patch("/images/{image_id}", response_model=ImageOut, dependencies=[Depends(require_role("owner", "admin"))])
def update_image(image_id: int, payload: ImageUpdate, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "company_id" in update_data:
        company = db.query(Company).filter(Company.id == update_data["company_id"]).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    if "image_category_id" in update_data:
        category = db.query(ImageCategory).filter(ImageCategory.id == update_data["image_category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Image category not found")

    for field, value in update_data.items():
        setattr(image, field, value)

    db.commit()
    db.refresh(image)
    image.usage_count = db.query(Story).filter(Story.image_id == image.id).count()
    return image


@router.delete("/images/{image_id}", dependencies=[Depends(require_role("owner", "admin"))])
def delete_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    db.delete(image)
    db.commit()
    return {"status": "deleted"}


# ── Public: Companies ──────────────────────────────────────

@public_router.get("/companies", response_model=list[CompanyPublicOut])
def list_public_companies(exclusive: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(Company).filter(Company.page_visible == True)
    if exclusive is not None:
        q = q.filter(Company.exclusive == exclusive)
    return q.order_by(Company.name).all()


@public_router.get("/companies/{slug}", response_model=CompanyPublicOut)
def get_public_company(slug: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.slug == slug, Company.page_visible == True).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company