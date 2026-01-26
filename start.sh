#!/bin/sh
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
gunicorn mimi_platform.wsgi:application --bind 0.0.0.0:$PORT
