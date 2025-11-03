#!/bin/sh

# makemessages and makemigrations should be run before starting the server
# so that any changes are included in the container image.
# This is especially important for makemigrations, as migrations should be
# part of version control and not generated at runtime.

# django-admin makemessages -a -l nl -e html,py
django-admin compilemessages
# python manage.py makemigrations # makemigrations should have its result in version control
python manage.py migrate
python manage.py collectstatic --noinput
# TODO: create a superuser

exec "$@"
