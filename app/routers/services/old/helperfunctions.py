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
