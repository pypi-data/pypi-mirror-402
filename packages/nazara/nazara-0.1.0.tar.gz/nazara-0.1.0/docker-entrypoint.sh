#!/bin/bash
set -e

MODE="$1"

wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    while ! nc -z ${POSTGRES_HOST:-localhost} ${POSTGRES_PORT:-5432}; do
        sleep 1
    done
    echo "PostgreSQL ready!"
}

if [ "$MODE" = 'web' ]; then
    wait_for_postgres
    echo "Running migrations..."
    uv run python manage.py migrate --noinput
    if [ "$DEBUG" = "1" ]; then
        echo "Starting Django development server..."
        exec uv run python manage.py runserver 0.0.0.0:8000
    else
        echo "Starting Gunicorn production server..."
        exec uv run gunicorn sandbox.wsgi:application -b 0.0.0.0:8000 --workers 4
    fi

elif [ "$MODE" = 'celery-worker' ]; then
    wait_for_postgres
    echo "Starting Celery worker..."
    exec uv run celery -A sandbox worker -l INFO

elif [ "$MODE" = 'celery-beat' ]; then
    wait_for_postgres
    echo "Starting Celery beat scheduler..."
    exec uv run celery -A sandbox beat -l INFO \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler

elif [ "$MODE" = 'migrate' ]; then
    wait_for_postgres
    echo "Running database migrations..."
    exec uv run python manage.py migrate --noinput

elif [ "$MODE" = 'createsuperuser' ]; then
    wait_for_postgres
    echo "Creating superuser..."
    exec uv run python manage.py createsuperuser

elif [ "$MODE" = 'shell' ]; then
    wait_for_postgres
    echo "Starting Django shell..."
    exec uv run python manage.py shell

else
    # Pass through any other command
    exec "$@"
fi
