# CoinMarketCap Parser

Парсер для сбора данных с CoinMarketCap.

## Локальная разработка

Установка зависимостей:
```bash
uv sync
```

Установка хуков:
```bash
uv run prek install
```

Запуск:
```bash
uv run fastapi dev src/app/main.py
```

Запуск ифраструктуры:
```bash
docker-compose -f infra/docker/docker-compose.yml up -d --build
```

Миграции:
```bash
uv run alembic upgrade head
```

Создание миграции:
```bash
uv run alembic revision --autogenerate -m "migration_name"
```
