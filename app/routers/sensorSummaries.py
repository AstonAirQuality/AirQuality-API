import datetime as dt

from core.models import SensorSummaries as ModelSensorSummary
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

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
@sensorSummariesRouter.get("/read/{start}/{end}")
def get_sensorSummaries(
    start: str,
    end: str,
    columns: list[str] = Query(default=["sensor_id", "measurement_count", "geom", "timestamp"]),
    geom_type: str = Query(None),
    geom: str = Query(None),
    sensor_ids: list[int] = Query(default=[]),
):
    """read sensor summaries e.g /read/28-09-2022/30-09-2022"""

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensorSummary, col))

        query = db.query(*fields).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)
        query = searchQueryFilters(query, geom_type, geom, sensor_ids)
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


@sensorSummariesRouter.get("/readasgeojson/{start}/{end}")
def get_geojson_Export_of_sensorSummaries(
    start: str,
    end: str,
    geom_type: str = Query(None),
    geom: str = Query(None),
    sensor_ids: list[int] = Query(default=[]),
    averaging_methods: list[str] = Query(default=["mean", "count"]),
    averaging_frequency: str = Query(None),
):
    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:

        query = db.query(ModelSensorSummary.sensor_id, ModelSensorSummary.measurement_data).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)
        query = searchQueryFilters(query, geom_type, geom, sensor_ids)
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
