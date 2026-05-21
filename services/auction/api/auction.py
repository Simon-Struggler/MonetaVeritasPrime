from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas
from database import get_db
from dependencies import get_current_user_id

router = APIRouter(prefix="/auction", tags=["auction"])

@router.post("/lots", response_model=schemas.LotResponse)
def create_lot(lot: schemas.LotCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Проверка существования item_id через Catalog Service (опционально)
    db_lot = models.Lot(
        item_id=lot.item_id,
        seller_id=user_id,
        start_price=lot.start_price,
        current_price=lot.start_price,
        end_time=lot.end_time,
    )
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

@router.get("/lots", response_model=list[schemas.LotResponse])
def list_lots(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Lot)
    if active_only:
        query = query.filter(models.Lot.is_active == True, models.Lot.end_time > datetime.now())
    return query.all()

@router.post("/bids", response_model=schemas.BidResponse)
def place_bid(bid: schemas.BidCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    lot = db.query(models.Lot).filter(models.Lot.id == bid.lot_id).first()
    if not lot or not lot.is_active or lot.end_time < datetime.now():
        raise HTTPException(400, "Lot not active")
    if lot.seller_id == user_id:
        raise HTTPException(403, "Seller cannot bid on own lot")
    if bid.amount <= lot.current_price:
        raise HTTPException(400, "Bid must be higher than current price")
    
    lot.current_price = bid.amount
    new_bid = models.Bid(lot_id=bid.lot_id, bidder_id=user_id, amount=bid.amount)
    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)
    return new_bid