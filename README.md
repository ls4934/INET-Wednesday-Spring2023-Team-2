# Show Of Hands

[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/INET-Wednesday-Spring2023-Team-2.svg?branch=develop)](https://app.travis-ci.com/gcivil-nyu-org/INET-Wednesday-Spring2023-Team-2)
[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/INET-Wednesday-Spring2023-Team-2/badge.svg?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/INET-Wednesday-Spring2023-Team-2?branch=develop)


Backend setup (Ideally use Python 3.8 +)
```
$ python3 -m venv python_venv
$ source python_venv/bin/activate
$ python -m pip install -r requirements.txt
```
Configure DB (You will need to have installed Postgres 15)
```
$ sudo su
$ sudo -u postgres psql
$ CREATE DATABASE <db_name>;
$ CREATE USER <username> WITH PASSWORD <password>;
$ GRANT ALL PRIVILEGES ON DATABASE <db_name> TO <username>;
$ ALTER DATABASE <db_name> OWNER TO <username>;
```
Add Credentials to .env
```
$ touch showofhands/.env
$ echo "POSTGRES_DB_NAME='<db_name>'" >> showofhands/.env
$ echo "POSTGRES_USER_NAME='<username>'" >> showofhands/.env
$ echo "POSTGRES_PASSWORD='<password>'" >> showofhands/.env
$ echo "POSTGRES_HOST='localhost'" >> showofhands/.env
$ echo "POSTGRES_PORT='5432'" >> showofhands/.env
$ echo "SECRET_KEY='<any_unique_set_of_characters>'" >> showofhands/.env
```
Set up SMTP for Email Verifications (You will need to add app in your gmail settings to obtain host password)
```
$ echo "EMAIL_HOST='smtp.gmail.com'" >> showofhands/.env
$ echo "EMAIL_HOST_USER='<email>'" >> showofhands/.env
$ echo "EMAIL_HOST_PASSWORD='<app_password>'" >> showofhands/.env
$ echo "EMAIL_PORT=587" >> showofhands/.env
```
Migrate Models
```
$ python manage.py makemigrations
$ python manage.py migrate
```
Create a superuser
```
$ python manage.py createsuperuser
```
Runserver
```
$ python manage.py runserver
```