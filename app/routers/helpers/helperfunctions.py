import datetime as dt
from typing import Tuple

from config.firebaseConfig import PyreBaseDB
from fastapi import HTTPException, status


def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:
    """converts a date range string to a tuple of datetime objects
    :param start: start date string in format DD-MM-YYYY
    :param end: end date string in format DD-MM-YYYY
    :return: tuple of datetime objects
    """
    try:
        startDate = dt.datetime.strptime(start, "%d-%m-%Y")
        endDate = dt.datetime.strptime(end, "%d-%m-%Y")

    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format {start},{end}".format(start=start, end=end))

    return startDate, endDate


def addFirebaseNotifcationDataIngestionTask(uid: str, timestamp_key: str, status: int, message: str):
    """adds a firebase notification data ingestion task to the realtime db
    :param user_id: user id
    :param timestamp_key: timestamp key
    :param status: status of the task
    :param message: message of the task
    """
    PyreBaseDB.child("data-ingestion-tasks").child(timestamp_key).set({"uid": uid, "status": status, "message": message})


def updateFirebaseNotifcationDataIngestionTask(timestamp_key: str, status: int, message: str):
    """updates a firebase notification data ingestion task in the queue
    :param timestamp_key: timestamp key
    :param status: status of the task
    :param message: message of the task"""

    PyreBaseDB.child("data-ingestion-tasks").child(timestamp_key).update({"status": status, "message": message})


def clearFirebaseNotifcationDataIngestionTask():
    """clears all firebase notification data ingestion task in the queue
    :param timestamp_key: timestamp key"""

    PyreBaseDB.child("data-ingestion-tasks").remove()
