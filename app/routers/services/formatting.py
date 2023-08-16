import datetime as dt
from typing import Tuple

import shapely.wkt
from fastapi import HTTPException, status
from geoalchemy2.shape import WKBElement, from_shape, to_shape


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


def convertWKTtoWKB(wkt: str) -> WKBElement:
    """converts wkt string to wkb element
    :param wkt: wkt string
    :return: wkb element"""
    try:
        wkb = from_shape(shapely.wkt.loads(wkt), srid=4326)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geometry must be a valid WKTE geometry: {e}")
    return wkb


def convertWKBtoWKT(element: any) -> str:
    """converts wkb element to human-readable (wkt string)
    :param element: wkb element
    :return: wkt string"""
    try:
        # if the element is already a string, then it is already in wkt format
        if isinstance(element, str):
            return element
        if element is not None:
            return to_shape(element).wkt
    except AssertionError:
        pass
    return None


def format_sensor_joined_data(result: any):
    """Format the sensor data's stationary box and joined data
    :param result: result to format
    :return: formatted result"""
    results = []
    try:
        for row in result:
            row_as_dict = dict(row._mapping)
            if "stationary_box" in row_as_dict:
                row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            if "username" in row_as_dict and "uid" in row_as_dict:
                row_as_dict["username"] = str(row_as_dict["username"]) + " " + str(row_as_dict["uid"])
                del row_as_dict["uid"]

            results.append(row_as_dict)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not format results")

    return results
