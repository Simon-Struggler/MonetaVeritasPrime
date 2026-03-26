from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/internal", tags=["internal"])

@router.get("/collections/{user_id}")
def get_user_collection(user_id: int, db: Session = Depends(get_db)):
    items = db.query(models.UserCollectionItem).filter(
        models.UserCollectionItem.user_id == user_id
    ).all()
    return [{"item_id": ci.item_id} for ci in items]
