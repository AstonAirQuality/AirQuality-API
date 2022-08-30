web: gunicorn --workers=3 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 main:app
worker: celery -A tasks worker --loglevel=INFO