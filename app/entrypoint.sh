#!/bin/sh

django-admin makemessages -a -l nl -e html,py
django-admin compilemessages
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
