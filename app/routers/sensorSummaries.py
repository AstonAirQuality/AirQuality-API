import datetime as dt
import json
from typing import Tuple

# from celeryWrapper import CeleryWrapper
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from geoalchemy2 import functions  # used to convert WKBE geometry to GEOSJON
from geoalchemy2.shape import to_shape  # used to convert WKBE geometry to WKT string

# https://stackoverflow.com/questions/57764525/how-to-catch-specific-exceptions-on-sqlalchemy
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

sensorSummariesRouter = APIRouter()

db = SessionLocal()

# https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#query-parameter-list-multiple-values
@sensorSummariesRouter.get("/read-sensorSummaries/{start}/{end}/{raw_data}")
def get_sensorSummaries(
    start: str,
    end: str,
    raw_data: bool,
    geom_type: str | None = None,
    geom: str | None = None,
    sensor_ids: list[int] | None = Query(None),
):
    """read sensor summaries e.g /read-sensorSummaries/20-08-2022/26-08-2022/false"""

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    # TODO refactor this to use dynamic select statement instead of if/else
    try:
        if raw_data == False:
            query = db.query(
                ModelSensorSummary.sensor_id,
                functions.ST_AsGeoJSON(ModelSensorSummary.geom).label("geom"),
                ModelSensorSummary.measurement_count,
            ).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)
        else:
            query = db.query(
                ModelSensorSummary.sensor_id,
                ModelSensorSummary.measurement_data,
            ).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)

        query = searchQueryFilters(query, geom_type, geom, sensor_ids)
        result = query.all()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return result


@sensorSummariesRouter.post("/add-sensorSummary/", response_model=SchemaSensorSummary)
def add_sensorSummary(sensorSummary: SchemaSensorSummary):
    sensorSummary = ModelSensorSummary(
        timestamp=sensorSummary.timestamp,
        sensor_id=sensorSummary.sensor_id,
        geom=sensorSummary.geom,
        measurement_count=sensorSummary.measurement_count,
        measurement_data=sensorSummary.measurement_data,
    )

    try:
        # wkt string is auto converted to wkb element in the model
        db.add(sensorSummary)
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SensorSummary already exists")

    # converting wkb element to wkt string
    sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    return sensorSummary


@sensorSummariesRouter.put("/update-sensorSummary/", response_model=SchemaSensorSummary)
def update_sensorSummary(sensorSummary: SchemaSensorSummary):

    try:
        db.query(ModelSensorSummary).filter(
            ModelSensorSummary.timestamp == sensorSummary.timestamp,
            ModelSensorSummary.sensor_id == sensorSummary.sensor_id,
        ).update(
            {
                ModelSensorSummary.geom: sensorSummary.geom,
                ModelSensorSummary.measurement_count: sensorSummary.measurement_count,
                ModelSensorSummary.measurement_data: sensorSummary.measurement_data,
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # converting wkb element to wkt string
    sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    return sensorSummary


@sensorSummariesRouter.put("/upsert-sensorSummary/", response_model=SchemaSensorSummary)
def upsert_sensorSummary(sensorSummary: SchemaSensorSummary):
    try:
        add_sensorSummary(sensorSummary)
    except HTTPException as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            # update existing sensorSummary
            update_sensorSummary(sensorSummary)

    # converting wkb element to wkt string
    sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    return sensorSummary


# helper functions
def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:
    """converts a date range string to a tuple of datetime objects"""
    try:
        startDate = dt.datetime.strptime(start, "%d-%m-%Y")
        endDate = dt.datetime.strptime(end, "%d-%m-%Y")

    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format {start},{end}")

    return startDate, endDate


def convertWKBtoWKT(element: any) -> str:
    """converts wkb element to human-readable (wkt string)"""
    try:
        if element is not None:
            return to_shape(element).wkt
    except AssertionError:
        return None
    return None


def searchQueryFilters(query: any, geom_type: str, geom: str, sensor_ids: list[str]) -> any:

    if sensor_ids is not None:
        query = query.filter(ModelSensorSummary.sensor_id.in_(sensor_ids))

    # TODO add geom validation to ensure it is a valid geom and raise error if not

    if geom_type and geom is not None:
        match geom_type:
            case "point-intersect":
                query = query.filter(functions.ST_Intersects(geom))
            case "point-within":
                query = query.filter(functions.ST_Within(geom))
            case "point-contains":
                query = query.filter(functions.ST_Contains(geom))
            case "point-overlaps":
                query = query.filter(functions.ST_Overlaps(geom))
            case "point-equals":
                query = query.filter(functions.ST_Equals(geom))
            case "point-disjoint":
                query = query.filter(functions.ST_Disjoint(geom))
            case "point-touches":
                query = query.filter(functions.ST_Touches(geom))
            case "point-crosses":
                query = query.filter(functions.ST_Crosses(geom))
            case _:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid geom_type")

    return query
