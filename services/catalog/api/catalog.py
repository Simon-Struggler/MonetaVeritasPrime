from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional, Union
import models
import schemas
from database import get_db
from dependencies import get_current_user_id_optional

router = APIRouter(prefix="/catalog", tags=["catalog"])

# --- Вспомогательная функция для получения предмета с проверкой прав ---
def get_item(db: Session, item_id: int, user_id: Optional[int] = None):
    item = db.query(models.CollectibleItem).options(
        joinedload(models.CollectibleItem.category),
        joinedload(models.CollectibleItem.country)
    ).filter(models.CollectibleItem.id == item_id).first()
    if not item:
        return None
    if not item.is_published and (user_id is None or item.author_id != user_id):
        return None
    return item

# ==================== КАТЕГОРИИ ====================
@router.get("/categories", response_model=List[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(
    category: schemas.CategoryBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_cat = models.Category(**category.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category: schemas.CategoryBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(404, "Category not found")
    db_cat.title = category.title
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(404, "Category not found")
    db.delete(db_cat)
    db.commit()
    return

# ==================== СТРАНЫ ====================
@router.get("/countries", response_model=List[schemas.CountryResponse])
def list_countries(db: Session = Depends(get_db)):
    return db.query(models.Country).all()

@router.post("/countries", response_model=schemas.CountryResponse, status_code=201)
def create_country(
    country: schemas.CountryBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_country = models.Country(**country.model_dump())
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

@router.put("/countries/{country_id}", response_model=schemas.CountryResponse)
def update_country(
    country_id: int,
    country: schemas.CountryBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not db_country:
        raise HTTPException(404, "Country not found")
    db_country.title = country.title
    db.commit()
    db.refresh(db_country)
    return db_country

@router.delete("/countries/{country_id}", status_code=204)
def delete_country(
    country_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not db_country:
        raise HTTPException(404, "Country not found")
    db.delete(db_country)
    db.commit()
    return

# ==================== МАТЕРИАЛЫ ====================
@router.get("/materials", response_model=List[schemas.MaterialResponse])
def list_materials(db: Session = Depends(get_db)):
    return db.query(models.Material).all()

@router.post("/materials", response_model=schemas.MaterialResponse, status_code=201)
def create_material(
    material: schemas.MaterialBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_material = models.Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

@router.put("/materials/{material_id}", response_model=schemas.MaterialResponse)
def update_material(
    material_id: int,
    material: schemas.MaterialBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not db_material:
        raise HTTPException(404, "Material not found")
    db_material.title = material.title
    db.commit()
    db.refresh(db_material)
    return db_material

@router.delete("/materials/{material_id}", status_code=204)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not db_material:
        raise HTTPException(404, "Material not found")
    db.delete(db_material)
    db.commit()
    return

# ==================== МОНЕТНЫЕ ДВОРЫ ====================
@router.get("/mints", response_model=List[schemas.MintResponse])
def list_mints(db: Session = Depends(get_db)):
    return db.query(models.Mint).all()

@router.post("/mints", response_model=schemas.MintResponse, status_code=201)
def create_mint(
    mint: schemas.MintBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_mint = models.Mint(**mint.model_dump())
    db.add(db_mint)
    db.commit()
    db.refresh(db_mint)
    return db_mint

@router.put("/mints/{mint_id}", response_model=schemas.MintResponse)
def update_mint(
    mint_id: int,
    mint: schemas.MintBase,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_mint = db.query(models.Mint).filter(models.Mint.id == mint_id).first()
    if not db_mint:
        raise HTTPException(404, "Mint not found")
    db_mint.title = mint.title
    db_mint.country_id = mint.country_id
    db.commit()
    db.refresh(db_mint)
    return db_mint

@router.delete("/mints/{mint_id}", status_code=204)
def delete_mint(
    mint_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_mint = db.query(models.Mint).filter(models.Mint.id == mint_id).first()
    if not db_mint:
        raise HTTPException(404, "Mint not found")
    db.delete(db_mint)
    db.commit()
    return

# ==================== ПРЕДМЕТЫ (МОНЕТЫ/БАНКНОТЫ) ====================
@router.get("/items", response_model=List[Union[schemas.CoinResponse, schemas.BanknoteResponse]])
def list_items(
    type: Optional[str] = Query(None, enum=["coin", "banknote"]),
    category_id: Optional[int] = None,
    country_id: Optional[int] = None,
    year: Optional[int] = None,
    is_on_main: Optional[bool] = None,
    author_id: Optional[int] = None,        # ← фильтр по автору
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    query = db.query(models.CollectibleItem).options(
        joinedload(models.CollectibleItem.category),
        joinedload(models.CollectibleItem.country)
    )
    if type:
        query = query.filter(models.CollectibleItem.type == type)
    if category_id:
        query = query.filter(models.CollectibleItem.category_id == category_id)
    if country_id:
        query = query.filter(models.CollectibleItem.country_id == country_id)
    if year:
        query = query.filter(models.CollectibleItem.year == year)
    if is_on_main is not None:
        query = query.filter(models.CollectibleItem.is_on_main == is_on_main)
    if author_id is not None:
        query = query.filter(models.CollectibleItem.author_id == author_id)

    # Права доступа: показываем опубликованные всегда, а неопубликованные — только если текущий пользователь является автором
    if user_id:
        # Если передан author_id и он равен user_id, показываем и неопубликованные автора
        if author_id is not None and author_id == user_id:
            # показываем всё, что принадлежит этому автору (включая неопубликованные)
            pass
        else:
            # иначе только опубликованные или свои неопубликованные (если автор совпадает)
            query = query.filter(
                or_(
                    models.CollectibleItem.is_published == True,
                    models.CollectibleItem.author_id == user_id
                )
            )
    else:
        # для неавторизованных — только опубликованные
        query = query.filter(models.CollectibleItem.is_published == True)

    items = query.order_by(models.CollectibleItem.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for item in items:
        if item.type == "coin":
            coin = db.query(models.Coin).filter(models.Coin.id == item.id).options(
                joinedload(models.Coin.material),
                joinedload(models.Coin.mint).joinedload(models.Mint.country)
            ).first()
            result.append(coin)
        else:
            banknote = db.query(models.Banknote).filter(models.Banknote.id == item.id).first()
            result.append(banknote)
    return result

@router.get("/items/{item_id}", response_model=Union[schemas.CoinResponse, schemas.BanknoteResponse])
def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    item = get_item(db, item_id, user_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.type == "coin":
        coin = db.query(models.Coin).filter(models.Coin.id == item_id).options(
            joinedload(models.Coin.material),
            joinedload(models.Coin.mint).joinedload(models.Mint.country)
        ).first()
        return coin
    else:
        banknote = db.query(models.Banknote).filter(models.Banknote.id == item_id).first()
        return banknote

@router.post("/items", response_model=Union[schemas.CoinResponse, schemas.BanknoteResponse], status_code=201)
def create_item(
    item: Union[schemas.CoinCreate, schemas.BanknoteCreate],
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")

    # Преобразуем входящие данные в словарь
    data = item.model_dump()
    data["author_id"] = user_id
    data.pop("type", None)  # убираем type, т.к. в моделях его нет (используется наследование)

    if item.type == "coin":
        db_item = models.Coin(**data)
    else:
        db_item = models.Banknote(**data)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Загружаем связанные данные (для ответа)
    if item.type == "coin":
        db_item = db.query(models.Coin).filter(models.Coin.id == db_item.id).options(
            joinedload(models.Coin.material),
            joinedload(models.Coin.mint).joinedload(models.Mint.country)
        ).first()
    else:
        db_item = db.query(models.Banknote).filter(models.Banknote.id == db_item.id).first()

    return db_item

@router.put("/items/{item_id}", response_model=Union[schemas.CoinResponse, schemas.BanknoteResponse])
def update_item(
    item_id: int,
    item: Union[schemas.CoinCreate, schemas.BanknoteCreate],
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")

    # Получаем существующий предмет с проверкой прав
    db_item = get_item(db, item_id, user_id)
    if not db_item:
        raise HTTPException(404, "Item not found")
    if db_item.author_id != user_id:
        raise HTTPException(403, "Not enough permissions")

    # Обновляем поля (используем только те, что есть в модели)
    data = item.model_dump(exclude={"type"})  # исключаем type, чтобы не было конфликта
    for key, value in data.items():
        if hasattr(db_item, key):
            setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)

    # Возвращаем обновлённый объект с связями
    if db_item.type == "coin":
        db_item = db.query(models.Coin).filter(models.Coin.id == item_id).options(
            joinedload(models.Coin.material),
            joinedload(models.Coin.mint).joinedload(models.Mint.country)
        ).first()
    else:
        db_item = db.query(models.Banknote).filter(models.Banknote.id == item_id).first()

    return db_item

@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    if not user_id:
        raise HTTPException(401, "Authentication required")
    db_item = get_item(db, item_id, user_id)
    if not db_item:
        raise HTTPException(404, "Item not found")
    if db_item.author_id != user_id:
        raise HTTPException(403, "Not enough permissions")
    db.delete(db_item)
    db.commit()
    return