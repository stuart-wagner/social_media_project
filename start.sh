#!/bin/bash

# Run migrations
python manage.py migrate

# Start gunicorn
gunicorn learning_log.wsgi:application

