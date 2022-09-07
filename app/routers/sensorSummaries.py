import datetime as dt

# from celeryWrapper import CeleryWrapper
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from routers.helperfunctions import (
    convertDateRangeStringToDate,
    convertWKBtoWKT,
    spatialQueryBuilder,
)

sensorSummariesRouter = APIRouter()

db = SessionLocal()

# TODO query validation check columns exist
# https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#query-parameter-list-multiple-values
@sensorSummariesRouter.get("/read/{start}/{end}/{raw_data}")
def get_sensorSummaries(
    start: str,
    end: str,
    columns: list[str] = Query(default=["sensor_id", "measurement_count", "geom", "timestamp"]),
    geom_type: str = Query(None),
    geom: str = Query(None),
    sensor_ids: list[int] = Query(default=[]),
):
    """read sensor summaries e.g /read/20-08-2022/26-08-2022/false"""

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensorSummary, col))

        query = db.query(*fields).filter(
            ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd
        )
        query = searchQueryFilters(query, geom_type, geom, sensor_ids)
        query_result = query.all()

        # # must convert wkb to wkt string to be be api friendly
        results = []
        for row in query_result:
            row_as_dict = dict(row._mapping)
            row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


@sensorSummariesRouter.post("/create", response_model=SchemaSensorSummary)
def add_sensorSummary(sensorSummary: SchemaSensorSummary):
    sensorSummary = ModelSensorSummary(
        timestamp=sensorSummary.timestamp,
        sensor_id=sensorSummary.sensor_id,
        geom=sensorSummary.geom,
        measurement_count=sensorSummary.measurement_count,
        measurement_data=sensorSummary.measurement_data,
        stationary=sensorSummary.stationary,
    )

    try:
        # wkt string is auto converted to wkb element in the model
        db.add(sensorSummary)
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SensorSummary already exists")
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # converting wkb element to wkt string
    sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    return sensorSummary


@sensorSummariesRouter.put("/update", response_model=SchemaSensorSummary)
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


@sensorSummariesRouter.put("/upsert", response_model=SchemaSensorSummary)
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


# adding search filters
def searchQueryFilters(query: any, geom_type: str, geom: str, sensor_ids: list[str]) -> any:

    if sensor_ids:
        query = query.filter(ModelSensorSummary.sensor_id.in_(sensor_ids))

    # TODO add geom validation to ensure it is a valid geom and raise error if not

    if geom_type and geom is not None:

        query = spatialQueryBuilder(query, ModelSensorSummary, "geom", geom_type, geom)

    return query
