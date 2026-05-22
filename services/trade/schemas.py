from pydantic import BaseModel, ConfigDict, model_serializer
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

    @model_serializer
    def ser(self):
        return {
            "id": self.id,
            "offer_id": self.id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "offered_item_id": self.offered_item_id,
            "requested_item_id": self.requested_item_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

class TradeAction(BaseModel):
    accept: bool   # true = принять, false = отклонить