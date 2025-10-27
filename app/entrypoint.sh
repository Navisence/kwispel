#!/bin/sh

django-admin compilemessages
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
