#!/bin/sh
set -e

: "${DJANGO_ENV:=development}"
: "${DJANGO_SUPERUSER_USERNAME:=admin}"
: "${DJANGO_SUPERUSER_EMAIL:=admin@example.com}"
: "${DJANGO_SUPERUSER_PASSWORD:=changetheadminpassword}"

echo "Environment: $DJANGO_ENV"

# makemessages and makemigrations should be run before starting the server
# so that any changes are included in the container image.
# This is especially important for makemigrations, as migrations should be
# part of version control and not generated at runtime.
# For makemessages, its result is further completed with translations and is
# also part of revision control.

# migration files are created with makemigrations. This command should have
# its result in version control.
# python manage.py makemigrations
# Apply migrations to the database, creating it if necessary
python manage.py migrate --noinput

# translation files are created/updated with makemessages. These files should be
# part of version control.
# django-admin makemessages -l nl -e html,py
django-admin compilemessages

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Ensuring superuser exists..."
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
if not User.objects.filter(username=username).exists():
    print(f"Creating superuser {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"Superuser {username} already exists.")
EOF

exec "$@"
