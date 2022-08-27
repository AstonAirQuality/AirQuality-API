import time

# enviroment variables dependacies
from os import environ as env

from celery import Celery
from dotenv import load_dotenv

# from celery.schedules import crontab
# from celery.task import periodic_task


load_dotenv()

# _name?
celery = Celery(__name__)
celery.conf.broker_url = env["CELERY_BROKER_URL"]
celery.conf.result_backend = env["CELERY_RESULT_BACKEND"]


@celery.task(name="tasks.add")
def add(x, y):
    time.sleep(5)
    return x + y
