import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, Mock, patch 

from main import app
from database import Base, get_db
from models import UserCollectionItem
from dependencies import get_current_user_id

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_current_user_id():
        return 1
    
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.pop(get_current_user_id, None)


def get_mock_catalog_response(item_id: int, is_published: bool = True, author_id: int = 2):
    return {
        "id": item_id,
        "type": "coin",
        "name": f"Test Coin {item_id}",
        "denomination": 10,
        "currency": "RUB",
        "country_id": 1,
        "is_published": is_published,
        "author_id": author_id,
        "created_at": "2023-01-01T00:00:00",
        "category": None,
        "country": None
    }


class TestAddToCollection:

    @patch("api.collections.httpx.AsyncClient")
    def test_add_item_success(self, mock_httpx_class, client, db_session):
        item_id = 101
        
        # Используем обычный Mock, чтобы resp.json() возвращал dict сразу (синхронно)
        mock_response = Mock() 
        mock_response.status_code = 200
        mock_response.json.return_value = get_mock_catalog_response(item_id)
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        
        mock_httpx_class.return_value = mock_client

        response = client.post(
            "/collections/",
            json={"item_id": item_id, "notes": "My favorite coin"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["item_id"] == item_id
        assert data["item"]["id"] == item_id
        
        db_item = db_session.query(UserCollectionItem).filter_by(user_id=1, item_id=item_id).first()
        assert db_item is not None

    @patch("api.collections.httpx.AsyncClient")
    def test_add_item_not_found_in_catalog(self, mock_httpx_class, client):
        item_id = 999
        
        mock_response = Mock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        
        mock_httpx_class.return_value = mock_client

        response = client.post("/collections/", json={"item_id": item_id})
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found or not accessible"

    @patch("api.collections.httpx.AsyncClient")
    def test_add_item_duplicate(self, mock_httpx_class, client, db_session):
        item_id = 102
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = get_mock_catalog_response(item_id)
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_httpx_class.return_value = mock_client

        client.post("/collections/", json={"item_id": item_id})
        response = client.post("/collections/", json={"item_id": item_id})
        
        assert response.status_code == 400
        assert "already in collection" in response.json()["detail"]

    @patch("api.collections.httpx.AsyncClient")
    def test_add_item_permission_denied_unpublished(self, mock_httpx_class, client):
        item_id = 103
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = get_mock_catalog_response(
            item_id, is_published=False, author_id=2
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_httpx_class.return_value = mock_client

        response = client.post("/collections/", json={"item_id": item_id})
        
        assert response.status_code == 403
        assert "cannot add this item" in response.json()["detail"]


class TestGetCollection:

    @patch("api.collections.httpx.AsyncClient")
    def test_get_my_collection(self, mock_httpx_class, client, db_session):
        col_item_1 = UserCollectionItem(user_id=1, item_id=201, notes="Note 1")
        col_item_2 = UserCollectionItem(user_id=1, item_id=202, notes="Note 2")
        db_session.add_all([col_item_1, col_item_2])
        db_session.commit()

        def mock_get_side_effect(url, *args, **kwargs):
            item_id = int(url.split("/")[-1])
            # Используем Mock, чтобы данные возвращались синхронно
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = get_mock_catalog_response(item_id)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.get.side_effect = mock_get_side_effect
        mock_client.__aenter__.return_value = mock_client
        mock_httpx_class.return_value = mock_client

        response = client.get("/collections/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["notes"] == "Note 1"

    @patch("api.collections.httpx.AsyncClient")
    def test_get_my_collection_catalog_error(self, mock_httpx_class, client, db_session):
        col_item = UserCollectionItem(user_id=1, item_id=301, notes="Error Item")
        db_session.add(col_item)
        db_session.commit()

        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Catalog service down")
        mock_client.__aenter__.return_value = mock_client
        mock_httpx_class.return_value = mock_client

        response = client.get("/collections/")
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestRemoveFromCollection:

    def test_remove_item_success(self, client, db_session):
        col_item = UserCollectionItem(user_id=1, item_id=401, notes="To delete")
        db_session.add(col_item)
        db_session.commit()
        collection_id = col_item.id

        response = client.delete(f"/collections/{collection_id}")
        assert response.status_code == 204
        
        deleted_item = db_session.query(UserCollectionItem).filter_by(id=collection_id).first()
        assert deleted_item is None

    def test_remove_item_not_found(self, client):
        response = client.delete("/collections/99999")
        assert response.status_code == 404
        
    def test_remove_item_wrong_user(self, client, db_session):
        other_item = UserCollectionItem(user_id=2, item_id=501, notes="Not mine")
        db_session.add(other_item)
        db_session.commit()
        
        response = client.delete(f"/collections/{other_item.id}")
        assert response.status_code == 404