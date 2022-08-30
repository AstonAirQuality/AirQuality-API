web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
worker: celery -A tasks worker --loglevel=INFO