#!/bin/bash

# Команды для настройки БД в Docker

# 1. Подключиться к контейнеру PostgreSQL
# Для обычного запуска:
docker-compose exec db psql -U postgres

# Для Windows:
# docker-compose -f docker-compose.windows.yml exec db psql -U postgres

# 2. В psql выполнить следующие команды:

# Создать пользователя
CREATE USER circlemafia_user WITH PASSWORD 'kjhdsuiheuifbuwehfkisdh';

# Создать базу данных
CREATE DATABASE circlemafia;

# Дать права пользователю на базу данных
GRANT ALL PRIVILEGES ON DATABASE circlemafia TO circlemafia_user;

# Подключиться к базе данных
\c circlemafia

# Дать права на схему public
GRANT ALL ON SCHEMA public TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;

# Выйти из psql
\q

