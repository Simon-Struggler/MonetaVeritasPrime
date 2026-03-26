from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
import httpx
from typing import List
import models
import schemas
from dependencies import get_current_user_id
from database import get_db
from config import settings

router = APIRouter(prefix="/exchange", tags=["exchange"])


async def fetch_item(item_id: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.CATALOG_SERVICE_URL}/internal/items/{item_id}")
        if resp.status_code != 200:
            return None
        return resp.json()


async def check_item_in_collection(user_id: int, item_id: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.COLLECTIONS_SERVICE_URL}/internal/collections/{user_id}")
        if resp.status_code != 200:
            return False
        collection = resp.json()
        return any(ci["item_id"] == item_id for ci in collection)


def build_trade_response(trade, offered_item=None, requested_item=None):
    return {
        "id": trade.id,
        "requester_id": trade.requester_id,
        "requested_user_id": trade.requested_user_id,
        "offered_item_id": trade.offered_item_id,
        "requested_item_id": trade.requested_item_id,
        "message": trade.message,
        "status": trade.status,
        "created_at": trade.created_at,
        "updated_at": trade.updated_at,
        "offered_item": offered_item,
        "requested_item": requested_item,
    }


@router.post("/trades", response_model=schemas.ExchangeResponse, status_code=201)
async def create_trade(
    data: schemas.ExchangeCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if data.requested_user_id == user_id:
        raise HTTPException(400, "You cannot create a trade with yourself")

    offered_item = await fetch_item(data.offered_item_id)
    if not offered_item:
        raise HTTPException(404, "Offered item not found")

    # Check if offered item is in user's collection
    if not await check_item_in_collection(user_id, data.offered_item_id):
        raise HTTPException(403, "You can only offer an item that is in your collection")

    requested_item = await fetch_item(data.requested_item_id)
    if not requested_item:
        raise HTTPException(404, "Requested item not found")

    # Check if requested item is in target user's collection
    if not await check_item_in_collection(data.requested_user_id, data.requested_item_id):
        raise HTTPException(400, "Requested item is not in the target user's collection")

    existing = db.query(models.ExchangeRequest).filter(
        models.ExchangeRequest.requester_id == user_id,
        models.ExchangeRequest.requested_user_id == data.requested_user_id,
        models.ExchangeRequest.offered_item_id == data.offered_item_id,
        models.ExchangeRequest.requested_item_id == data.requested_item_id,
        models.ExchangeRequest.status == "pending",
    ).first()
    if existing:
        raise HTTPException(400, "Duplicate pending trade request already exists")

    trade = models.ExchangeRequest(
        requester_id=user_id,
        requested_user_id=data.requested_user_id,
        offered_item_id=data.offered_item_id,
        requested_item_id=data.requested_item_id,
        message=data.message,
        status="pending",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    return build_trade_response(trade, offered_item=offered_item, requested_item=requested_item)


@router.get("/trades", response_model=List[schemas.ExchangeResponse])
async def list_trades(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    trades = db.query(models.ExchangeRequest).filter(
        or_(
            models.ExchangeRequest.requester_id == user_id,
            models.ExchangeRequest.requested_user_id == user_id,
        )
    ).order_by(models.ExchangeRequest.created_at.desc()).all()

    result = []
    for trade in trades:
        offered_item = await fetch_item(trade.offered_item_id)
        requested_item = await fetch_item(trade.requested_item_id)
        result.append(build_trade_response(trade, offered_item=offered_item, requested_item=requested_item))
    return result


@router.get("/trades/{trade_id}", response_model=schemas.ExchangeResponse)
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    trade = db.query(models.ExchangeRequest).filter(
        models.ExchangeRequest.id == trade_id,
        or_(
            models.ExchangeRequest.requester_id == user_id,
            models.ExchangeRequest.requested_user_id == user_id,
        ),
    ).first()
    if not trade:
        raise HTTPException(404, "Trade request not found")

    offered_item = await fetch_item(trade.offered_item_id)
    requested_item = await fetch_item(trade.requested_item_id)
    return build_trade_response(trade, offered_item=offered_item, requested_item=requested_item)


@router.post("/trades/{trade_id}/accept", response_model=schemas.ExchangeResponse)
async def accept_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    trade = db.query(models.ExchangeRequest).filter(
        models.ExchangeRequest.id == trade_id,
        models.ExchangeRequest.requested_user_id == user_id,
    ).first()
    if not trade:
        raise HTTPException(404, "Trade request not found")
    if trade.status != "pending":
        raise HTTPException(400, "Trade request is not pending")

    offered_item = await fetch_item(trade.offered_item_id)
    requested_item = await fetch_item(trade.requested_item_id)
    if not offered_item or not requested_item:
        raise HTTPException(404, "One or both items are unavailable")

    # Check if items are still in collections
    if not await check_item_in_collection(trade.requester_id, trade.offered_item_id):
        raise HTTPException(400, "Offered item is no longer in requester's collection")
    if not await check_item_in_collection(trade.requested_user_id, trade.requested_item_id):
        raise HTTPException(400, "Requested item is no longer in your collection")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.CATALOG_SERVICE_URL}/internal/items/{trade.offered_item_id}/transfer",
            json={"new_author_id": trade.requested_user_id},
        )
        if resp.status_code != 200:
            raise HTTPException(500, "Failed to transfer offered item")
        resp = await client.post(
            f"{settings.CATALOG_SERVICE_URL}/internal/items/{trade.requested_item_id}/transfer",
            json={"new_author_id": trade.requester_id},
        )
        if resp.status_code != 200:
            raise HTTPException(500, "Failed to transfer requested item")

    trade.status = "accepted"
    db.commit()
    db.refresh(trade)

    updated_offered_item = await fetch_item(trade.offered_item_id)
    updated_requested_item = await fetch_item(trade.requested_item_id)
    return build_trade_response(trade, offered_item=updated_offered_item, requested_item=updated_requested_item)


@router.post("/trades/{trade_id}/reject", response_model=schemas.ExchangeResponse)
async def reject_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    trade = db.query(models.ExchangeRequest).filter(
        models.ExchangeRequest.id == trade_id,
        models.ExchangeRequest.requested_user_id == user_id,
    ).first()
    if not trade:
        raise HTTPException(404, "Trade request not found")
    if trade.status != "pending":
        raise HTTPException(400, "Trade request is not pending")

    trade.status = "rejected"
    db.commit()
    db.refresh(trade)

    offered_item = await fetch_item(trade.offered_item_id)
    requested_item = await fetch_item(trade.requested_item_id)
    return build_trade_response(trade, offered_item=offered_item, requested_item=requested_item)


@router.delete("/trades/{trade_id}", status_code=204)
async def cancel_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    trade = db.query(models.ExchangeRequest).filter(
        models.ExchangeRequest.id == trade_id,
        models.ExchangeRequest.requester_id == user_id,
    ).first()
    if not trade:
        raise HTTPException(404, "Trade request not found")
    if trade.status != "pending":
        raise HTTPException(400, "Only pending trades can be cancelled")

    trade.status = "cancelled"
    db.commit()
    return
