from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from models import TradeStatus

class TradeOfferCreate(BaseModel):
    to_user_id: int
    offered_item_id: int
    requested_item_id: Optional[int] = None   # если None – это дарение / просто передача

class TradeOfferResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    offered_item_id: int
    requested_item_id: Optional[int]
    status: TradeStatus
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class TradeAction(BaseModel):
    accept: bool   # true = принять, false = отклонить