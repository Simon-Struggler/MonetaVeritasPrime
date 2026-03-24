from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union, Any

class CollectionItemCreate(BaseModel):
    item_id: int
    notes: Optional[str] = None

class CollectionItemResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    notes: Optional[str]
    added_at: datetime
    item: Optional[Any] = None  # будет подставляться ответ от Catalog
    model_config = ConfigDict(from_attributes=True)