import datetime as dt
import json
from typing import Tuple

from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary
from database import SessionLocal
from fastapi import APIRouter, HTTPException, status
from geoalchemy2 import functions  # used to convert WKBE geometry to GEOSJON
from geoalchemy2.shape import to_shape  # used to convert WKBE geometry to WKT string
from nomans_functions import Nomans

# https://stackoverflow.com/questions/57764525/how-to-catch-specific-exceptions-on-sqlalchemy
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

# fetching active sensors from the database
from routers.sensors import get_active_sensors, sensor_id_from_lookup_id

sensorSummariesRouter = APIRouter()

db = SessionLocal()

# TODO add fetching active sensors then for each type use the appropriate api wrapper to fetch data
@sensorSummariesRouter.put("/upsert-scheduled-ingest-active-sensors/{start}/{end}")
def upsert_scheduled_ingest_active_sensors(start: str, end: str):
    """must be valid date string e.g. 2022-08-20,2022-08-26"""

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    api = Nomans()

    sensorsPairs = get_active_sensors()

    # group sensors by type into a dictionary dict[sensor_type] = [list of sensors]
    sensor_dict = {}
    for (key, value) in sensorsPairs:

        if key in sensor_dict:
            sensor_dict[key].append(value)
        else:
            sensor_dict[key] = [value]

    succesful_writes = {}
    # for each sensor type, fetch the data from the api and write to the database
    for (key, value) in sensor_dict.items():
        match key:
            case 1:
                for sensorSummary in api.fetch_plume_data(startDate, endDate, value):
                    try:
                        # TODO map lookup_id to sensor_id
                        lookupid = sensorSummary.sensor_id
                        (sensorSummary.sensor_id,) = sensor_id_from_lookup_id(str(lookupid))

                        upsert_sensorSummary(sensorSummary)

                        succesful_writes[str(sensorSummary.timestamp) + "_" + str(lookupid)] = True
                    except Exception:
                        succesful_writes[str(sensorSummary.timestamp) + "_" + str(lookupid)] = False
            case 2:
                continue
            case 3:
                continue

    # return the id and sensor id of the summaries that were successfully written to the database

    return succesful_writes


# https://gis.stackexchange.com/questions/233184/converting-geoalchemy2-elements-wkbelement-to-wkt
@sensorSummariesRouter.get("/read-sensorSummaries/{start}/{end}")
def get_sensorSummaries(start: str, end: str):

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    try:
        result = (
            db.query(
                ModelSensorSummary.timestamp,
                ModelSensorSummary.sensor_id,
                functions.ST_AsGeoJSON(ModelSensorSummary.geom).label("geom"),
                ModelSensorSummary.measurement_data,
            )
            .filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)
            .all()
        )
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

    # wkt string is auto converted to wkb element in the model
    db.add(sensorSummary)
    db.commit()

    # converting wkb element to wkt string
    if sensorSummary.geom is not None:
        sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    # sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    return sensorSummary


@sensorSummariesRouter.put("/upsert-sensorSummary/", response_model=SchemaSensorSummary)
def upsert_sensorSummary(sensorSummary: SchemaSensorSummary):
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
    # if the sensorSummary already exists, update it
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
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
        else:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # converting wkb element to wkt string
    if sensorSummary.geom is not None:
        sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    return sensorSummary

    # return None


def convertDateRangeStringToDate(start: str, end: str) -> Tuple[dt.datetime, dt.datetime]:
    try:
        startDate = dt.datetime.strptime(start, "%Y-%m-%d")
        endDate = dt.datetime.strptime(end, "%Y-%m-%d")

    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format")

    return startDate, endDate


# {
#   "timestamp": 0,
#   "geom": null,
#   "measurement_count": 0,
#   "measurement_data": "{\"name\":\"john\",\"age\":22,\"class\":\"mca\"}",
#   "sensor_id": 51
# }
