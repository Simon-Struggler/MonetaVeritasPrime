FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей (включая curl для healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Команда будет переопределена в docker-compose (указывается с нужным портом)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]