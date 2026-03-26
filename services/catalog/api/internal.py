from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/internal", tags=["internal"])

@router.get("/items/{item_id}")
def get_item_internal(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.CollectibleItem).filter(models.CollectibleItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    return {"id": item.id, "type": item.type, "author_id": item.author_id, "is_published": item.is_published}