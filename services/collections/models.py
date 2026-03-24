from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class UserCollectionItem(Base):
    __tablename__ = "collection_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="unique_user_item"),)