web: gunicorn web:app
worker: celery -A tasks.celery worker -c 2 --without-heartbeat --without-gossip --without-mingle
