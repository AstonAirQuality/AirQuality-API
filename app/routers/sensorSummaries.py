import json
import sys
from typing import Iterator

# dependencies for hidden routes
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorSummary as SchemaSensorSummary

# dependencies for exposed routes
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from routers.services.crud.crud import CRUD
from routers.services.enums import averagingMethod, sensorSummaryColumns, spatialQueryType
from routers.services.formatting import convertDateRangeStringToTimestamp, format_sensor_summary_data, format_sensor_summary_to_csv, sensorSummariesToGeoJson
from routers.services.query_building import searchQueryFilters
from routers.services.validation import validate_json_file_size
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns

sensorSummariesRouter = APIRouter()


def generate_json_stream(json_objects: list[dict]) -> Iterator[str]:
    """
    Generates a streaming response for a list of JSON objects.
    Each JSON object is yielded as a separate line in the response.

    Args:
        json_objects (list): A list of JSON objects to stream.
    Yields:
        str: A JSON object as a string, followed by a newline character.
    """
    for obj in json_objects:
        yield json.dumps(obj) + "\n"  # Add newline for line-by-line streaming


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
# TODO add param to read to allow aggregation of sensors into a single measurement_data json
# TODO use ORJSONResponse for better performance
# TODO check filesize of the json response and if it is too large then return a streaming response instead


@sensorSummariesRouter.get("/as-json")
def get_sensorSummaries(
    start: str = Query(..., description="format dd-mm-yyyy"),
    end: str = Query(..., description="format dd-mm-yyyy"),
    columns: list[sensorSummaryColumns] = Query(...),
    measurement_columns: list[SensorMeasurementsColumns] = Query(default=[]),
    join_sensor_type: bool = Query(False, description="if true then the sensor type will be joined to the query"),
    spatial_query_type: spatialQueryType = Query(None),
    geom: str = Query(None, description="format: WKT string. **Required if spatial_query_type is provided**"),
    sensor_ids: list[int] = Query(default=[]),
):
    """
    read sensor summaries given a date range (e.g /read/28-09-2022/30-09-2022) and any optional filters then return a json of sensor summaries
    leave the measurement_columns empty to return the measurement_data as a json string with all the columns

    Args:
        start (str): Start date of the query in the format dd-mm-yyyy.
        end (str): End date of the query in the format dd-mm-yyyy.
        columns (list[sensorSummaryColumns]): list of columns to return from the sensor summaries table
        measurement_columns (list[SensorMeasurementsColumns]): list of sensor measurements columns to return from the sensor summaries measurement_data field
        join_sensor_type (bool): if true then the sensor type will be joined to the query
        spatial_query_type (spatialQueryType): type of spatial query to perform (e.g intersects, contains, within ) - see spatialQueryBuilder for more info
        geom (str): geometry to use in the spatial query (e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0)) ) - see spatialQueryBuilder for more info
        sensor_ids (list[int]): list of sensor ids to filter by if none then all sensors that match the above filters will be returned

    Returns:
        list[dict]: sensor summaries as a list of dictionaries

    Raises:
        HTTPException: if the query fails or if the file size exceeds the limit set in the env
        HTTPException: if the geometry is not a valid WKT string
        HTTPException: if the date range exceeds the maximum allowed days (30 days by default)
    """

    (timestampStart, timestampEnd) = convertDateRangeStringToTimestamp(start, end, max_days=30)
    if measurement_columns:
        deserialize = True  # if measurement columns are provided then we need to deserialize the measurement data
    else:
        deserialize = False  # if no measurement columns are provided then we don't need to deserialize the measurement data

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

        if validate_json_file_size(sys.getsizeof(query_result)):
            # if the query result is too large then return a streaming response
            return StreamingResponse(
                generate_json_stream(format_sensor_summary_data(query_result, deserialize, columns=measurement_columns)),
                media_type="application/json",
            )
        else:
            return format_sensor_summary_data(query_result, deserialize, columns=measurement_columns)
            # return ORJSONResponse(format_sensor_summary_data(query_result, deserialize))

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# TODO include stationary bool and geom in the query. for stationary sensors use its geom for the bounding boxes in the geojson.
# for non stationary sensors calculate the bounding box from the sensor readings
@sensorSummariesRouter.get("/as-geojson")
def get_sensorSummaries_geojson_export(
    start: str = Query(..., description=" format: dd-mm-yyyy"),
    end: str = Query(..., description="format: dd-mm-yyyy"),
    averaging_frequency: str = Query(..., description="examples: 'Min','H', '8H' , 'D', 'M', 'Y'"),
    averaging_methods: list[averagingMethod] = Query(...),
    spatial_query_type: spatialQueryType = Query(None),
    geom: str = Query(None, description="format: WKT string. **Required if spatial_query_type is provided**"),
    sensor_ids: list[int] = Query(default=[]),
):
    """read and aggregate sensor summaries given a date range and any optional filters then return as geojson

    Args:
        start (str): start date of the query in the format dd-mm-yyyy
        end (str): end date of the query in the format dd-mm-yyyy
        averaging_frequency (str): frequency to average the data by e.g H, D, M, Y
        averaging_methods (list[averagingMethod]): list of averaging methods to use e.g mean, count
        spatial_query_type (spatialQueryType): type of spatial query to perform (e.g intersects, contains, within ) - see spatialQueryBuilder for more info
        geom (str): geometry to use in the spatial query (e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0)) ) - see spatialQueryBuilder for more info
        sensor_ids (list[int]): list of sensor ids to filter by, if none then all sensors that match the above filters will be returned
    Returns:
        dict: geojson of sensor summaries
    Raises:
        HTTPException: if the query fails or if the file size exceeds the limit set in the env
        HTTPException: if the geometry is not a valid WKT string
        HTTPException: if the date range exceeds the maximum allowed days (30 days for minutely data, 90 days for hourly data, 365 days for daily data, 1825 days for monthly data, no limit for yearly data)
    """
    max_days = 30
    if averaging_frequency == "Min":
        max_days = 30  # 30 days for minutely data
    elif averaging_frequency == "H":
        max_days = 90  # 3 months for hourly data
    elif averaging_frequency == "D":
        max_days = 365  # 1 year for daily data
    elif averaging_frequency == "M":
        max_days = 1825  # 5 years for monthly data
    elif averaging_frequency == "Y":
        max_days = None  # no limit for yearly data

    (timestampStart, timestampEnd) = convertDateRangeStringToTimestamp(start, end, max_days)

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
        results = format_sensor_summary_data(query_result, deserialize=False)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorSummariesToGeoJson(results, averaging_methods, averaging_frequency)


