import datetime as dt
import json

# enviroment variables dependacies
from os import environ as env
from typing import Tuple

from core.authentication import AuthHandler
from core.models import SensorSummaries
from core.schema import DataIngestionLog as SchemaDataIngestionLog
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
from routers.logs import add_log
from routers.sensorSummaries import upsert_sensorSummary
from routers.services.crud.crud import CRUD
from routers.services.firebase_notifications import (
    addFirebaseNotifcationDataIngestionTask,
    clearFirebaseNotifcationDataIngestionTask,
    updateFirebaseNotifcationDataIngestionTask,
)
from routers.services.formatting import convertDateRangeStringToDate
from routers.services.sensorsSharedFunctions import (
    deactivate_unsynced_sensor,
    get_lookupids_of_sensors,
    get_sensor_dict,
    get_sensor_id_and_serialnum_from_lookup_id,
    set_last_updated,
)
from sensor_api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper

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

    data_ingestion_logs = []

    if type_of_id == "sensor_id":
        sensor_dict, flagged_sensors = get_lookupids_of_sensors(id_list, "sensor_id")
    elif type_of_id == "sensor_type_id":
        sensor_dict, flagged_sensors = get_lookupids_of_sensors(id_list, "sensor_type_id")

    if flagged_sensors:
        for flaggedSensor in flagged_sensors:
            deactivate_unsynced_sensor(flaggedSensor["id"])
            data_ingestion_logs.append(
                SchemaDataIngestionLog(
                    sensor_id=flaggedSensor["id"],
                    sensor_serial_number=flaggedSensor["serial_number"],
                    timestamp=int(dt.datetime.utcnow().timestamp()),
                    success_status=False,
                    message="Sensor has not been updated in over 90 days",
                )
            )

    if sensor_dict:
        # for each sensor type, fetch the data from the sfw and write to the database
        for sensorType, dict_lookupid_stationaryBox_and_timeUpdated in sensor_dict.items():
            if sensorType.lower() == "plume":
                for sensorSummary in sfw.fetch_plume_data(startDate, endDate, dict_lookupid_stationaryBox_and_timeUpdated):
                    data_ingestion_logs = append_data_ingestion_logs(sensorSummary, data_ingestion_logs)

            elif sensorType.lower() == "zephyr":
                for sensorSummary in sfw.fetch_zephyr_data(startDate, endDate, dict_lookupid_stationaryBox_and_timeUpdated):
                    data_ingestion_logs = append_data_ingestion_logs(sensorSummary, data_ingestion_logs)

            elif sensorType.lower() == "sensorcommunity":
                # CSV ingest only
                # # if the cron job was used then we can use the same start and end date because the latest historical data is yesterday instead of today
                # if type_of_id == "sensor_type_id":
                #     endDate = startDate
                for sensorSummary in sfw.fetch_sensorCommunity_data(startDate, endDate, dict_lookupid_stationaryBox_and_timeUpdated):
                    data_ingestion_logs = append_data_ingestion_logs(sensorSummary, data_ingestion_logs)
                continue
    else:
        if type_of_id == "sensor_id":
            try:
                updateFirebaseNotifcationDataIngestionTask(log_timestamp, -1, "❌ No active sensors found")
            except Exception as e:
                return "No active sensors found"

    if len(data_ingestion_logs) == 0:
        if type_of_id == "sensor_id":
            try:
                updateFirebaseNotifcationDataIngestionTask(log_timestamp, -1, "❌ No data was found for the requested sensors in the given date range")
            except Exception as e:
                return "No data was found for this sensor in the given date range"

    else:
        # return timestamp and sensor id of the summaries that were successfully written to the database
        log_dict = update_sensor_last_updated(data_ingestion_logs, log_timestamp)
        if type_of_id == "sensor_id":
            try:
                updateFirebaseNotifcationDataIngestionTask(log_timestamp, 1, "✅ data ingestion task completed")
            except Exception as e:
                print("✅ data ingestion task completed")
            return log_dict

    return


