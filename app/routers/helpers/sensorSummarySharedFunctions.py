from api_wrappers.Sensor_DTO import SensorDTO
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import GeoJsonExport
from core.schema import SensorSummary as SchemaSensorSummary
from db.database import SessionLocal
from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT, spatialQueryBuilder
from sqlalchemy.exc import IntegrityError

db = SessionLocal()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
# used for background tasks
# @sensorSummariesRouter.post("/", response_model=SchemaSensorSummary)
def add_sensorSummary(sensorSummary: SchemaSensorSummary):
    """adds a sensor summary
    :param sensorSummary: sensor summary to add
    :return: sensor summary added"""

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
# @sensorSummariesRouter.put("/", response_model=SchemaSensorSummary)
def update_sensorSummary(sensorSummary: SchemaSensorSummary):
    """updates a sensor summary
    :param sensorSummary: sensor summary to update
    :return: updated sensor summary"""
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
    """upserts a sensor summary
    :param sensorSummary: sensor summary to upsert
    :return: upserted sensor summary"""
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
def searchQueryFilters(query: any, spatial_query_type: str, geom: str, sensor_ids: list[str]) -> any:
    """applies search filters to the query
    :param query: query to apply filters to
    :param spatial_query_type: type of geometry filter query to use (intersects, contains, within)
    :param geom: geometry to filter by
    :param sensor_ids: list of sensor ids to filter by
    :return: query with filters applied"""

    if sensor_ids:
        query = query.filter(ModelSensorSummary.sensor_id.in_(sensor_ids))

    if spatial_query_type and geom is not None:
        query = spatialQueryBuilder(query, ModelSensorSummary, "geom", spatial_query_type, geom)

    return query


def JsonToSensorDTO(results: list) -> list[SensorDTO]:
    """converts a list of sensor summaries into a list of sensor DTOs.
    :param results: list of sensor summaries
    :return: list of sensor DTOs"""

    # group sensors by id into a dictionary dict[sensor_id] = dict{json_ : measurement data, "boundingBox": geom}
    sensor_dict = {}
    for sensorSummary in results:
        if sensorSummary["sensor_id"] in sensor_dict:
            sensor_dict[sensorSummary["sensor_id"]].append({"json_": sensorSummary["measurement_data"], "boundingBox": sensorSummary["geom"] if sensorSummary["stationary"] == True else None})
        else:
            sensor_dict[sensorSummary["sensor_id"]] = [{"json_": sensorSummary["measurement_data"], "boundingBox": sensorSummary["geom"] if sensorSummary["stationary"] == True else None}]

    # convert list of measurement data into a sensorDTO
    sensors = []
    for (sensor_id, data) in sensor_dict.items():
        sensors.append(SensorDTO.from_json_list(sensor_id, data))

    return sensors


def sensorSummariesToGeoJson(results: list, averaging_methods: list[str], averaging_frequency: str = "H"):
    """converts a list of sensor summaries into geojsons
    :param results: list of sensor summaries
    :param averaging_method: method of averaging the sensor summaries
    :param averaging_frequency: frequency of averaging the sensor summaries
    :return: list of geojsons"""

    sensors = JsonToSensorDTO(results)

    geoJsons = []
    for sensor in sensors:
        geoJsons.append(GeoJsonExport(sensorid=sensor.id, geojson=sensor.to_geojson(averaging_methods, averaging_frequency)))

    return geoJsons
