import datetime as dt

# from celeryWrapper import CeleryWrapper
from core.models import SensorSummaries as ModelSensorSummary
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from routers.helpers.helperfunctions import convertDateRangeStringToDate
from routers.helpers.sensorSummarySharedFunctions import searchQueryFilters
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

sensorSummariesRouter = APIRouter()

db = SessionLocal()

#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorSummariesRouter.get("/read/{start}/{end}")
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
