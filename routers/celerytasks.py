# dependancies:
# import datetime as dt  # TODO REMOVE
# from typing import Tuple  # TODO REMOVE

# from tasks import scheduled_upsert_sensorSummary
import tasks as CeleryWorker

# from tasks import add, read_sensor_data, scheduled_upsert_sensorSummary
# error handling
from celery.result import AsyncResult
from fastapi import APIRouter, Body, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

celeryTasksRouter = APIRouter()

# TODO add leap year check
dateRegex = "\s+(?:0[1-9]|[12][0-9]|3[01])[-/.](?:0[1-9]|1[012])[-/.](?:19\d{2}|20\d{2}|2100)\b"


# {"x": 100, "y": 123}
@celeryTasksRouter.post("/ex1")
def run_task(data=Body(...)):
    x = data["x"]
    y = data["y"]
    task = CeleryWorker.add.delay(x, y)
    return {"result": task.get()}


@celeryTasksRouter.get("/task/{task_id}")
def get_task_result(task_id: str):
    res = AsyncResult(task_id)
    return {"task_id": task_id, "task_status": res.status, "task_result": res.result}


# TODO validate query params here rather than in celery task
@celeryTasksRouter.put("/api/upsert-scheduled-ingest-active-sensors/{start}/{end}")
def upsert_scheduled_ingest_active_sensors(start: str = Query(regex=dateRegex), end: str = Query(regex=dateRegex)):
    """create a scheduled ingest task of the active sensors.
    params: must be valid date string e.g. 20-08-2022,26-08-2022"""

    # route task to celery
    task = CeleryWorker.scheduled_upsert_sensorSummary.delay(start, end)

    return {"task_id": task.id}


# TODO validate query params here rather than in celery task
@celeryTasksRouter.get("/api/read-sensorSummaries/{start}/{end}/{raw_data}")
def get_sensorSummaries(
    start: str,
    end: str,
    raw_data: bool,
    geom_type: str | None = None,
    geom: str | None = None,
    sensor_ids: list[int] | None = Query(None),
):
    """create a scheduled ingest task of the active sensors.
    params: must be valid date string e.g. 20-08-2022,26-08-2022"""

    # route task to celery
    task = CeleryWorker.read_sensor_data.delay(start, end, raw_data, geom_type, geom, sensor_ids)

    return {"task_id": task.id}


# # helper functions
# def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:
#     try:
#         startDate = dt.datetime.strptime(start, "%Y-%m-%d")
#         endDate = dt.datetime.strptime(end, "%Y-%m-%d")

#     except (ValueError, TypeError):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format")

#     return startDate, endDate
