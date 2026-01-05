#!/bin/sh
echo "Waiting for database to be ready..."
sleep 10

echo "Running Alembic migrations..."
alembic upgrade head

echo "Migrations completed successfully!"