@sensorSummariesRouter.get("/as-csv")
def get_sensorSummaries_csv_export(
    start: str = Query(..., description="format: dd-mm-yyyy"),
    end: str = Query(..., description="format: dd-mm-yyyy"),
    measurement_columns: list[SensorMeasurementsColumns] = Query(default=[]),
    all_columns: bool = Query(False, description="if true then all columns will be returned from the measurement_data field"),
    sensor_id: int = Query(default=0, description="a sensor id to filter by"),
):
    """read sensor summaries given a date range and one sensor id then return as csv
    Args:
        start (str): start date of the query in the format dd-mm-yyyy
        end (str): end date of the query in the format dd-mm-yyyy
        measurement_columns (list[SensorMeasurementsColumns]): list of sensor measurements columns to return from the sensor summaries measurement_data field
        all_columns (bool): if true then all columns will be returned from the measurement_data field
        sensor_id (int): sensor id to filter by (default is 0 which means no filter)
    Returns:
        StreamingResponse: a streaming response with the csv data
    Raises:
        HTTPException: if the query fails or if the file size exceeds the limit set in the env
        HTTPException: if the date range exceeds the maximum allowed days (30 days by default)
    """

    (timestampStart, timestampEnd) = convertDateRangeStringToTimestamp(start, end, max_days=30)

    if all_columns:
        measurement_columns = [col for col in SensorMeasurementsColumns]
    elif not measurement_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one measurement column or set all_columns to true.",
        )

    try:
        fields = []
        join_models = None

        fields.append(getattr(ModelSensorSummary, "measurement_data").label("measurement_data"))

        filter_expressions = searchQueryFilters(
            filter_expressions=[ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd], spatial_query_type=None, geom=None, sensor_ids=[sensor_id]
        )
        query_result = CRUD().db_get_fields_using_filter_expression(filter_expressions, fields, ModelSensorSummary, join_models)
        response = StreamingResponse(
            iter([format_sensor_summary_to_csv(query_result, measurement_columns)]),
            media_type="text/csv",
        )
        response.headers["Content-Disposition"] = "attachment; filename=sensor_summaries.csv"
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


