# kwispel

*kwispel* is a Django app to manage quiz results and show rankings.

## Features

 * Enter teams and rounds by name using the standard Django admin interface
 * Each round can have its own max score
 * Only rounds that have scores for all teams count in the ranking
 * i18n supported with English and Dutch to start with
 * Data is stored in an Sqlite3 db
 * The included nginx container will make sure static files are correctly served.
 * The application itself is served by [Gunicorn](https://gunicorn.org).

## Status

Version 2.0 of this app is meant to be running in a Docker compose environment.
Considering the status a beta for now.

## Requirements

* Docker compose

## Startup

Run `docker compose -f docker-compose.prod.yml up -d` and the application should become available on `http://localhost:1337/`.
This setup provides a production-ready experience.

For development purposes, instead of using the `docker-compose.prod.yml` file, you can use the regular `docker-compose.yml` file which will serve the application on `http://localhost:8000/`.

To create an admin user, go into the running container and `./manage.py createsuperuser`.

## TODO

* You'll need to provide `.env.dev` and/or `.env.prod` in the root of this project before starting Docker. These files need to contain the following values

```sh
DEBUG=0 # 1 for dev
SECRET_KEY= # to fill in
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1] # good default
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:1337 # should contain actual URL used to access the application
```

* The docker setup still lacks copying the static files from this repository.
* The SQLITE database should be created and configured - or kept intact.
* An initial admin user should be made.

## Background

This is an implementation of kwispel using Docker for easy deployment, 
based on information gathered from https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

---
---
---

The following should be no longer needed. Making sure before removing here.

After installation, run the following commands:
 * django-admin compilemessages
 * manage.py makemigrations
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
