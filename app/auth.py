import hashlib
from datetime import datetime, timezone
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey


def require_scope(scope: str):
    def checker(x_api_key: str = Header(...), db: Session = Depends(get_db)):
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        key_row = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        ).first()

        if not key_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key"
            )

        if key_row.scope != scope:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This key is not authorized for '{scope}' operations"
            )

        key_row.last_used_at = datetime.now(timezone.utc)
        db.commit()

        return key_row
    return checker