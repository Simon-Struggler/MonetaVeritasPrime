import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app  
from models import User


# Настройка in-memory SQLite для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """
    autouse=True означает, что эта функция будет автоматически 
    запускаться ПЕРЕД каждым тестом и ПОСЛЕ каждого теста.
    """
    # Выполняется ПЕРЕД тестом: создаем чистые таблицы
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Выполняется ПОСЛЕ теста: удаляем все таблицы (очищаем базу)
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_test_user(username="testuser", email="test@test.com", password="password123"):
    response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password}
    )
    return response

def get_auth_header(username="testuser", password="password123"):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_success():
    """Тест успешной регистрации нового пользователя"""
    response = create_test_user()
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@test.com"
    assert "id" in data
    # Убеждаемся, что хеш пароля не возвращается
    assert "password_hash" not in data 


def test_register_duplicate_username():
    """Тест попытки регистрации с уже существующим username"""
    create_test_user(username="john_doe")
    response = create_test_user(username="john_doe", email="another@email.com")
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_register_duplicate_email():
    """Тест попытки регистрации с уже существующим email"""
    create_test_user(email="unique@test.com")
    response = create_test_user(username="another_user", email="unique@test.com")
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success():
    """Тест успешного входа и получения токена"""
    create_test_user()
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password():
    """Тест входа с неверным паролем"""
    create_test_user()
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_non_existent_user():
    """Тест входа с несуществующим пользователем"""
    response = client.post(
        "/auth/login",
        json={"username": "ghost", "password": "password123"}
    )
    
    assert response.status_code == 401


def test_read_users_me_success():
    """Тест успешного получения профиля текущего пользователя"""
    create_test_user()
    headers = get_auth_header()
    
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@test.com"


def test_read_users_me_missing_token():
    """Тест обращения к /me без токена"""
    response = client.get("/auth/me")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_users_me_invalid_token():
    """Тест обращения к /me с поддельным/невалидным токеном"""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_read_users_me_deleted_user():
    """Тест обращения к /me с токеном удаленного пользователя (симуляция)"""
    # Создаем пользователя и получаем токен
    create_test_user()
    headers = get_auth_header()
    
    # Имитируем удаление пользователя напрямую через БД
    db = TestingSessionLocal()
    db.query(User).filter(User.username == "testuser").delete()
    db.commit()
    db.close()
    
    # Пробуем получить профиль по старому токену
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"