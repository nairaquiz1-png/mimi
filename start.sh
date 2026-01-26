#!/bin/bash
pip install -r requirements.txt
python manage.py migrate
gunicorn --bind 0.0.0.0:$PORT mimi_platform.wsgi:application
