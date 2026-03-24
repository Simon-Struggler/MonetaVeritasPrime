from sqlalchemy import Column, Integer, String, Text, Float, Numeric, DateTime, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from database import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False, unique=True)

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(25), nullable=False, unique=True)

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(25), nullable=False, unique=True)

class Mint(Base):
    __tablename__ = "mints"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(25), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    __table_args__ = (UniqueConstraint("title", "country_id", name="unique_mint_per_country"),)

class CollectibleItem(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum("coin", "banknote", name="item_type"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    year = Column(Integer, nullable=True)
    image_url = Column(String(500), nullable=True)
    author_id = Column(Integer, nullable=False)   # ссылка на user_id из Auth
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_published = Column(Boolean, default=True)
    is_on_main = Column(Boolean, default=False)

    category = relationship("Category")
    country = relationship("Country")

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "item"}

class Coin(CollectibleItem):
    __tablename__ = "coins"
    id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    denomination = Column(Integer, nullable=False)
    currency = Column(String(50), default="RUB")
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    weight = Column(Numeric(8,3), nullable=True)
    mint_id = Column(Integer, ForeignKey("mints.id"), nullable=True)
    diameter = Column(Numeric(6,2), nullable=True)

    material = relationship("Material")
    mint = relationship("Mint")
    __mapper_args__ = {"polymorphic_identity": "coin"}

class Banknote(CollectibleItem):
    __tablename__ = "banknotes"
    id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    denomination = Column(Integer, nullable=False)
    currency = Column(String(50), default="RUB")
    serial_number = Column(String(50), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    __mapper_args__ = {"polymorphic_identity": "banknote"}