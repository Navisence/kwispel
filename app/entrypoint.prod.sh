#!/bin/sh

django-admin compilemessages

# Check whether the database exists, and create it if not
if [ ! -f /home/app/web/data/db.sqlite3 ]; then
    echo "Creating initial database"
    python manage.py migrate
    # Create an initial superuser
#    python manage.py createsuperuser --noinput
    # Collect static files
    python manage.py collectstatic --noinput
fi

exec "$@"
