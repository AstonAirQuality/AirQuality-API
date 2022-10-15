import datetime as dt
import json  # TODO remove this

from api_wrappers.Sensor_DTO import SensorDTO
from app.core.schema import GeoJsonExport

# from celeryWrapper import CeleryWrapper
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary
from db.database import SessionLocal
from fastapi import HTTPException, Query, status
from psycopg2.errors import UniqueViolation
from routers.helpers.helperfunctions import convertDateRangeStringToDate
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT, spatialQueryBuilder

# from shapely.geometry import Point, Polygon
# from shapely.wkt import loads
from sqlalchemy.exc import IntegrityError

db = SessionLocal()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
# used for background tasks
# @sensorSummariesRouter.post("/create", response_model=SchemaSensorSummary)
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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # converting wkb element to wkt string
    sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    return sensorSummary


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
# used for background tasks
# @sensorSummariesRouter.put("/update", response_model=SchemaSensorSummary)
def update_sensorSummary(sensorSummary: SchemaSensorSummary):

    try:
        db.query(ModelSensorSummary).filter(ModelSensorSummary.timestamp == sensorSummary.timestamp, ModelSensorSummary.sensor_id == sensorSummary.sensor_id,).update(
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


# used for background tasks
# @sensorSummariesRouter.put("/upsert", response_model=SchemaSensorSummary)
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


#################################################################################################################################
#                                              helper functions                                                                 #
#################################################################################################################################

# adding search filters
def searchQueryFilters(query: any, geom_type: str, geom: str, sensor_ids: list[str]) -> any:

    if sensor_ids:
        query = query.filter(ModelSensorSummary.sensor_id.in_(sensor_ids))

    if geom_type and geom is not None:
        query = spatialQueryBuilder(query, ModelSensorSummary, "geom", geom_type, geom)

    return query


def JsonToSensorDTO(results: list) -> list[SensorDTO]:
    # 28-09-2022

    # group sensors by id into a dictionary dict[sensor_id] = list[measurement data]
    sensor_dict = {}
    for sensorSummary in results:
        if sensorSummary["sensor_id"] in sensor_dict:
            sensor_dict[sensorSummary["sensor_id"]].append(sensorSummary["measurement_data"])
        else:
            sensor_dict[sensorSummary["sensor_id"]] = [sensorSummary["measurement_data"]]

    # convert list of measurement data into a sensorDTO
    sensors = []
    for (sensor_id, data) in sensor_dict.items():
        sensors.append(SensorDTO.from_json_list(sensor_id, data))

    return sensors


def sensorSummariesToGeoJson(results: list, averaging_method: str, averaging_frequency: str = "H"):
    sensors = JsonToSensorDTO(results)

    for sensor in sensors:
        geoJson = GeoJsonExport(sensor_id=sensor.id, geojson=sensor.to_geojson(averaging_method, averaging_frequency))

    yield geoJson  # assign new dataframe to coressponding key
