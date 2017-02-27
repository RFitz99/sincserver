# sincserver

[![Build status](https://travis-ci.org/sdob/sincserver.svg?branch=master)](https://travis-ci.org/sdob/sincserver/branches)
[![Coverage Status](https://coveralls.io/repos/github/sdob/sincserver/badge.svg?branch=master)](https://coveralls.io/github/sdob/sincserver?branch=master)
[![Code Climate](https://codeclimate.com/github/sdob/sincserver/badges/gpa.svg)](https://codeclimate.com/github/sdob/sincserver)

SINC backend.

## Requirements

1. Python 3.4 or above.
1. PostgreSQL 9.5.4 or above. (SINC will use Postgres in production and has
`psycopg2` in its dependencies, although you're free to use SQLite in development.)

## Getting started

1. Clone this repo: `git clone https://github.com/sdob/sincserver.git && cd sincserver`
1. Install dependencies: `pip install -r requirements.txt` (preferably in a virtualenv).
1. Create your database.
1. Rename `env.example` to `.env` and edit the values of the
`SECRET_KEY` and `DATABASE_URL` environment variables.
1. Apply the database migrations: `python manage.py migrate`
1. Create a superuser: `python manage.py createsuperuser`  
   This will prompt you for a username (type in anything you want here; SINC uses
   the db's primary key as the username), an email address, and first and last names.
1. (Optional) Run the tests: `python manage.py test`
1. Run the development server: `python manage.py runserver`

This will start the dev server running on [http://localhost:8000/](http://localhost:8000/).
