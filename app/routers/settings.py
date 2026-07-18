from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import Setting
from app.schemas import SettingOut, SettingUpdate
from app.auth_admin import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["settings"])


def get_setting_value(db: Session, key: str, default: str = "0") -> str:
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else default


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