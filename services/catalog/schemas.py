from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union, Literal

class CategoryBase(BaseModel):
    title: str
class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CountryBase(BaseModel):
    title: str
class CountryResponse(CountryBase):
    id: int

class MaterialBase(BaseModel):
    title: str
class MaterialResponse(MaterialBase):
    id: int

class MintBase(BaseModel):
    title: str
    country_id: int
class MintResponse(MintBase):
    id: int

class CollectibleItemBase(BaseModel):
    name: str
    category_id: Optional[int] = None
    description: Optional[str] = None
    country_id: int
    year: Optional[int] = None
    image_url: Optional[str] = None
    is_published: bool = True
    is_on_main: bool = False

class CoinCreate(CollectibleItemBase):
    type: Literal["coin"] = "coin"
    denomination: int
    currency: str = "RUB"
    material_id: Optional[int] = None
    weight: Optional[float] = None
    mint_id: Optional[int] = None
    diameter: Optional[float] = None

class BanknoteCreate(CollectibleItemBase):
    type: Literal["banknote"] = "banknote"
    denomination: int
    currency: str = "RUB"
    serial_number: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

class CoinResponse(CollectibleItemBase):
    id: int
    type: str
    denomination: int
    currency: str
    material_id: Optional[int] = None
    weight: Optional[float] = None
    mint_id: Optional[int] = None
    diameter: Optional[float] = None
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    # add relationships if needed (category, country, material, mint)
    category: Optional[CategoryResponse] = None
    country: Optional[CountryResponse] = None
    material: Optional[MaterialResponse] = None
    mint: Optional[MintResponse] = None
    model_config = ConfigDict(from_attributes=True)

class BanknoteResponse(CollectibleItemBase):
    id: int
    type: str
    denomination: int
    currency: str
    serial_number: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    category: Optional[CategoryResponse] = None
    country: Optional[CountryResponse] = None
    model_config = ConfigDict(from_attributes=True)