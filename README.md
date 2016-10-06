# kwispel
kwispel is a Django app to manage quiz results and show rankings

## Features
 * Enter teams and rounds by name using the standard Django admin interface
 * Each round can have its own max score
 * Data is stored in sqlite3 db
 * Only rounds that have scores for each team count in the ranking
 * i18n supported with English and Dutch to start with

## Status
Early development

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
 * manage.py createsuperuser
 * manage.py runserver
