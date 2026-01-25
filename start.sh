#!/bin/bash
python manage.py migrate --noinput
gunicorn mimi_platform.wsgi:application --bind 0.0.0.0:$PORT
