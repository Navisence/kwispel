#!/bin/sh

# Check whether the database exists, and create it if not
if [ ! -f /data/db.sqlite3 ]; then
    echo "Creating initial database"
    python manage.py migrate
    # Create an initial superuser
    python manage.py createsuperuser --noinput --username admin
    # Collect static files
    python manage.py collectstatic --noinput
fi

# python manage.py migrate

exec "$@"
