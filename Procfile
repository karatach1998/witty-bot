web: gunicorn web:app
worker: celery -A tasks.celery worker -c 2
