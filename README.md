# MonetaVeritasPrime

**Moneta Veritas** — это сервис для оцифровки и отслеживания реальной личной коллекции нумизмата (монет и банкнот). 

Проект построен по принципам микросервисной архитектуры. Каждая часть системы отвечает за свою узкую область:
* *_auth_* — отвечает за регистрацию, аутентификацию пользователей и выдачу JWT-токенов.
* *_catalog_* — ядро системы. Управляет справочниками (страны, материалы, монетные дворы, категории) и непосредственно карточками предметов коллекции (монеты и банкноты) с использованием полиморфизма SQLAlchemy.
* *_collections_* — управление личной коллекцией пользователя (добавление, просмотр, удаление предметов из своей коллекции).
* *_auction_* — пользователь выставит предмет из своей коллекции на аукцион на определённое время, пользователи делают ставки, кто поставил больше - тот выиграл (предметы должны быть в коллекциях пользователей).
* *_trade_* — обмен предметами между пользователями (предметы должны быть в коллекциях пользователей).
* *_gateway_* — API Gateway (маршрутизатор), который выступает единой точкой входа для клиентов и проксирует запросы к нужным микросервисам.

---

## Архитектура и зависимости

### Технологии и фреймворки
* **Язык:** Python 3.12.1
* **Веб-фреймворк:** FastAPI
* **ASGI-сервер:** Uvicorn
* **ORM:** SQLAlchemy
* **База данных:** SQLite (драйвер `psycopg2-binary`)
* **Валидация данных:** Pydantic (v2)
* **Аутентификация:** python-jose (JWT), passlib[bcrypt]
* **HTTP-клиент (для межсервисного взаимодействия):** httpx
* **Тестирование:** pytest, coverage

### Взаимодействие между микросервисами
Сервисы общаются по синхронному протоколу HTTP:
* **Gateway** проксирует все входящие запросы (`/auth/`, `/catalog/`, `/collections/`, `/auction/`, `/trade/`) на соответствующие порты внутренних сервисов.
* **Collections Service** при отображении коллекции или добавлении предмета делает внутренние запросы в **Catalog Service** (`GET /internal/items/{item_id}`) через `httpx.AsyncClient`, чтобы получить актуальные данные о предмете и проверить его существование/статус публикации.

### Внешние сервисы
В текущей реализации **не используются** внешние брокеры сообщений (Kafka/RabbitMQ), кэширующие серверы (Redis) или объектные хранилища (S3). Взаимодействие построено исключительно на прямых HTTP-вызовах и базе данных SQLite.

---

## Способы запуска сервиса

### Предварительная настройка
1. Убедитесь, что у вас установлен Python.
2. Установите зависимости в каждом из сервисов (или создайте виртуальное окружение на уровне корня проекта):
   ```bash
   pip install -r requirements.txt
   ```
3. В папках `auth`, `catalog` и `collections` создайте файл `.env` (пример переменных окружения ниже).

### Переменные окружения (.env)
Для каждого сервиса необходим свой файл `.env`. Пример базовой конфигурации:

**Для `auth/.env`:**
```env
DATABASE_URL=sqlite:///./auth.db
SECRET_KEY=ваш_супер_секретный_ключ_для_jwt
```

**Для `catalog/.env`:**
```env
DATABASE_URL=sqlite:///./catalog.db
SECRET_KEY=ваш_супер_секретный_ключ_для_jwt
AUTH_SERVICE_URL=http://localhost:8001
```

**Для `collections/.env`:**
```env
DATABASE_URL=sqlite:///./collections.db
SECRET_KEY=ваш_супер_секретный_ключ_для_jwt
CATALOG_SERVICE_URL=http://localhost:8002
```

**Для `auction/.env`:**
```env
DATABASE_URL=sqlite:///./auction.db
SECRET_KEY=ваш_супер_секретный_ключ_для_jwt
AUTH_SERVICE_URL=http://localhost:8001
```

**Для `trade/.env`:**
```env
DATABASE_URL=sqlite:///./trade.db
SECRET_KEY=ваш_супер_секретный_ключ_для_jwt
CATALOG_SERVICE_URL=http://localhost:8002
AUTH_SERVICE_URL=http://localhost:8001
```

### Локальный запуск (без Docker)
Так как проект разбит на микросервисы, для полного запуска системы потребуется открыть 6 отдельных терминалов:

**Терминал 1 (Auth - Порт 8001)**
```bash
cd auth
uvicorn main:app --reload --port 8001
```

**Терминал 2 (Catalog - Порт 8002)**
```bash
cd catalog
uvicorn main:app --reload --port 8002
```

**Терминал 3 (Collections - Порт 8003)**
```bash
cd collections
uvicorn main:app --reload --port 8003
```

