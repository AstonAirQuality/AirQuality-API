import datetime as dt
import json
import time
from json.decoder import JSONDecodeError

# enviroment variables dependacies
from os import environ as env
from typing import Tuple

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder  # encode model to json

from api_wrappers.plume_api_wrapper import PlumeWrapper
from api_wrappers.Sensor_DTO import SensorDTO
from celeryWrapper import CeleryWrapper

# sensor summary
from core.schema import Sensor as SchemaSensor
from core.schema import SensorSummary as SchemaSensorSummary
from errorLogging import check_log, clean_log, write_json
from routers.sensors import (
    get_active_sensors,
    sensor_id_from_lookup_id,
    set_last_updated,
)
from routers.sensorSummaries import get_sensorSummaries, upsert_sensorSummary

load_dotenv()

# _name?
celeryapp = Celery(__name__)
celeryapp.conf.broker_url = env["CELERY_BROKER_URL"]
celeryapp.conf.result_backend = env["CELERY_RESULT_BACKEND"]
celeryapp.conf.update(result_expires=3600, enable_utc=True, timezone="UTC")
# TODO add retries and timeouts

# TODO delete this function
@celeryapp.task(name="tasks.add")
def add(x, y):
    # time.sleep(5)
    return x + y


@celeryapp.task(name="tasks.read_sensor_data", serializer="json")
def read_sensor_data(start: str, end: str, rawdata: bool, geom_type: str, geom: str, sensor_ids: list[int]):
    """reads sensor data from sensor summaries and encodes it to json"""
    result = get_sensorSummaries(start, end, rawdata, geom_type, geom, sensor_ids)
    return jsonable_encoder(result)


# TODO add fetching for each sensor type using appropriate api wrapper to fetch data
@celeryapp.task(name="tasks.scheduled_upsert_sensorSummary")
def scheduled_upsert_sensorSummary(startDate: str, endDate: str, type_ids: list[int]):
    """upsert sensor summaries for all active sensors"""
    try:
        startDate, endDate = convertDateRangeStringToDate(startDate, endDate)
    except (ValueError, TypeError):
        raise Exception("Invalid date range or type")

    api = CeleryWrapper()

    sensor_dict = get_lookupids_of_active_sensors_by_type(type_ids)

    if sensor_dict:
        logged_writes = {}
        # for each sensor type, fetch the data from the api and write to the database
        for (key, value) in sensor_dict.items():
            match key:
                case 1:
                    for sensorSummary in api.fetch_plume_data(startDate, endDate, value):
                        try:
                            lookupid = sensorSummary.sensor_id
                            (sensorSummary.sensor_id,) = sensor_id_from_lookup_id(str(lookupid))

                            upsert_sensorSummary(sensorSummary)

                            logged_writes[sensorSummary.sensor_id] = (True, sensorSummary.timestamp, "no errors")
                        except Exception as e:
                            logged_writes[sensorSummary.sensor_id] = (False, sensorSummary.timestamp, str(e))
                case 2:
                    continue
                case 3:
                    continue

        # return timestamp and sensor id of the summaries that were successfully written to the database
        return log_sensor_writes(logged_writes)
    else:
        return "No active sensors found"


# TODO test this function
@celeryapp.task(name="tasks.check_error_logs")
def check_error_logs():
    if check_log():
        # TODO send to firebase db or email and clean log
        clean_log()
        return "errors found"
    else:
        return "No errors found"


#################################################################################################################################
###############################################Sentry setup###################################################################
#################################################################################################################################
# setting up sentry
if env["PRODUCTION_MODE"] == "TRUE":
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=env["CELERY_SENTRY_DSN"],
        integrations=[
            CeleryIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=env["CELERY_SENTRY_SAMPLE_RATE"],
    )

#################################################################################################################################
###############################################Cron Job function###################################################################
#################################################################################################################################
@celeryapp.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    cronjobs to retrieve sensor data.
    """

    # sender.add_periodic_task(5, add.s(5, 15), name="test")

    # TODO add daily cronjob to add json logs to firebase db if is not empty
    # log results and email if there are errors DAILY just before midnight
    sender.add_periodic_task(crontab(hour=23, minute=59), check_error_logs.s(), name="check_error_logs")

    # TODO separate cronjobs for sensor community sensors (daily)

    # schedule a upsert to run every day at 2am
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        scheduled_upsert_sensorSummary.s(*get_dates(-1), [1, 2, 3]),
        name="daily_upsert_sensorSummary",
    )

    # schedule a task to run every 10 minutes 600 for plume and zephyr sensors
    # sender.add_periodic_task(600, scheduled_upsert_sensorSummary.s(*get_dates(1), [1, 2]), name="upsert_sensorSummary")


#################################################################################################################################
###############################################helper functions###################################################################
#################################################################################################################################


def get_dates(days: int) -> Tuple[str, str]:
    """
    :return: Tuple[start, end] -> now, now +/- days
    """
    return dt.datetime.today().strftime("%d-%m-%Y"), (dt.datetime.today() + dt.timedelta(days)).strftime("%d-%m-%Y")


def get_lookupids_of_active_sensors_by_type(type_ids: list[int]) -> dict[int, list[str]]:
    """
    Returns dict: where dict[sensor_type] = [list of lookup_ids]

    """
    sensorsPairs = get_active_sensors(type_ids)

    # group sensors by type into a dictionary dict[sensor_type] = [list of sensors]
    sensor_dict = {}
    for (key, value) in sensorsPairs:

        if key in sensor_dict:
            sensor_dict[key].append(value)
        else:
            sensor_dict[key] = [value]

    return sensor_dict


def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:

    startDate = dt.datetime.strptime(start, "%d-%m-%Y")
    endDate = dt.datetime.strptime(end, "%d-%m-%Y")

    return startDate, endDate


def log_sensor_writes(succesful_writes: dict[int, tuple([bool, str, str])]) -> dict[int, tuple([bool, str, str])]:
    """
    Logs sensor data to a file
    """
    for (id_, (success, timestamp, error_message)) in succesful_writes.items():
        if success:
            set_last_updated(id_, timestamp)
        else:
            write_json({timestamp: [{id_: error_message}]}, timestamp)

    return succesful_writes
