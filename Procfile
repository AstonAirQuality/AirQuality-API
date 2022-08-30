web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
release: alembic revision --autogenerate -m "New Migration" && alembic upgrade head
worker: celery -A tasks worker --loglevel=INFO