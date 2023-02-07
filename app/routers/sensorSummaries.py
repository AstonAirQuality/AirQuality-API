import datetime as dt

from core.models import SensorSummaries as ModelSensorSummary
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from routers.helpers.helperfunctions import convertDateRangeStringToDate
from routers.helpers.sensorSummarySharedFunctions import (
    searchQueryFilters,
    sensorSummariesToGeoJson,
)
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

sensorSummariesRouter = APIRouter()

db = SessionLocal()

#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
# TODO add param to read to allow aggregation of sensors into a single measurement_data json
@sensorSummariesRouter.get("/{start}/{end}")
def get_sensorSummaries(
    start: str,
    end: str,
    columns: list[str] = Query(default=["sensor_id", "measurement_count", "geom", "timestamp"]),
    spatial_query_type: str = Query(None),
    geom: str = Query(None),
    sensor_ids: list[int] = Query(default=[]),
):
    """read sensor summaries given a date range (e.g /read/28-09-2022/30-09-2022) and any optional filters then return a json of sensor summaries
    :param start: start date of the query in the format dd-mm-yyyy
    :param end: end date of the query in the format dd-mm-yyyy
    :param columns: list of columns to return from the sensor summaries table
    :param spatial_query_type: type of spatial query to perform (e.g intersects, contains, within ) - see spatialQueryBuilder for more info
    :param geom: geometry to use in the spatial query (e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0)) ) - see spatialQueryBuilder for more info
    :param sensor_ids: list of sensor ids to filter by if none then all sensors that match the above filters will be returned
    :return: sensor summaries"""

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensorSummary, col))

        query = db.query(*fields).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)
        query = searchQueryFilters(query, spatial_query_type, geom, sensor_ids)
        query_result = query.all()

        # # must convert wkb to wkt string to be be api friendly
        results = []
        for row in query_result:
            row_as_dict = dict(row._mapping)
            # TODO check if geom column is there?
            try:
                row_as_dict["timestamp_UTC"] = row_as_dict.pop("timestamp")
                row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])
            except KeyError:
                pass
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


# TODO include stationary bool and geom in the query. for stationary sensors use its geom for the bounding boxes in the geojson.
# for non stationary sensors calculate the bounding box from the sensor readings
@sensorSummariesRouter.get("/as-geojson/{start}/{end}/{averaging_frequency}")
def get_geojson_Export_of_sensorSummaries(
    start: str,
    end: str,
    spatial_query_type: str = Query(None),
    geom: str = Query(None),
    averaging_methods: list[str] = Query(default=["mean", "count"]),
    averaging_frequency: str = Query(None),
    sensor_ids: list[int] = Query(default=[]),
):
    """read sensor summaries given a date range and any optional filters then return as geojson
    :param start: start date of tthe query in the format dd-mm-yyyy
    :param end: end date of the query in the format dd-mm-yyyy
    :param spatial_query_type: type of spatial query to perform e.g intersects, contains, within
    :param geom: geometry to use in the spatial query e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))
    :param averaging_methods: list of averaging methods to use e.g mean, count
    :param averaging_frequency: frequency to average the data by e.g H, D, M, Y
    :param sensor_ids: list of sensor ids to filter by, if none then all sensors that match the above filters will be returned
    """

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:
        query = db.query(ModelSensorSummary.sensor_id, ModelSensorSummary.geom, ModelSensorSummary.stationary, ModelSensorSummary.measurement_data).filter(
            ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd
        )
        query = searchQueryFilters(query, spatial_query_type, geom, sensor_ids)
        query_result = query.all()

        # # must convert wkb to wkt string to be be api friendly
        results = []
        for row in query_result:
            row_as_dict = dict(row._mapping)
            # TODO check if geom column is there?
            try:
                row_as_dict["timestamp_UTC"] = row_as_dict.pop("timestamp")
                row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])
            except KeyError:
                pass
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorSummariesToGeoJson(results, averaging_methods, averaging_frequency)
