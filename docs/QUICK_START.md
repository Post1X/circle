# Быстрый запуск NestJS версии

## Вариант 1: Локальный запуск NestJS + Docker для БД/Redis (рекомендуется для разработки)

### 1. Установите зависимости

```bash
npm install
```

### 2. Настройте .env файл

**Для обычного запуска (`npm run dev`):**
```env
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Для Windows (`npm run dev:windows`) - если порт 5432 занят:**
```env
DB_HOST=localhost
DB_PORT=5434
REDIS_HOST=localhost
REDIS_PORT=6381
```

(Порты проброшены из Docker на хост)

### 3. Запустите БД и Redis в Docker

**Обычный запуск (порты 5432, 6379):**
```bash
# Запустить только БД и Redis
docker-compose up -d db redis

# Проверить статус
docker-compose ps
```

**Для Windows (порты 5434, 6381) - если 5432 занят:**
```bash
# Запустить с альтернативными портами
docker-compose -f docker-compose.windows.yml up -d db redis
```

### 4. Примените миграции (если БД новая)

**Если БД уже существует и миграции применены - пропустите этот шаг.**

Если БД новая, используйте существующие Alembic миграции:

```bash
# Применить миграции через Alembic (Python)
docker-compose up alembic
```

**Примечание:** TypeORM настроен с `synchronize: false`, поэтому схема БД управляется через миграции. 
Для новых миграций можно использовать TypeORM:
```bash
npm run migration:run
```

### 5. Запустите NestJS приложение

**Одной командой (рекомендуется):**

```bash
# Обычный запуск (порты 5432, 6379)
npm run dev

# Для Windows (порты 5433, 6380) - если 5432 занят
npm run dev:windows
```

**Важно:** Перед `npm run dev:windows` убедитесь, что в `.env` указаны правильные порты:
- `DB_PORT=5434`
- `REDIS_PORT=6381`

**Или по отдельности:**

```bash
# Режим разработки (с автоперезапуском)
npm run start:dev

# Или продакшен
npm run build
npm run start:prod
```

**Дополнительные команды:**

```bash
# Остановить Docker контейнеры (обычные)
npm run docker:down

# Остановить Docker контейнеры (Windows версия)
npm run docker:down:windows

# Посмотреть логи Docker (обычные)
npm run docker:logs

# Посмотреть логи Docker (Windows версия)
npm run docker:logs:windows
```

Приложение будет доступно на `http://localhost:8000`

---

## Вариант 2: Все в Docker (для продакшена)

Для этого нужно будет создать Dockerfile для NestJS и обновить docker-compose.yml, но это можно сделать позже.

---

## Проверка работы

```bash
# Проверить health endpoint
curl http://localhost:8000/api/health

# Проверить активных игроков
curl http://localhost:8000/api/active-players
```

## Остановка

```bash
# Остановить NestJS: Ctrl+C

# Остановить Docker контейнеры
docker-compose down
```

