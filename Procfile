web: gunicorn wsgi:app
worker: celery -A tasks.celery worker -c 4
