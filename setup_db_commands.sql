-- Команды для выполнения в psql внутри Docker контейнера

-- Создать пользователя
CREATE USER circlemafia_user WITH PASSWORD 'kjhdsuiheuifbuwehfkisdh';

-- Создать базу данных
CREATE DATABASE circlemafia;

-- Дать права пользователю на базу данных
GRANT ALL PRIVILEGES ON DATABASE circlemafia TO circlemafia_user;

-- Подключиться к базе данных
\c circlemafia

-- Дать права на схему public
GRANT ALL ON SCHEMA public TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;

