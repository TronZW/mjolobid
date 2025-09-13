web: gunicorn mjolobid.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A mjolobid worker --loglevel=info
