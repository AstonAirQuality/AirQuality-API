# dependencies for hidden routes
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorSummary as SchemaSensorSummary

# dependencies for exposed routes
from fastapi import APIRouter, HTTPException, Query, status
from routers.services.crud.crud import CRUD
from routers.services.enums import (
    averagingMethod,
    sensorSummaryColumns,
    spatialQueryType,
)
from routers.services.formatting import (
    convertDateRangeStringToTimestamp,
    format_sensor_summary_data,
    sensorSummariesToGeoJson,
)
from routers.services.query_building import searchQueryFilters

sensorSummariesRouter = APIRouter()


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
# TODO add param to read to allow aggregation of sensors into a single measurement_data json
@sensorSummariesRouter.get("")
def get_sensorSummaries(
    start: str = Query(..., description="format dd-mm-yyyy"),
    end: str = Query(..., description="format dd-mm-yyyy"),
    columns: list[sensorSummaryColumns] = Query(...),
    join_sensor_type: bool = Query(False, description="if true then the sensor type will be joined to the query"),
    spatial_query_type: spatialQueryType = Query(None),
    geom: str = Query(None, description="format: WKT string. **Required if spatial_query_type is provided**"),
    sensor_ids: list[int] = Query(default=[]),
    deserialize: bool = Query(False, description="if true then the measurement_data json will be deserialized into a python dict"),
):
    """read sensor summaries given a date range (e.g /read/28-09-2022/30-09-2022) and any optional filters then return a json of sensor summaries
    \n :param start: start date of the query in the format dd-mm-yyyy
    \n :param end: end date of the query in the format dd-mm-yyyy
    \n :param columns: list of columns to return from the sensor summaries table
    \n :param join_sensor_type: if true then the sensor type will be joined to the query
    \n :param spatial_query_type: type of spatial query to perform (e.g intersects, contains, within ) - see spatialQueryBuilder for more info
    \n :param geom: geometry to use in the spatial query (e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0)) ) - see spatialQueryBuilder for more info
    \n :param sensor_ids: list of sensor ids to filter by if none then all sensors that match the above filters will be returned
    \n :return: sensor summaries"""

    (timestampStart, timestampEnd) = convertDateRangeStringToTimestamp(start, end)

    try:
        fields = []
        model = ModelSensorSummary
        join_models = None
        for col in columns:
            fields.append(getattr(ModelSensorSummary, col))

        if join_sensor_type:
            fields.append(getattr(ModelSensorType, "name").label("type_name"))
            fields.append(getattr(ModelSensor, "id").label("sensor_id"))
            join_models = [ModelSensor, ModelSensorType]

        filter_expressions = searchQueryFilters([ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd], spatial_query_type, geom, sensor_ids)
        query_result = CRUD().db_get_fields_using_filter_expression(filter_expressions, fields, model, join_models)
        return format_sensor_summary_data(query_result, deserialize)
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# TODO include stationary bool and geom in the query. for stationary sensors use its geom for the bounding boxes in the geojson.
# for non stationary sensors calculate the bounding box from the sensor readings
@sensorSummariesRouter.get("/as-geojson")
def get_sensorSummaries_geojson_export(
    start: str = Query(..., description=" format: dd-mm-yyyy"),
    end: str = Query(..., description="format: dd-mm-yyyy"),
    averaging_frequency: str = Query(..., description="examples: 'H', '8H' , 'D', 'M', 'Y'"),
    averaging_methods: list[averagingMethod] = Query(...),
    spatial_query_type: spatialQueryType = Query(None),
    geom: str = Query(None, description="format: WKT string. **Required if spatial_query_type is provided**"),
    sensor_ids: list[int] = Query(default=[]),
):
    """read sensor summaries given a date range and any optional filters then return as geojson
    \n :param start: start date of tthe query in the format dd-mm-yyyy
    \n :param end: end date of the query in the format dd-mm-yyyy
    \n :param spatial_query_type: type of spatial query to perform e.g intersects, contains, within
    \n :param geom: geometry to use in the spatial query in a WKT format e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))
    \n :param averaging_methods: list of averaging methods to use e.g mean, count
    \n :param averaging_frequency: frequency to average the data by e.g H, D, M, Y
    \n :param sensor_ids: list of sensor ids to filter by, if none then all sensors that match the above filters will be returned
    \n :return: geojson of sensor summaries
    """

    (timestampStart, timestampEnd) = convertDateRangeStringToTimestamp(start, end)

    # append all the columns we want to return from the sensor summary table and the sensor type name from the sensor type table
    fields = []
    columns = ["geom", "stationary", "measurement_data"]
    for col in columns:
        fields.append(getattr(ModelSensorSummary, col))

    fields.append(getattr(ModelSensorType, "name").label("type_name"))
    fields.append(getattr(ModelSensor, "id").label("sensor_id"))

    try:
        filter_expressions = searchQueryFilters([ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd], spatial_query_type, geom, sensor_ids)
        join_models = [ModelSensor, ModelSensorType]
        query_result = CRUD().db_get_fields_using_filter_expression(filter_expressions, fields, ModelSensorSummary, join_models)
        results = format_sensor_summary_data(query_result, False)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorSummariesToGeoJson(results, averaging_methods, averaging_frequency)


#################################################################################################################################
#                                                  Hiden Routes                                                                 #
#################################################################################################################################


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

    CRUD().db_add(ModelSensorSummary, sensorSummary)

    # converting wkb element to wkt string
    # sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    # return sensorSummary


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
# used for background tasks
# @sensorSummariesRouter.put("/", response_model=SchemaSensorSummary)
def update_sensorSummary(sensorSummary: SchemaSensorSummary):
    """updates a sensor summary
    :param sensorSummary: sensor summary to update
    :return: updated sensor summary"""

    filters = [ModelSensorSummary.timestamp == sensorSummary.timestamp, ModelSensorSummary.sensor_id == sensorSummary.sensor_id]
    data = {
        "geom": sensorSummary.geom,
        "measurement_count": sensorSummary.measurement_count,
        "measurement_data": sensorSummary.measurement_data,
        "stationary": sensorSummary.stationary,
    }

    CRUD().db_update(ModelSensorSummary, filters, data)

    # converting wkb element to wkt string
    # sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    # return sensorSummary


# used for background tasks
# @sensorSummariesRouter.put("/upsert", response_model=SchemaSensorSummary)
def upsert_sensorSummary(sensorSummary: SchemaSensorSummary):
    """upserts a sensor summary
    :param sensorSummary: sensor summary to upsert
    :return: upserted sensor summary"""

    try:
        CRUD().db_add(ModelSensorSummary, sensorSummary.dict())
    except HTTPException as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            # update existing sensorSummary
            update_sensorSummary(sensorSummary)

    # converting wkb element to wkt string
    # sensorSummary.geom = convertWKBtoWKT(sensorSummary.geom)

    # return sensorSummary