#################################################################################################################################
#                                                  Hiden Routes                                                                 #
#################################################################################################################################

# from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns as SensorMeasurementsColumns


# @sensorSummariesRouter.post("/fix-sensorSummaries", status_code=status.HTTP_200_OK)
# async def fix_sensorSummaries():
#     """Fixes sensor summaries by updating the measurement_data column to use the new column names.
#     This is a background task that will be run when the /fix-sensorSummaries endpoint is called.
#     It will iterate over all sensor summaries and update the measurement_data column to use the new column names.
#     """

#     try:
#         sensor_summaries = CRUD().db_get_fields_using_filter_expression(
#             filter_expressions=[ModelSensorSummary.sensor_id >= 64, ModelSensorSummary.sensor_id <= 66],
#             fields=[
#                 ModelSensorSummary.timestamp,
#                 ModelSensorSummary.sensor_id,
#                 ModelSensorSummary.geom,
#                 ModelSensorSummary.measurement_count,
#                 ModelSensorSummary.measurement_data,
#                 ModelSensorSummary.stationary,
#             ],
#             model=ModelSensorSummary,
#             join_models=None,
#             first=False,
#             # page=i + 1,
#             # limit=1,
#         )

#         for sensor_summary in sensor_summaries:
#             # # read sensor_summary as a ModelSensorSummary object
#             sensor_summary = ModelSensorSummary(**sensor_summary)
#             if sensor_summary.sensor_id <= 64 or sensor_summary.sensor_id >= 66:  # sensorcommuity sensor 64 to 66
#                 # skip every non sensorcommuity sensor
#                 continue

#             measurement_data = sensor_summary.measurement_data
#             # keep measurement_data as a string and just replace the old column names with the new ones
#             # replace certain values
#             replacements = [
#                 (SensorMeasurementsColumns.PM1.value, SensorMeasurementsColumns.PM1_RAW.value),
#                 (SensorMeasurementsColumns.PM2_5.value, SensorMeasurementsColumns.PM2_5_RAW.value),
#                 (SensorMeasurementsColumns.PM10.value, SensorMeasurementsColumns.PM10_RAW.value),
#                 (SensorMeasurementsColumns.HUMIDITY.value, SensorMeasurementsColumns.AMBIENT_HUMIDITY.value),
#                 (SensorMeasurementsColumns.TEMPERATURE.value, SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value),
#                 (SensorMeasurementsColumns.PRESSURE.value, SensorMeasurementsColumns.AMBIENT_PRESSURE.value),
#             ]
#             for old, new in replacements:
#                 measurement_data = measurement_data.replace(old, new)

#             filters = [ModelSensorSummary.timestamp == sensor_summary.timestamp, ModelSensorSummary.sensor_id == sensor_summary.sensor_id]
#             data = {
#                 "geom": sensor_summary.geom,
#                 "measurement_count": sensor_summary.measurement_count,
#                 "measurement_data": measurement_data,
#                 "stationary": sensor_summary.stationary,
#             }

#             # update the sensor summary with the new measurement_data
#             CRUD().db_update(ModelSensorSummary, filter_expressions=filters, data=data)

#         return {"message": "Sensor summaries updated successfully"}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
