import datetime as dt
import time

# enviroment variables dependacies
from os import environ as env
from typing import Tuple  # TODO REMOVE

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
from routers.sensors import get_active_sensors, sensor_id_from_lookup_id

#
from routers.sensorSummaries import get_sensorSummaries, upsert_sensorSummary

# from celery.schedules import crontab
# from celery.task import periodic_task


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
def scheduled_upsert_sensorSummary(startDate: str, endDate: str):
    """upsert sensor summaries for all active sensors"""

    try:
        startDate, endDate = convertDateRangeStringToDate(startDate, endDate)
    except (ValueError, TypeError):
        raise Exception("Invalid date range or type")

    sensor_dict = get_lookupids_of_active_sensors_by_type()

    api = CeleryWrapper()

    succesful_writes = {}
    # for each sensor type, fetch the data from the api and write to the database
    for (key, value) in sensor_dict.items():
        match key:
            case 1:
                for sensorSummary in api.fetch_plume_data(startDate, endDate, value):
                    try:
                        # TODO map lookup_id to sensor_id
                        lookupid = sensorSummary.sensor_id
                        (sensorSummary.sensor_id,) = sensor_id_from_lookup_id(str(lookupid))

                        upsert_sensorSummary(sensorSummary)

                        succesful_writes[str(sensorSummary.timestamp) + "_" + str(lookupid)] = "True"
                    except Exception as e:
                        succesful_writes[str(sensorSummary.timestamp) + "_" + str(lookupid)] = str(e)
            case 2:
                continue
            case 3:
                continue

    # return timestamp and sensor id of the summaries that were successfully written to the database
    return succesful_writes


#################################################################################################################################
###############################################Other functions###################################################################
#################################################################################################################################


@celeryapp.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    cronjobs to retrieve sensor data.
    """
    sender.add_periodic_task(10.0, add.s(5, 10), name="test")

    # #schedule a task to run every day at 2am
    # sender.add_periodic_task(crontab(hour=2, minute=0), scheduled_upsert_sensorSummary.s(), name="daily_upsert_sensorSummary")

    # #schedule a task to run every 10 minutes
    # sender.add_periodic_task(600, scheduled_upsert_sensorSummary.s() name="upsert_sensorSummary")


def get_lookupids_of_active_sensors_by_type() -> dict[int, list[str]]:
    """
    Returns dict: where dict[sensor_type] = [list of lookup_ids]

    """
    sensorsPairs = get_active_sensors()

    # group sensors by type into a dictionary dict[sensor_type] = [list of sensors]
    sensor_dict = {}
    for (key, value) in sensorsPairs:

        if key in sensor_dict:
            sensor_dict[key].append(value)
        else:
            sensor_dict[key] = [value]

    return sensor_dict


# helper functions
def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:

    startDate = dt.datetime.strptime(start, "%d-%m-%Y")
    endDate = dt.datetime.strptime(end, "%d-%m-%Y")

    return startDate, endDate
