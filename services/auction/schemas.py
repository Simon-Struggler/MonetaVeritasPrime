from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LotBase(BaseModel):
    item_id: int
    start_price: float
    end_time: datetime

class LotCreate(LotBase):
    pass

class LotResponse(LotBase):
    id: int
    seller_id: int
    current_price: float
    start_time: datetime
    is_active: bool

class BidCreate(BaseModel):
    lot_id: int
    amount: float

class BidResponse(BaseModel):
    id: int
    lot_id: int
    bidder_id: int
    amount: float
    created_at: datetime