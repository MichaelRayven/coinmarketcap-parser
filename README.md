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
uv run python -m src.app.main
```

Запуск ифраструктуры:
```bash
docker-compose -f infra/docker/docker-compose.yml up -d --build
```
