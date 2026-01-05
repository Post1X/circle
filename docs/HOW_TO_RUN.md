# Как запустить сервер

## Способ 1: Через Docker Compose (рекомендуется)

Это основной способ запуска для продакшена и разработки.

### Предварительные требования:
1. Установлен Docker и Docker Compose
2. Заполнен файл `.env` со всеми необходимыми переменными
3. Файл `.env` находится в корне проекта

### Запуск всех сервисов:

```bash
# Запустить все сервисы (включая БД, Redis, миграции, Celery)
docker-compose up -d

# Или с выводом логов в консоль
docker-compose up
```

### Что запускается:

1. **alembic** - выполняет миграции базы данных (запускается первым)
2. **db** (PostgreSQL) - база данных
3. **redis** - Redis для кеша и Celery
4. **web** - основной веб-сервер FastAPI (порт 8000)
5. **celery_worker** - воркер для фоновых задач
6. **celery_beat** - планировщик задач Celery

### Проверка статуса:

```bash
# Проверить статус всех контейнеров
docker-compose ps

# Посмотреть логи веб-сервера
docker-compose logs -f web

# Посмотреть логи всех сервисов
docker-compose logs -f
```

### Остановка:

```bash
# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes (БД будет очищена!)
docker-compose down -v
```

### Перезапуск:

```bash
# Перезапустить все сервисы
docker-compose restart

# Перезапустить только веб-сервер
docker-compose restart web
```

### Пересборка после изменений:

```bash
# Пересобрать образы и перезапустить
docker-compose up -d --build

# Пересобрать только веб-сервер
docker-compose up -d --build web
```

---

## Способ 2: Локальный запуск (для разработки)

Для локального запуска без Docker нужны:
- Python 3.13+
- PostgreSQL (запущенный локально или удаленно)
- Redis (запущенный локально или удаленно)

### Установка зависимостей:

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Запуск:

```bash
# Убедитесь, что .env файл заполнен и указывает на локальные БД и Redis
python main.py
```

Сервер запустится на `http://localhost:8000`

**Важно:** При локальном запуске нужно вручную запустить:
- PostgreSQL
- Redis
- Выполнить миграции: `alembic upgrade head`
- Celery worker (если нужны фоновые задачи)

---

## Проверка работоспособности

После запуска проверьте:

1. **Health check:**
   ```bash
   curl http://localhost:8000/api/health
   # Или в браузере: http://localhost:8000/api/health
   ```

2. **Активные игроки:**
   ```bash
   curl http://localhost:8000/api/active-players
   ```

3. **Документация API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## Порты

- **8000** - Веб-сервер FastAPI
- **5432** - PostgreSQL (только для локального доступа, отключить на проде)
- **6379** - Redis (только для локального доступа, отключить на проде)

---

## Логи и отладка

### Просмотр логов:

```bash
# Все сервисы
docker-compose logs -f

# Только веб-сервер
docker-compose logs -f web

# Только база данных
docker-compose logs -f db

# Только Redis
docker-compose logs -f redis

# Celery worker
docker-compose logs -f celery_worker

# Celery beat
docker-compose logs -f celery_beat
```

### Режим разработки:

В `.env` установите:
```env
mode=test
```

Это включит:
- Автоперезапуск при изменении кода (reload=True)
- Более подробные логи

---

## Структура запуска

При запуске через `docker-compose up` сервисы запускаются в следующем порядке:

1. **db** (PostgreSQL) - ждем пока станет healthy
2. **redis** - ждем пока станет healthy
3. **alembic** - выполняет миграции (зависит от db)
4. **web** - запускается после успешных миграций
5. **celery_worker** - запускается после миграций
6. **celery_beat** - запускается после миграций

---

## Решение проблем

### Проблема: Контейнер не запускается

```bash
# Проверить логи
docker-compose logs web

# Проверить статус
docker-compose ps

# Пересобрать образ
docker-compose build --no-cache web
```

### Проблема: Ошибка подключения к БД

1. Проверьте переменные в `.env`:
   - `DB_HOST=db` (для Docker) или `DB_HOST=localhost` (для локального)
   - `DB_PORT=5432`
   - `DB_NAME`, `DB_USER`, `DB_PASS`

2. Проверьте, что БД запущена:
   ```bash
   docker-compose ps db
   ```

### Проблема: Ошибка миграций

```bash
# Запустить миграции вручную
docker-compose run --rm alembic alembic upgrade head

# Или пересоздать БД (ВНИМАНИЕ: удалит все данные!)
docker-compose down -v
docker-compose up -d
```

### Проблема: Порт 8000 занят

Измените порт в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Внешний порт:внутренний порт
```

---

## Команды для разработки

```bash
# Запустить только БД и Redis (без веб-сервера)
docker-compose up -d db redis

# Запустить веб-сервер локально
python main.py

# Выполнить миграции
docker-compose run --rm alembic alembic upgrade head

# Создать новую миграцию
docker-compose run --rm alembic alembic revision --autogenerate -m "описание"

# Зайти в контейнер веб-сервера
docker-compose exec web bash

# Выполнить команду в контейнере
docker-compose exec web python generate_mnemonic.py
```

---

## Продакшен

Для продакшена:

1. Установите `mode=prod` в `.env`
2. Отключите проброс портов БД и Redis в `docker-compose.yml`:
   ```yaml
   # db:
   #   ports:
   #     - "5432:5432"  # Закомментировать
   
   # redis:
   #   ports:
   #     - "6379:6379"  # Закомментировать
   ```
3. Используйте reverse proxy (nginx) перед веб-сервером
4. Настройте SSL/TLS сертификаты
5. Используйте секреты из безопасного хранилища вместо `.env` файла