def append_data_ingestion_logs(sensorSummary: SchemaSensorSummary, data_ingestion_logs: list[SchemaDataIngestionLog]) -> list[SchemaDataIngestionLog]:
    """append a data ingestion log to the data ingestion logs
    :param data_ingestion_logs: list of data ingestion logs
    :param sensorSummary: sensor summary object
    """
    (sensorSummary.sensor_id, sensor_serial_number) = get_sensor_id_and_serialnum_from_lookup_id(str(sensorSummary.sensor_id))

    # if the sensor has data we try to upsert a sensor summary into the database
    if sensorSummary.measurement_count > 0:
        try:
            upsert_sensorSummary(sensorSummary)
            data_ingestion_logs.append(SchemaDataIngestionLog(sensor_id=sensorSummary.sensor_id, sensor_serial_number=sensor_serial_number, timestamp=sensorSummary.timestamp, success_status=True))
        # if the upsert fails we log the failure
        except Exception as e:
            data_ingestion_logs.append(
                SchemaDataIngestionLog(sensor_id=sensorSummary.sensor_id, sensor_serial_number=sensor_serial_number, timestamp=sensorSummary.timestamp, success_status=False, message=str(e))
            )

    # else the sensor has no data. So we log the failure
    else:
        message = "No data was found for this sensor in the given date range"
        try:
            message = json.loads(sensorSummary.measurement_data)["message"]
        except Exception as e:
            pass

        data_ingestion_logs.append(
            SchemaDataIngestionLog(
                sensor_id=sensorSummary.sensor_id,
                sensor_serial_number=sensor_serial_number,
                timestamp=sensorSummary.timestamp,
                success_status=False,
                message=message,
            )
        )

    return data_ingestion_logs


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

    # get the user id from the payload
    uid = payload["sub"]
    # add a firebase notification task to the realtime db
    addFirebaseNotifcationDataIngestionTask(uid, log_timestamp, 0, "🔎 searching for sensors")

    return {"task_id": log_timestamp, "task_message": "task sent to backend"}


@backgroundTasksRouter.get("/cron/ingest-active-sensors/{id_type}")
async def schedule_data_ingest_task_of_active_sensors_by_sensorTypeId(background_tasks: BackgroundTasks, id_type: int, cron_job_token=Header(...)):
    """
    This function is called by AWS Lambda to run the scheduled ingest task for plume sensors
    :param cron_job_token: cron job token
    """
    if cron_job_token != env["CRON_JOB_TOKEN"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    start, end = get_dates(-1)
    log_timestamp = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    background_tasks.add_task(upsert_sensor_summary_by_id_list, start, end, [id_type], "sensor_type_id", log_timestamp)
    return {"task_id": log_timestamp, "task_message": "task sent to backend"}


@backgroundTasksRouter.get("/cron/clear-data-ingestion-queue")
async def clear_data_ingestion_queue(cron_job_token=Header(...)):
    """
    This function is called by AWS Lambda to clear the data ingestion queue
    :param cron_job_token: cron job token
    """
    if cron_job_token != env["CRON_JOB_TOKEN"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    else:
        clearFirebaseNotifcationDataIngestionTask()
        return {"message": "data ingestion queue cleared"}


#################################################################################################################################
#                                              helper functions                                                                 #
#################################################################################################################################
def get_dates(days: int) -> Tuple[str, str]:
    """
    :return: Tuple[start, end] -> now +/- days, now in format dd-mm-yyyy
    """
    return (dt.datetime.today() + dt.timedelta(days)).strftime("%d-%m-%Y"), dt.datetime.today().strftime("%d-%m-%Y")


def update_sensor_last_updated(data_ingestion_logs: list[SchemaDataIngestionLog], log_timestamp: str) -> dict:
    """
    Logs sensor data that was successfully written to the database and updates the last_updated field of the sensor
    """
    log_data_dict = {}
    for data_ingestion_log in data_ingestion_logs:
        id_ = data_ingestion_log.sensor_id
        timestamp = data_ingestion_log.timestamp
        sensor_serial_number = data_ingestion_log.sensor_serial_number
        success_status = data_ingestion_log.success_status
        message = data_ingestion_log.message

        if success_status:
            try:
                set_last_updated(id_, timestamp)
            except Exception as e:
                message = "sensor last updated failed: " + str(e)

        # if message is None then don't include it in the log

        if timestamp in log_data_dict:
            log_data_dict[timestamp][id_] = {"serial_number": sensor_serial_number, "status": success_status, "message": message}
        else:
            log_data_dict[timestamp] = {id_: {"serial_number": sensor_serial_number, "status": success_status, "message": message}}

        if message is None:
            del log_data_dict[timestamp][id_]["message"]

    add_log(
        log_timestamp,
        SchemaLog(log_data=json.dumps(log_data_dict)),
    )

    return log_data_dict
