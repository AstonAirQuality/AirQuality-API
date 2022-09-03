import datetime as dt

# enviroment variables dependacies
from os import environ as env
from typing import Tuple

from api_wrappers.scraperWrapper import ScraperWrapper
from core.models import SensorSummaries

# sensor summary
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, status

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


@backgroundTasksRouter.put("/api/upsert-scheduled-ingest-active-sensors/{start}/{end}")
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
        summary_insert_log = {}
        # for each sensor type, fetch the data from the api and write to the database
        for (key, value) in sensor_dict.items():
            match key:
                case 1:
                    for sensorSummary in api.fetch_plume_data(startDate, endDate, value):
                        try:
                            lookupid = sensorSummary.sensor_id
                            (sensorSummary.sensor_id,) = sensor_id_from_lookup_id(str(lookupid))

                            upsert_sensorSummary(sensorSummary)

                            summary_insert_log[sensorSummary.sensor_id] = (
                                True,
                                sensorSummary.timestamp,
                                "no errors",
                            )
                        except Exception as e:
                            summary_insert_log[sensorSummary.sensor_id] = (False, sensorSummary.timestamp, str(e))
                case 2:
                    # TODO add api call for sensor type 2
                    continue
                case 3:
                    # TODO add api call for sensor type 3
                    continue

        # return timestamp and sensor id of the summaries that were successfully written to the database
        return update_sensor_last_updated(summary_insert_log)
    else:
        return "No active sensors found"


#################################################################################################################################
###############################################helper functions###################################################################
#################################################################################################################################
def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:
    try:
        startDate = dt.datetime.strptime(start, "%d-%m-%Y")
        endDate = dt.datetime.strptime(end, "%d-%m-%Y")

    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format")

    return startDate, endDate


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


def get_dates(days: int) -> Tuple[str, str]:
    """
    :return: Tuple[start, end] -> now, now +/- days
    """
    return dt.datetime.today().strftime("%d-%m-%Y"), (dt.datetime.today() + dt.timedelta(days)).strftime("%d-%m-%Y")


def update_sensor_last_updated(
    succesful_writes: dict[int, tuple([bool, str, str])]
) -> dict[int, tuple([bool, str, str])]:
    """
    Logs sensor data to a file
    """
    for (id_, (success, timestamp, error_message)) in succesful_writes.items():
        if success:
            set_last_updated(id_, timestamp)
        else:
            # TODO log error to db
            # write_json({timestamp: [{id_: error_message}]}, timestamp)
            pass

    return succesful_writes
