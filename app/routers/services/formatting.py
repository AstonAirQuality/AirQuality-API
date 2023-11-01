import datetime as dt
from math import log10
from typing import Tuple

import shapely.wkt
from core.schema import GeoJsonExport
from fastapi import HTTPException, status
from geoalchemy2.shape import WKBElement, from_shape, to_shape
from sensor_api_wrappers.data_transfer_object.sensor_readable import SensorReadable


def decode_geohash(geohash: str) -> tuple[float, float]:
    """
    Decode geohash, returning two strings with latitude and longitude
    containing only relevant digits and with trailing zeroes removed.
    """
    # decode geohash
    base32_ = "0123456789bcdefghjkmnpqrstuvwxyz"
    decode_map = {}
    for i in range(len(base32_)):
        decode_map[base32_[i]] = i
    del i

    lat_interval, lon_interval = (-90.0, 90.0), (-180.0, 180.0)
    lat_err, lon_err = 90.0, 180.0
    is_even = True
    for c in geohash:
        cd = decode_map[c]
        for mask in [16, 8, 4, 2, 1]:
            if is_even:  # adds longitude info
                lon_err /= 2
                if cd & mask:
                    lon_interval = ((lon_interval[0] + lon_interval[1]) / 2, lon_interval[1])
                else:
                    lon_interval = (lon_interval[0], (lon_interval[0] + lon_interval[1]) / 2)
            else:  # adds latitude info
                lat_err /= 2
                if cd & mask:
                    lat_interval = ((lat_interval[0] + lat_interval[1]) / 2, lat_interval[1])
                else:
                    lat_interval = (lat_interval[0], (lat_interval[0] + lat_interval[1]) / 2)
            is_even = not is_even
    lat = (lat_interval[0] + lat_interval[1]) / 2
    lon = (lon_interval[0] + lon_interval[1]) / 2

    # Format to the number of decimals that are known
    lats = "%.*f" % (max(1, int(round(-log10(lat_err)))) - 1, lat)
    lons = "%.*f" % (max(1, int(round(-log10(lon_err)))) - 1, lon)
    if "." in lats:
        lats = lats.rstrip("0")
    if "." in lons:
        lons = lons.rstrip("0")
    return lats, lons


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


def convertDateRangeStringToTimestamp(start: dt.datetime, end: dt.datetime) -> Tuple[int, int]:
    """converts a date range string to a tuple of timestamps
    :param start: start date string in format DD-MM-YYYY
    :param end: end date string in format DD-MM-YYYY
    :return: tuple of timestamps
    """
    (startDate, endDate) = convertDateRangeStringToDate(start, end)
    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))
    return timestampStart, timestampEnd


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


def format_sensor_summary_data(query_result: any, deserialize: bool = True):
    """Format the sensor summary data"""
    results = []
    for row in query_result:
        row_as_dict = dict(row._mapping)
        if "geom" in row_as_dict:
            row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])

        if "timestamp" in row_as_dict:
            row_as_dict["timestamp_UTC"] = row_as_dict.pop("timestamp")

        if "measurement_data" in row_as_dict and deserialize:
            # convert the json string to a python dict
            row_as_dict["measurement_data"] = deserializeMeasurementData(row_as_dict["measurement_data"])

        results.append(row_as_dict)

        

    return results


def JsonToSensorReadable(results: list) -> list[tuple[SensorReadable, str]]:
    """converts a list of sensor summaries into a list of SensorReadables.
    :param results: list of sensor summaries
    :return: list of SensorReadables"""

    # group sensors by id into a dictionary dict[sensor_id] = dict{json_ : measurement data, "boundingBox": geom}
    sensor_dict = {}
    for sensorSummary in results:
        data_dict = {"sensor_type": None, "json_": sensorSummary["measurement_data"], "boundingBox": sensorSummary["geom"] if sensorSummary["stationary"] == True else None}

        # if type_name key exists in sensorSummary, add it to the data_dict, otherwise remove it from the data_dict
        if "type_name" in sensorSummary:
            data_dict["sensor_type"] = sensorSummary["type_name"]
        else:
            del data_dict["sensor_type"]

        # add the data dict to the sensor_dict
        if sensorSummary["sensor_id"] in sensor_dict:
            sensor_dict[sensorSummary["sensor_id"]].append(data_dict)
        else:
            sensor_dict[sensorSummary["sensor_id"]] = [data_dict]

    # convert list of measurement data into a SensorReadable
    sensors = []
    for sensor_id, data in sensor_dict.items():
        sensors.append([SensorReadable.from_json_list(sensor_id, data), data[0]["sensor_type"]])
    return sensors


def sensorSummariesToGeoJson(results: list, averaging_methods: list[str], averaging_frequency: str = "H"):
    """converts a list of sensor summaries into geojsons
    :param results: list of sensor summaries
    :param averaging_method: method of averaging the sensor summaries
    :param averaging_frequency: frequency of averaging the sensor summaries
    :return: list of geojsons"""

    sensors = JsonToSensorReadable(results)

    geoJsons = []
    for sensor, sensorTypeString in sensors:
        geoJsons.append(GeoJsonExport(sensorid=sensor.id, sensorType=sensorTypeString, geojson=sensor.to_geojson(averaging_methods, averaging_frequency)))

    return geoJsons


def deserializeMeasurementData(measurement_data: str) -> dict:
    """deserializes the measurement data
    :param measurement_data: measurement data to deserialize
    :return: dictionary of deserialized measurement data"""
    df = SensorReadable.JsonStringToDataframe(measurement_data, boundingBox=None)
    df.drop(columns=["timestamp", "boundingBox"], inplace=True)
    return df.to_dict(orient="index")
