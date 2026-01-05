# Docker для NestJS версии

## Настройка для работы с Docker

База данных PostgreSQL запускается в Docker контейнере. В `docker-compose.yml` сервис называется `db`.

### Переменные окружения для Docker

В файле `.env` для работы с Docker используйте:

```env
DB_HOST=db
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_db_user
DB_PASS=your_db_password
```

**Важно**: `DB_HOST=db` - это имя сервиса в docker-compose.yml, не `localhost`!

### Для локальной разработки (без Docker)

Если вы запускаете NestJS локально, а база данных в Docker:

```env
DB_HOST=localhost
DB_PORT=5432
```

### Запуск с Docker

```bash
# Запустить только базу данных и Redis
docker-compose up -d db redis

# Затем запустить NestJS приложение
npm run start:dev
```

### Проверка подключения

```bash
# Проверить статус БД
docker-compose ps db

# Посмотреть логи БД
docker-compose logs db

# Подключиться к БД через psql
docker-compose exec db psql -U ${DB_USER} -d ${DB_NAME}
```

## Миграции

Проект использует существующие миграции Alembic из Python версии. TypeORM настроен с `synchronize: false`, поэтому схема БД управляется через Alembic миграции.

Если нужно создать новые миграции TypeORM:

```bash
# Применить миграции
npm run migration:run
```


