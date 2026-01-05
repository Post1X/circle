#!/bin/bash

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-circlemafia_user}
DB_NAME=${DB_NAME:-circlemafia}
DB_PASS=${DB_PASS:-}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}

echo "Granting permissions to user $DB_USER on database $DB_NAME..."

# Попробуем подключиться как postgres, если есть пароль
if [ -n "$POSTGRES_PASSWORD" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
  psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d "$DB_NAME" <<EOF
-- Выдать права на схему public пользователю
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- Если схема public не существует, создать её
CREATE SCHEMA IF NOT EXISTS public;
EOF
else
  echo "POSTGRES_PASSWORD not set. Trying to connect as current user..."
  echo "Please run these commands manually as postgres user:"
  echo ""
  echo "psql -U postgres -d $DB_NAME <<EOF"
  echo "GRANT ALL ON SCHEMA public TO $DB_USER;"
  echo "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
  echo "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
  echo "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
  echo "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"
  echo "CREATE SCHEMA IF NOT EXISTS public;"
  echo "EOF"
  exit 1
fi

echo "Permissions granted successfully!"


