# Настройка базы данных в Docker

## Вариант 1: Через docker-compose exec (рекомендуется)

### Для обычного запуска (порт 5432):

```bash
# 1. Подключиться к контейнеру и выполнить команды
docker-compose exec db psql -U postgres -c "CREATE USER circlemafia_user WITH PASSWORD 'kjhdsuiheuifbuwehfkisdh';"
docker-compose exec db psql -U postgres -c "CREATE DATABASE circlemafia;"
docker-compose exec db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE circlemafia TO circlemafia_user;"
docker-compose exec db psql -U postgres -d circlemafia -c "GRANT ALL ON SCHEMA public TO circlemafia_user;"
docker-compose exec db psql -U postgres -d circlemafia -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;"
docker-compose exec db psql -U postgres -d circlemafia -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;"
```

### Для Windows (порт 5434):

```bash
# 1. Подключиться к контейнеру и выполнить команды
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -c "CREATE USER circlemafia_user WITH PASSWORD 'kjhdsuiheuifbuwehfkisdh';"
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -c "CREATE DATABASE circlemafia;"
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE circlemafia TO circlemafia_user;"
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -d circlemafia -c "GRANT ALL ON SCHEMA public TO circlemafia_user;"
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -d circlemafia -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;"
docker-compose -f docker-compose.windows.yml exec db psql -U postgres -d circlemafia -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;"
```

## Вариант 2: Интерактивный режим psql

### Для обычного запуска:

```bash
# 1. Подключиться к контейнеру
docker-compose exec db psql -U postgres

# 2. В psql выполнить:
CREATE USER circlemafia_user WITH PASSWORD 'kjhdsuiheuifbuwehfkisdh';
CREATE DATABASE circlemafia;
GRANT ALL PRIVILEGES ON DATABASE circlemafia TO circlemafia_user;
\c circlemafia
GRANT ALL ON SCHEMA public TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;
\q
```

### Для Windows:

```bash
# 1. Подключиться к контейнеру
docker-compose -f docker-compose.windows.yml exec db psql -U postgres

# 2. В psql выполнить те же команды, что выше
```

## Вариант 3: Через SQL файл

### Для обычного запуска:

```bash
# Создать файл setup_db_commands.sql с командами (уже создан)
docker-compose exec -T db psql -U postgres < setup_db_commands.sql
```

### Для Windows:

```bash
docker-compose -f docker-compose.windows.yml exec -T db psql -U postgres < setup_db_commands.sql
```

## Проверка подключения

После настройки проверьте подключение:

### Для обычного запуска:

```bash
docker-compose exec db psql -U circlemafia_user -d circlemafia -c "SELECT version();"
```

### Для Windows:

```bash
docker-compose -f docker-compose.windows.yml exec db psql -U circlemafia_user -d circlemafia -c "SELECT version();"
```

## Если пользователь уже существует

Если нужно пересоздать пользователя:

```bash
# Удалить пользователя и базу данных (ОСТОРОЖНО!)
docker-compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS circlemafia;"
docker-compose exec db psql -U postgres -c "DROP USER IF EXISTS circlemafia_user;"

# Затем выполнить команды создания заново
```

## Важно

1. Убедитесь, что Docker контейнеры запущены:
   ```bash
   docker-compose ps
   # или
   docker-compose -f docker-compose.windows.yml ps
   ```

2. После настройки БД примените миграции:
   ```bash
   docker-compose up alembic
   ```

3. Проверьте `.env` файл - он должен содержать:
   ```env
   DB_NAME=circlemafia
   DB_USER=circlemafia_user
   DB_PASS=kjhdsuiheuifbuwehfkisdh
   DB_HOST=localhost
   DB_PORT=5432
   ```

