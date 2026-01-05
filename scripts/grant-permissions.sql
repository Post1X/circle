-- Выдать права на схему public пользователю
GRANT ALL ON SCHEMA public TO circlemafia_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO circlemafia_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO circlemafia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO circlemafia_user;

-- Если схема public не существует, создать её
CREATE SCHEMA IF NOT EXISTS public;


