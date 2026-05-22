from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
import httpx
from database import get_db
from dependencies import get_current_user_id
import models
import schemas
from config import settings

router = APIRouter(prefix="/trade", tags=["trade"])

async def transfer_ownership(item_id: int, new_owner_id: int):
    """Внутренний вызов catalog для смены владельца предмета"""
    async with httpx.AsyncClient() as client:
        # Предположим, в catalog есть internal эндпоинт /internal/items/{item_id}/transfer
        resp = await client.put(
            f"{settings.CATALOG_SERVICE_URL}/internal/items/{item_id}/transfer",
            json={"new_owner_id": new_owner_id}
        )
        return resp.status_code == 200

@router.post("/offers", response_model=schemas.TradeOfferResponse, status_code=201)
async def create_offer(
    offer: schemas.TradeOfferCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # 1. Проверяем, что предложенный предмет существует
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.CATALOG_SERVICE_URL}/internal/items/{offer.offered_item_id}")
        if resp.status_code != 200:
            raise HTTPException(404, "Offered item not found")
        item = resp.json()

        # Проверяем, что пользователь либо автор (author_id), либо владелец в Collections
        if item["author_id"] != current_user_id:
            # Попробуем проверить в Collections, форвардя Authorization от запроса
            auth = request.headers.get("authorization")
            try:
                coll_resp = await client.get(
                    f"{settings.COLLECTIONS_SERVICE_URL}/collections/?skip=0&limit=100",
                    headers={"Authorization": auth} if auth else None
                )
                if coll_resp.status_code == 200:
                    coll_items = coll_resp.json()
                    if not any(ci.get("item_id") == offer.offered_item_id for ci in coll_items):
                        raise HTTPException(403, "You don't own this item")
                else:
                    raise HTTPException(403, "You don't own this item")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(403, "You don't own this item")

        # 2. Если указан запрашиваемый предмет, проверяем, что он существует и принадлежит получателю
        if offer.requested_item_id:
            resp2 = await client.get(f"{settings.CATALOG_SERVICE_URL}/internal/items/{offer.requested_item_id}")
            if resp2.status_code != 200:
                raise HTTPException(404, "Requested item not found")
            requested_item = resp2.json()
            if requested_item["author_id"] != offer.to_user_id:
                coll_resp = await client.get(
                    f"{settings.COLLECTIONS_SERVICE_URL}/collections/internal/users/{offer.to_user_id}/items/{offer.requested_item_id}"
                )
                if coll_resp.status_code != 200 or not coll_resp.json().get("owns"):
                    raise HTTPException(403, "The target user does not own the requested item")

    # 3. Создаём предложение
    db_offer = models.TradeOffer(
        from_user_id=current_user_id,
        to_user_id=offer.to_user_id,
        offered_item_id=offer.offered_item_id,
        requested_item_id=offer.requested_item_id
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer

@router.get("/offers/sent", response_model=List[schemas.TradeOfferResponse])
def list_sent_offers(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return db.query(models.TradeOffer).filter(models.TradeOffer.from_user_id == current_user_id).all()

@router.get("/offers/received", response_model=List[schemas.TradeOfferResponse])
def list_received_offers(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return db.query(models.TradeOffer).filter(
        models.TradeOffer.to_user_id == current_user_id,
        models.TradeOffer.status == models.TradeStatus.PENDING
    ).all()

@router.post("/offers/{offer_id}/respond")
async def respond_to_offer(
    offer_id: int,
    action: schemas.TradeAction,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    offer = db.query(models.TradeOffer).filter(models.TradeOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(404, "Offer not found")
    if offer.to_user_id != current_user_id:
        raise HTTPException(403, "You are not the recipient of this offer")
    if offer.status != models.TradeStatus.PENDING:
        raise HTTPException(400, f"Offer already {offer.status}")

    if action.accept:
        # Принимаем обмен: меняем владельцев предметов
        # Передаём offered_item от from_user к to_user
        success1 = await transfer_ownership(offer.offered_item_id, offer.to_user_id)
        if not success1:
            raise HTTPException(500, "Failed to transfer offered item")
        # Если есть requested_item, передаём его от to_user к from_user
        if offer.requested_item_id:
            success2 = await transfer_ownership(offer.requested_item_id, offer.from_user_id)
            if not success2:
                # Откат? Для простоты просто ошибка
                raise HTTPException(500, "Failed to transfer requested item")
        offer.status = models.TradeStatus.ACCEPTED
    else:
        offer.status = models.TradeStatus.REJECTED

    db.commit()
    return {"message": f"Offer {offer.status}"}