**Терминал 4 (Auction - Порт 8005)**
```bash
cd auction
uvicorn main:app --reload --port 8005
```

**Терминал 5 (Trade - Порт 8006)**
```bash
cd trade
uvicorn main:app --reload --port 8006
```

**Терминал 6 (Gateway - Порт 8000)**
```bash
cd gateway
uvicorn main:app --reload --port 8000
```

---

## API документация

Система использует автоматически генерируемую документацию OpenAPI (Swagger UI).

* **Главная точка входа (Gateway):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Прямой доступ к Auth:** [http://localhost:8001/docs](http://localhost:8001/docs)
* **Прямой доступ к Catalog:** [http://localhost:8002/docs](http://localhost:8002/docs)
* **Прямой доступ к Collections:** [http://localhost:8003/docs](http://localhost:8003/docs)
* **Прямой доступ к Auction:** [http://localhost:8005/docs](http://localhost:8005/docs)
* **Прямой доступ к Trade:** [http://localhost:8006/docs](http://localhost:8006/docs)


### Основные эндпоинты (через Gateway)

**Auth (`/auth/...`)**
* `POST /auth/register` — Регистрация нового пользователя.
* `POST /auth/login` — Авторизация и получение `access_token`.
* `GET /auth/me` — Получение информации о текущем пользователе.

**Catalog (`/catalog/...`)**
* **Справочники (CRUD):** `/categories/`, `/countries/`, `/materials/`, `/mints/`
* **Предметы коллекции:** 
  * `GET /catalog/items` — Получение списка монет и банкнот (с фильтрацией по типу, стране, году и т.д.).
  * `POST /catalog/items` — Создание предмета (монеты или банкноты, определяется полем `type`).
  * `GET /catalog/items/{item_id}` — Детали предмета.
  * `PUT /catalog/items/{item_id}` — Обновление предмета (только для автора).
  * `DELETE /catalog/items/{item_id}` — Удаление предмета (только для автора).

**Collections (`/collections/...`)**
* `GET /collections/` — Просмотр своей личной коллекции (с подтягиванием данных из Catalog).
* `POST /collections/` — Добавление предмета в свою коллекцию по `item_id`.
* `DELETE /collections/{collection_id}` — Удаление предмета из своей коллекции.

**Auction (`/auction/...`)**
* `POST /auction/lots` — Создание лота на аукцион.
* `GET /auction/lots` — Получение списка выставленных на аукцион предметов.
* `POST /auction/bids` — Создание ставки для предмета на аукционе.

**Trade (`/trade/...`)**
* `POST /trade/offers` — Создание предложения обмена.
* `GET /trade/offers/sent` — Получение списка отправленных предложений обмена.
* `GET /trade/offers/received` — Получение списка полученных предложений.
* `POST /trade/offers/{offer_id}/respond` — Ответ на предложение обмена.

---

## Как тестировать

### 1. Автоматизированные тесты (Pytest)
В проекте настроено тестирование с использованием `pytest`. Для запуска тестов выполните из корня микросервиса (при условии, что тесты находятся в соответствующих папках):

```bash
# Запуск всех тестов
pytest -m pytest -v

# Запустить тесты с измерением покрытия кода
coverage run -m pytest -v
coverage report -m / coverage html
```

### 2. Ручное тестирование через Swagger UI
Самый удобный способ проверить работоспособность системы — использовать интерфейс по адресу [http://localhost:8000/docs](http://localhost:8000/docs).

**Пошаговый сценарий:**
1. **Получите токен:** Перейдите в `POST /auth/login` -> *Try it out* -> Введите `{"username": "user2", "password": "123"}` -> *Execute*. Скопируйте полученный `access_token`.
2. **Авторизуйтесь:** Нажмите кнопку **Authorize** (🔒) в правом верхнем углу. Введите токен в формате: `<ваш_токен>` и нажмите Confirm.
3. **Создайте страну:** `POST /catalog/countries` -> `{"title": "Россия"}`. Вы получите объект с `id: 1`.
4. **Создайте монету:** `POST /catalog/items`:
   ```json
   {
     "type": "coin",
     "name": "10 рублей 2001",
     "country_id": 1,
     "denomination": 10,
     "currency": "RUB"
   }
   ```
5. **Добавьте в коллекцию:** `POST /collections/` -> `{"item_id": 1}`. 
6. **Проверьте коллекцию:** Выполните `GET /collections/`. В ответе придет ваш предмет вместе с вложенными данными из каталога.

---

## Контакты и поддержка
Над проектом работали студенты ПИН-33:

Патюков Семён - [https://github.com/Simon-Struggler]

Федотов Роман - [https://github.com/Rometei]

Вербицкий Александр - [https://github.com/SimSalobim]
