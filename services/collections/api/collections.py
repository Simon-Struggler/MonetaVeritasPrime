from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from typing import List
import models
import schemas
from dependencies import get_current_user_id
from database import get_db
from config import settings

router = APIRouter(prefix="/collections", tags=["collections"])

@router.get("/", response_model=List[schemas.CollectionItemResponse])
async def get_my_collection(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    print(f"User ID: {user_id}")
    items = db.query(models.UserCollectionItem).filter(
        models.UserCollectionItem.user_id == user_id
    ).offset(skip).limit(limit).all()

    # Получаем данные о предметах из Catalog Service
    async with httpx.AsyncClient() as client:
        result = []
        for ci in items:
            try:
                resp = await client.get(f"{settings.CATALOG_SERVICE_URL}/internal/items/{ci.item_id}")
                if resp.status_code == 200:
                    item_data = resp.json()
                    result.append({
                        "id": ci.id,
                        "user_id": ci.user_id,
                        "item_id": ci.item_id,
                        "notes": ci.notes,
                        "added_at": ci.added_at,
                        "item": item_data
                    })
            except Exception:
                continue
    return result

@router.post("/", response_model=schemas.CollectionItemResponse, status_code=201)
async def add_to_collection(
    data: schemas.CollectionItemCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # Проверяем существование предмета через Catalog Service
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.CATALOG_SERVICE_URL}/internal/items/{data.item_id}")
        if resp.status_code != 200:
            raise HTTPException(404, "Item not found or not accessible")
        item_info = resp.json()
        # Проверяем доступность: предмет должен быть опубликован или пользователь - автор
        if not item_info["is_published"] and item_info["author_id"] != user_id:
            raise HTTPException(403, "You cannot add this item to your collection")

    # Проверяем, нет ли уже в коллекции
    existing = db.query(models.UserCollectionItem).filter(
        models.UserCollectionItem.user_id == user_id,
        models.UserCollectionItem.item_id == data.item_id
    ).first()
    if existing:
        raise HTTPException(400, "Item already in collection")

    collection_item = models.UserCollectionItem(
        user_id=user_id,
        item_id=data.item_id,
        notes=data.notes
    )
    db.add(collection_item)
    db.commit()
    db.refresh(collection_item)

    return {
        "id": collection_item.id,
        "user_id": collection_item.user_id,
        "item_id": collection_item.item_id,
        "notes": collection_item.notes,
        "added_at": collection_item.added_at,
        "item": item_info
    }

@router.delete("/{collection_id}", status_code=204)
def remove_from_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    collection_item = db.query(models.UserCollectionItem).filter(
        models.UserCollectionItem.id == collection_id,
        models.UserCollectionItem.user_id == user_id
    ).first()
    if not collection_item:
        raise HTTPException(404, "Collection item not found")
    db.delete(collection_item)
    db.commit()
    return