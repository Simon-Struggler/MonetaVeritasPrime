from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any


class ExchangeCreate(BaseModel):
    requested_user_id: int
    offered_item_id: int
    requested_item_id: int
    message: Optional[str] = None


class ExchangeResponse(BaseModel):
    id: int
    requester_id: int
    requested_user_id: int
    offered_item_id: int
    requested_item_id: int
    message: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    offered_item: Optional[Any] = None
    requested_item: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)
