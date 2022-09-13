import datetime as dt
import json

# enviroment variables dependacies
from os import environ as env
from typing import Tuple

from api_wrappers.scraperWrapper import ScraperWrapper
from core.models import SensorSummaries
from core.schema import Log as SchemaLog

# sensor summary
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from routers.helperfunctions import convertDateRangeStringToDate
from routers.logs import add_log
from routers.sensors import (
    get_active_sensors,
    sensor_id_from_lookup_id,
    set_last_updated,
)
from routers.sensorSummaries import upsert_sensorSummary

load_dotenv()


backgroundTasksRouter = APIRouter()

# TODO add leap year check
dateRegex = "\s+(?:0[1-9]|[12][0-9]|3[01])[-/.](?:0[1-9]|1[012])[-/.](?:19\d{2}|20\d{2}|2100)\b"


@backgroundTasksRouter.put("/upsert/scheduled-ingest-active-sensors/{start}/{end}")
async def upsert_scheduled_ingest_active_sensors(
    start: str = Query(regex=dateRegex),
    end: str = Query(regex=dateRegex),
    sensor_type_ids: list[int] = Query(default=[1, 2, 3]),
):
    """create a scheduled ingest task of the active sensors.
    params: must be valid date string e.g. 20-08-2022,26-08-2022"""

    startDate, endDate = convertDateRangeStringToDate(start, end)

    api = ScraperWrapper()

    sensor_dict = get_lookupids_of_active_sensors_by_type(sensor_type_ids)

    if sensor_dict:
        upsert_log = []
        # for each sensor type, fetch the data from the api and write to the database
        for (key, value) in sensor_dict.items():
            if key == 1:
                for sensorSummary in api.fetch_plume_data(startDate, endDate, value):
                    try:
                        lookupid = sensorSummary.sensor_id
                        (sensorSummary.sensor_id,) = sensor_id_from_lookup_id(str(lookupid))

                        upsert_sensorSummary(sensorSummary)
                        upsert_log.append([sensorSummary.sensor_id, sensorSummary.timestamp, True, "success"])
                    except Exception as e:
                        upsert_log.append([sensorSummary.sensor_id, sensorSummary.timestamp, False, str(e)])
            elif key == 2:
                # TODO add api call for sensor type 2
                continue
            elif key == 3:
                # TODO add api call for sensor type 3
                continue

        # return timestamp and sensor id of the summaries that were successfully written to the database
        return update_sensor_last_updated(upsert_log)
    else:
        return "No active sensors found"


@backgroundTasksRouter.get("/cron/ingest-active-sensors")
async def aws_cronjob(background_tasks: BackgroundTasks):
    """
    This function is called by AWS Lambda to run the scheduled ingest task
    """
    start, end = get_dates(-1)
    background_tasks.add_task(upsert_scheduled_ingest_active_sensors, start, end,sensor_type_ids=[1])
    return {"message": "task sent to backend"}


#################################################################################################################################
#                                              helper functions                                                                 #
#################################################################################################################################
def get_lookupids_of_active_sensors_by_type(type_ids: list[int]) -> dict[int, dict[str, str]]:
    """
    Returns dict: where dict[sensor_type] = dict[lookup_id] = stationary_box

    """
    sensors = get_active_sensors(type_ids)

    # group sensors by type into a dictionary dict[sensor_type] = dict[lookup_id] = stationary_box
    sensor_dict = {}
    for data in sensors:
        if data[0] in sensor_dict:
            sensor_dict[data[0]][data[1]] = data[2]
        else:
            sensor_dict[data[0]] = {data[1]: data[2]}

    return sensor_dict


def get_dates(days: int) -> Tuple[str, str]:
    """
    :return: Tuple[start, end] -> now +/- days, now in format dd-mm-yyyy
    """
    return (dt.datetime.today() + dt.timedelta(days)).strftime("%d-%m-%Y"), dt.datetime.today().strftime("%d-%m-%Y")


def update_sensor_last_updated(upsert_log: list[list]) -> dict:
    """
    Logs sensor data to a file
    """
    log_dictionary = {}
    for (id_, timestamp, success_status, error_message) in upsert_log:
        if success_status:
            try:
                set_last_updated(id_, timestamp)
            except Exception as e:
                error_message = "sensor last updated failed: " + str(e)

        if timestamp in log_dictionary:
            log_dictionary[timestamp][id_] = [success_status, error_message]
        else:
            log_dictionary[timestamp] = {id_: [success_status, error_message]}

    add_log(SchemaLog(log_data=json.dumps(log_dictionary)))

    return log_dictionary
