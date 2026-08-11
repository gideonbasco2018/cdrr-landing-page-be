#!/bin/sh
set -e

echo "Waiting for database at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
until python -c "
import socket, os, sys
host = os.getenv('POSTGRES_HOST', 'db')
port = int(os.getenv('POSTGRES_PORT', '5432'))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((host, port))
    s.close()
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "Database is up."

echo "Running migrations (alembic upgrade head)..."
alembic upgrade head

echo "Starting FastAPI (uvicorn)..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
