from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum

class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class TradeOffer(Base):
    __tablename__ = "trade_offers"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, nullable=False)          # кто предлагает
    to_user_id = Column(Integer, nullable=False)            # кому предлагают
    offered_item_id = Column(Integer, nullable=False)       # какой предмет предлагают (id из catalog)
    requested_item_id = Column(Integer, nullable=True)      # какой предмет просят взамен (опционально, если нужен двухсторонний обмен)
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())