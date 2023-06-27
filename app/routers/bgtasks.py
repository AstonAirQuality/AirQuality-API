import datetime as dt
import json

# enviroment variables dependacies
from os import environ as env
from typing import Tuple

from api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from core.authentication import AuthHandler
from core.models import SensorSummaries
from core.schema import Log as SchemaLog
from core.schema import SensorSummary as SchemaSensorSummary

# sensor summary
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from routers.helpers.helperfunctions import convertDateRangeStringToDate
from routers.helpers.sensorsSharedFunctions import (
    get_sensor_dict,
    get_sensor_id_and_serialnum_from_lookup_id,
    set_last_updated,
)
from routers.helpers.sensorSummarySharedFunctions import upsert_sensorSummary
from routers.logs import add_log

load_dotenv()

auth_handler = AuthHandler()
backgroundTasksRouter = APIRouter()

# TODO add leap year check
dateRegex = "\s+(?:0[1-9]|[12][0-9]|3[01])[-/.](?:0[1-9]|1[012])[-/.](?:19\d{2}|20\d{2}|2100)\b"


# @backgroundTasksRouter.put("/upsert/sensor-data-ingestion-by-IdList/{start}/{end}/{type_of_id}")
def upsert_sensor_summary_by_id_list(
    start: str = Query(regex=dateRegex),
    end: str = Query(regex=dateRegex),
    id_list: list[int] = Query(default=[]),
    type_of_id: str = Query(default="sensor_id"),
    log_timestamp: str = Query(default=dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")),
):
    """start a background task to ingest sensor data using a list of ids. The type of id must be specified
    :param start: start date of the data to be ingested. (e.g 20-08-2022)
    :param end: end date of the data to be ingested (e.g 26-08-2022)
    :param id_list: list of ids
    :param type_of_id: type of id. Can be sensor_id or sensor_type_id
    :param log_timestamp: timestamp of the log
    """

    startDate, endDate = convertDateRangeStringToDate(start, end)

    sfw = SensorFactoryWrapper()

    if type_of_id == "sensor_id":
        sensor_dict = get_lookupids_of_sensors(id_list, "sensor_id")
    elif type_of_id == "sensor_type_id":
        sensor_dict = get_lookupids_of_sensors(id_list, "sensor_type_id")

    if sensor_dict:
        upsert_log = []
        # for each sensor type, fetch the data from the sfw and write to the database
        for sensorType, dict_lookupid_stationaryBox in sensor_dict.items():
            if sensorType.lower() == "plume":
                for sensorSummary in sfw.fetch_plume_data(startDate, endDate, dict_lookupid_stationaryBox):
                    upsert_log = upsert_summary_and_log(sensorSummary, upsert_log)

            elif sensorType.lower() == "zephyr":
                for sensorSummary in sfw.fetch_zephyr_data(startDate, endDate, dict_lookupid_stationaryBox):
                    upsert_log = upsert_summary_and_log(sensorSummary, upsert_log)

            elif sensorType.lower() == "sensorcommunity":
                # if the cron job was used then we can use the same start and end date
                if type_of_id == "sensor_type_id":
                    endDate = startDate
                for sensorSummary in sfw.fetch_sensorCommunity_data(startDate, endDate, dict_lookupid_stationaryBox):
                    upsert_log = upsert_summary_and_log(sensorSummary, upsert_log)
                continue

        # return timestamp and sensor id of the summaries that were successfully written to the database
        return update_sensor_last_updated(upsert_log, log_timestamp)
    else:
        return "No active sensors found"


def upsert_summary_and_log(sensorSummary: SchemaSensorSummary, upsert_log: list):
    """upsert a sensor summary into the database
    :param sensorSummary: sensor summary object
    :param upsert_log: list of logs
    """
    lookupid = sensorSummary.sensor_id
    (sensorSummary.sensor_id, sensor_serial_number) = get_sensor_id_and_serialnum_from_lookup_id(str(lookupid))
    try:
        upsert_sensorSummary(sensorSummary)
        upsert_log.append([sensorSummary.sensor_id, sensorSummary.timestamp, sensor_serial_number, True, "success"])
    except Exception as e:
        upsert_log.append([sensorSummary.sensor_id, sensorSummary.timestamp, sensor_serial_number, False, str(e)])

    return upsert_log


@backgroundTasksRouter.post("/schedule/ingest-bysensorid/{start}/{end}")
async def schedule_data_ingest_task_by_sensorid(
    background_tasks: BackgroundTasks,
    start: str = Query(regex=dateRegex),
    end: str = Query(regex=dateRegex),
    sensor_ids: list[int] = Query(default=[], description="list of sensor ids to search for"),
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Run by admins to schedule the data ingest task in the background for a list of sensors by sensor id
    \n :param start: start date of the data to be ingested. (e.g 20-08-2022)
    \n :param end: end date of the data to be ingested (e.g 26-08-2022)
    \n :param sensor_ids: list of sensor ids
    \n :return: task_id and task_message
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    log_timestamp = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    background_tasks.add_task(upsert_sensor_summary_by_id_list, start, end, sensor_ids, "sensor_id", log_timestamp)

    return {"task_id": log_timestamp, "task_message": "task sent to backend"}


@backgroundTasksRouter.get("/cron/ingest-active-sensors/{id_type}")
async def schedule_data_ingest_task_of_active_sensors_by_sensorTypeId(background_tasks: BackgroundTasks, id_type: int, cron_job_token=Header(...)):
    """
    This function is called by AWS Lambda to run the scheduled ingest task for plume sensors
    """
    if cron_job_token != env["CRON_JOB_TOKEN"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    start, end = get_dates(-1)
    log_timestamp = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    background_tasks.add_task(upsert_sensor_summary_by_id_list, start, end, [id_type], "sensor_type_id", log_timestamp)
    return {"task_id": log_timestamp, "task_message": "task sent to backend"}


#################################################################################################################################
#                                              helper functions                                                                 #
#################################################################################################################################
def get_lookupids_of_sensors(ids: list[int], idtype: str) -> dict[int, dict[str, str]]:
    """
    Returns dict: where dict[sensor_type_name][lookup_id] = stationary_box

    """
    sensors = get_sensor_dict(idtype, ids)

    # group sensors by type into a dictionary dict[sensor_type][lookup_id] = stationary_box
    sensor_dict = {}
    for data in sensors:
        if data["type_name"] in sensor_dict:
            sensor_dict[data["type_name"]][str(data["lookup_id"])] = data["stationary_box"]
        else:
            sensor_dict[data["type_name"]] = {str(data["lookup_id"]): data["stationary_box"]}

    return sensor_dict


def get_dates(days: int) -> Tuple[str, str]:
    """
    :return: Tuple[start, end] -> now +/- days, now in format dd-mm-yyyy
    """
    return (dt.datetime.today() + dt.timedelta(days)).strftime("%d-%m-%Y"), dt.datetime.today().strftime("%d-%m-%Y")


def update_sensor_last_updated(upsert_log: list[list], log_timestamp: str) -> dict:
    """
    Logs sensor data that was successfully written to the database and updates the last_updated field of the sensor
    """
    log_dictionary = {}
    for id_, timestamp, sensor_serial_number, success_status, error_message in upsert_log:
        if success_status:
            try:
                set_last_updated(id_, timestamp)
            except Exception as e:
                error_message = "sensor last updated failed: " + str(e)

        if timestamp in log_dictionary:
            log_dictionary[timestamp][id_] = {"serial_number": sensor_serial_number, "status": success_status, "message": error_message}
        else:
            log_dictionary[timestamp] = {id_: {"serial_number": sensor_serial_number, "status": success_status, "message": error_message}}

    add_log(
        log_timestamp,
        SchemaLog(log_data=json.dumps(log_dictionary)),
    )

    return log_dictionary
