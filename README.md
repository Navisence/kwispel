# kwispel
*kwispel* is a Django app to manage quiz results and show rankings

## Features
 * Enter teams and rounds by name using the standard Django admin interface
 * Each round can have its own max score
 * Data is stored in sqlite3 db
 * Only rounds that have scores for each team count in the ranking
 * i18n supported with English and Dutch to start with

## Status
Usable if you're not afraid of some manual configuration (see below).

## Requirements
 * python3
 * django
 * django-bootstrap3
 * numpy
 * matplotlib

## Startup
After installation, run the following commands:
 * django-admin compilemessages
 * manage.py migrate
 * manage.py collectstatic
 * manage.py createsuperuser
 * manage.py runserver

## Static files
To serve static files directly from nginx, add a snippet like the following
to the nginx server configuration.

```
location /static {
    alias /path/to/static;
}
```

## Production settings
Check the kwispel/settings.py file and add the hostname(s) that will be used
to access the site to the ALLOWED\_HOSTS list.

The SECURE\_PROXY\_SSL\_HEADER is needed if you want to forward traffic from e.g.
an nginx instance that serves as SSL termination.

## Startup using uwsgi
Instead of the last step before (`manage.py runserver`), run
uwsgi --ini kwispel\_uwsgi.ini
Read more on Django+uwsgi+Nginx on https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html

