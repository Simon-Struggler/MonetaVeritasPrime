import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from dependencies import get_current_user_id_optional
from models import Category, Country, Material, Mint, CollectibleItem, Coin, Banknote

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Фикстура для анонимного клиента
@pytest.fixture(name="client_no_auth")
def client_no_auth_fixture():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: None
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

# Фикстура для авторизованного клиента (user_id = 1)
@pytest.fixture(name="client_auth")
def client_auth_fixture():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: 1
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

# Фикстура для авторизованного клиента ДРУГОГО пользователя (user_id = 2)
@pytest.fixture(name="client_auth_2")
def client_auth_2_fixture():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_optional] = lambda: 2
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

# Функция для подготовки БД (справочники)
def seed_references(db_session):
    cat = Category(title="Монеты")
    country = Country(title="Россия")
    mat = Material(title="Серебро")
    
    db_session.add_all([cat, country, mat])
    db_session.commit()

    mint = Mint(title="Московский монетный двор", country_id=country.id)
    db_session.add(mint)
    db_session.commit()
    
    return cat.id, country.id, mat.id, mint.id


def test_create_category_unauthorized(client_no_auth):
    response = client_no_auth.post("/catalog/categories", json={"title": "Тест"})
    assert response.status_code == 401

def test_create_and_list_categories(client_auth):
    client_auth.post("/catalog/categories", json={"title": "Тестовая категория"})
    response = client_auth.get("/catalog/categories")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Тестовая категория"

def test_update_category(client_auth):
    res = client_auth.post("/catalog/categories", json={"title": "Старое"}).json()
    response = client_auth.put(f"/catalog/categories/{res['id']}", json={"title": "Новое"})
    assert response.status_code == 200
    assert response.json()["title"] == "Новое"

def test_delete_category(client_auth):
    res = client_auth.post("/catalog/categories", json={"title": "Удалить"}).json()
    response = client_auth.delete(f"/catalog/categories/{res['id']}")
    assert response.status_code == 204


def test_create_coin(client_auth):
    db = TestingSessionLocal()
    cat_id, country_id, mat_id, mint_id = seed_references(db)
    db.close()

    coin_payload = {
        "type": "coin",
        "name": "Рубль 1997",
        "category_id": cat_id,
        "country_id": country_id,
        "year": 1997,
        "denomination": 1,
        "currency": "RUB",
        "material_id": mat_id,
        "mint_id": mint_id,
        "is_published": True
    }
    response = client_auth.post("/catalog/items", json=coin_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Рубль 1997"
    assert data["type"] == "coin"
    assert data["material"]["title"] == "Серебро"
    assert "mint" in data

def test_create_banknote(client_auth):
    db = TestingSessionLocal()
    cat_id, country_id, _, _ = seed_references(db)
    db.close()

    banknote_payload = {
        "type": "banknote",
        "name": "100 рублей 2017",
        "category_id": cat_id,
        "country_id": country_id,
        "year": 2017,
        "denomination": 100,
        "currency": "RUB",
        "width": 150,
        "height": 65
    }
    response = client_auth.post("/catalog/items", json=banknote_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "banknote"
    assert data["width"] == 150

def test_get_item_detail(client_auth):
    db = TestingSessionLocal()
    cat_id, country_id, mat_id, mint_id = seed_references(db)
    
    coin = Coin(
        name="Прямая запись", type="coin", country_id=country_id, category_id=cat_id,
        author_id=1, denomination=5, material_id=mat_id, mint_id=mint_id, is_published=True
    )
    db.add(coin)
    db.commit()
    db.refresh(coin)
    db.close()

    response = client_auth.get(f"/catalog/items/{coin.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Прямая запись"


def test_items_visibility_unpublished_vs_published(client_auth):
    """
    Тест проверяет:
    - Аноним видит только опубликованные
    - Автор видит свои неопубликованные
    - Чужой не видит неопубликованные предметы
    """
    db = TestingSessionLocal()
    cat_id, country_id, _, _ = seed_references(db)
    
    # Предмет 1: Опубликованный, автор user_id=1
    item1 = Banknote(name="Опубликованная", type="banknote", country_id=country_id, author_id=1, denomination=10, is_published=True)
    # Предмет 2: Неопубликованный, автор user_id=1
    item2 = Banknote(name="Черновик юзера 1", type="banknote", country_id=country_id, author_id=1, denomination=20, is_published=False)
    # Предмет 3: Неопубликованный, автор user_id=2
    item3 = Banknote(name="Черновик юзера 2", type="banknote", country_id=country_id, author_id=2, denomination=50, is_published=False)
    
    db.add_all([item1, item2, item3])
    db.commit()
    db.close()

    # Вспомогательная функция для безопасной смены пользователя внутри теста
    def act_as(user_id):
        app.dependency_overrides[get_current_user_id_optional] = lambda: user_id

    # Действуем как Аноним
    act_as(None)
    res_anon = client_auth.get("/catalog/items").json()
    assert len(res_anon) == 1
    assert res_anon[0]["name"] == "Опубликованная"

    # Действуем как Юзер 1
    act_as(1)
    res_user1 = client_auth.get("/catalog/items").json()
    assert len(res_user1) == 2
    names_user1 = [item["name"] for item in res_user1]
    assert "Опубликованная" in names_user1
    assert "Черновик юзера 1" in names_user1

    # Действуем как Юзер 2
    act_as(2)
    res_user2 = client_auth.get("/catalog/items").json()
    assert len(res_user2) == 2
    names_user2 = [item["name"] for item in res_user2]
    assert "Опубликованная" in names_user2
    assert "Черновик юзера 2" in names_user2
    
def test_update_item_forbidden_for_another_user(client_auth, client_auth_2):
    db = TestingSessionLocal()
    cat_id, country_id, _, _ = seed_references(db)
    
    coin = Coin(name="Чужая монета", type="coin", country_id=country_id, author_id=1, denomination=1, is_published=True)
    db.add(coin)
    db.commit()
    db.refresh(coin)
    db.close()

    update_payload = {
        "type": "coin",
        "name": "Украденная монета",
        "country_id": country_id,
        "denomination": 1
    }
    response = client_auth_2.put(f"/catalog/items/{coin.id}", json=update_payload)
    assert response.status_code == 403

def test_delete_item_forbidden_for_another_user(client_auth, client_auth_2):
    db = TestingSessionLocal()
    cat_id, country_id, _, _ = seed_references(db)
    
    coin = Coin(name="Чужая монета", type="coin", country_id=country_id, author_id=1, denomination=1)
    db.add(coin)
    db.commit()
    db.refresh(coin)
    db.close()

    response = client_auth_2.delete(f"/catalog/items/{coin.id}")
    assert response.status_code == 403

def test_get_non_existent_item(client_auth):
    response = client_auth.get("/catalog/items/9999")
    assert response.status_code == 404