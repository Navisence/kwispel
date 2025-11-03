# Kwispel

*Kwispel* is a Django app to manage quiz results and show rankings.

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

## Translations

For translating the app into other languages, it is recommended to follow [the instructions for translating from the Django Manual]
(https://docs.djangoproject.com/en/5.2/topics/i18n/translation/#localization-how-to-create-language-files)

## TODO

* You'll need to provide `.env.dev` and/or `.env.prod` in the root of this project before starting Docker. These files need to contain the following values:

```sh
DEBUG=0 # 1 for dev
SECRET_KEY= # to fill in
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1] # good default
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:1337 # should contain actual URL used to access the application
```

* An initial admin user should be made, or instructions should be given.
* Suggestions for SSL handling in front of this app can be added.

## Background

This is an implementation of kwispel using Docker for easy deployment, 
based on information gathered from https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
