# Что осталось на Python

## ✅ Полностью перенесено в NestJS:
- ✅ Все handlers (API endpoints) → NestJS контроллеры
- ✅ Все сервисы (auth, withdrawal, tron_monitor, rooms) → NestJS сервисы
- ✅ Игровая логика (game/) → src/game/
- ✅ База данных модели (bd/models.py) → TypeORM entities
- ✅ База данных actions → NestJS сервисы
- ✅ Инициализация горячего кошелька → `src/services/hot-wallet-init/`

## 📝 Что осталось на Python (и нужно оставить):

### 1. **Миграции базы данных** (обязательно оставить)
- `migrations/` - Alembic миграции для БД
- `alembic.ini` - конфигурация Alembic
- `run_migrations.sh` - скрипт запуска миграций
- Используются для управления схемой БД (TypeORM использует существующую схему)

### 2. **Утилиты и скрипты** (можно оставить)
- `generate_mnemonic.py` - генерация мнемоники
- `generate_all_secrets.py` - генерация секретов
- `validate_env.py` - валидация .env файла
- `reboot_bd.py` - перезапуск БД
- `test/testcleint.py` - тестовый клиент
- `fix_tabs.py` - утилита для исправления табов

### 3. **Python FastAPI сервер** (можно оставить как резервную версию)
- `main.py` - главный файл FastAPI приложения
- `handlers/` - все обработчики (уже перенесены в NestJS, но файлы остались)
- `servises/` - сервисы (большинство перенесено, но файлы остались)
- `bd/` - модели и actions (перенесено в TypeORM, но файлы остались)
- `game/` - игровая логика (перенесена, но файлы остались)
- `schemas/` - Pydantic схемы (перенесены в DTO, но файлы остались)

### 4. **Celery для фоновых задач** (можно оставить или удалить)
- `celery_config.py` - конфигурация Celery
- `servises/player_counter.py` - использует Celery для обновления счетчика игроков
- `docker-compose.yml` - содержит celery_worker и celery_beat
- **Примечание:** В NestJS уже есть TronMonitorService и WithdrawalProcessorService, которые заменяют Celery задачи

### 5. **Docker конфигурация для Python** (можно оставить)
- `Dockerfile` - для Python версии
- `docker-compose.yml` - содержит сервисы web, alembic, celery_worker, celery_beat

## 📋 Итог:

**На Python осталось:**
1. ✅ Миграции БД (Alembic) - **нужно оставить**
2. ✅ Утилиты и скрипты - **можно оставить**
3. ✅ Python FastAPI версия - **можно оставить как резервную или удалить**
4. ✅ Celery - **можно удалить, так как заменено на NestJS сервисы**

**В NestJS есть:**
- ✅ Все API endpoints
- ✅ Вся игровая логика
- ✅ Все сервисы (включая фоновые)
- ✅ Инициализация горячего кошелька
- ✅ Мониторинг Tron депозитов
- ✅ Обработка выводов

**Рекомендация:** Python версию можно оставить как резервную или удалить, если уверены в NestJS версии. Миграции обязательно оставить.
