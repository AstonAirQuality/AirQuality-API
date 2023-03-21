import datetime as dt
from enum import Enum

from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from routers.helpers.helperfunctions import convertDateRangeStringToDate
from routers.helpers.sensorSummarySharedFunctions import (
    deserializeMeasurementData,
    searchQueryFilters,
    sensorSummariesToGeoJson,
)
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

sensorSummariesRouter = APIRouter()

db = SessionLocal()

#################################################################################################################################
#                                                  Enums                                                                        #
#################################################################################################################################
class sensorSummaryColumns(str, Enum):
    sensor_id = "sensor_id"
    measurement_count = "measurement_count"
    measurement_data = "measurement_data"
    stationary = "stationary"
    geom = "geom"
    timestamp = "timestamp"


class spatialQueryType(str, Enum):
    intersects = "intersects"
    contains = "contains"
    within = "within"
    overlaps = "overlaps"


class averagingMethod(str, Enum):
    mean = "mean"
    count = "count"
    median = "median"
    min = "min"
    max = "max"


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
# TODO add param to read to allow aggregation of sensors into a single measurement_data json
@sensorSummariesRouter.get("")
def get_sensorSummaries(
    start: str = Query(..., description="format dd-mm-yyyy"),
    end: str = Query(..., description="format dd-mm-yyyy"),
    columns: list[sensorSummaryColumns] = Query(...),
    spatial_query_type: spatialQueryType = Query(None),
    geom: str = Query(None, description="format: WKT string. **Required if spatial_query_type is provided**"),
    sensor_ids: list[int] = Query(default=[]),
    deserialize: bool = Query(False, description="if true then the measurement_data json will be deserialized into a python dict"),
):
    """read sensor summaries given a date range (e.g /read/28-09-2022/30-09-2022) and any optional filters then return a json of sensor summaries
    \n :param start: start date of the query in the format dd-mm-yyyy
    \n :param end: end date of the query in the format dd-mm-yyyy
    \n :param columns: list of columns to return from the sensor summaries table
    \n :param spatial_query_type: type of spatial query to perform (e.g intersects, contains, within ) - see spatialQueryBuilder for more info
    \n :param geom: geometry to use in the spatial query (e.g POINT(0 0), POLYGON((0 0, 0 1, 1 1, 1 0, 0 0)) ) - see spatialQueryBuilder for more info
    \n :param sensor_ids: list of sensor ids to filter by if none then all sensors that match the above filters will be returned
    \n :return: sensor summaries"""

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
            if "geom" in row_as_dict:
                row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])

            if "timestamp" in row_as_dict:
                row_as_dict["timestamp_UTC"] = row_as_dict.pop("timestamp")

            if "measurement_data" in row_as_dict and deserialize:
                # convert the json string to a python dict
                row_as_dict["measurement_data"] = jsonable_encoder(deserializeMeasurementData(row_as_dict["measurement_data"]))

            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


# TODO include stationary bool and geom in the query. for stationary sensors use its geom for the bounding boxes in the geojson.
# for non stationary sensors calculate the bounding box from the sensor readings
@sensorSummariesRouter.get("/as-geojson")
def get_geojson_Export_of_sensorSummaries(
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

    (startDate, endDate) = convertDateRangeStringToDate(start, end)

    timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))

    # append all the columns we want to return from the sensor summary table and the sensor type name from the sensor type table
    fields = []
    columns = ["sensor_id", "geom", "stationary", "measurement_data"]
    for col in columns:
        fields.append(getattr(ModelSensorSummary, col))

    fields.append(getattr(ModelSensorType, "name").label("type_name"))
    fields.append(getattr(ModelSensor, "id").label("model_sensor_id"))

    try:
        query = db.query(*fields).select_from(ModelSensorSummary).filter(ModelSensorSummary.timestamp >= timestampStart, ModelSensorSummary.timestamp <= timestampEnd)

        # join the sensor type table to get the sensor type name
        query = query.join(ModelSensor, ModelSensorSummary.sensor_id == ModelSensor.id, isouter=True)
        query = query.join(ModelSensorType, ModelSensor.type_id == ModelSensorType.id, isouter=True)

        query = searchQueryFilters(query, spatial_query_type, geom, sensor_ids)
        query_result = query.all()

        # # must convert wkb to wkt string to be be api friendly
        results = []
        for row in query_result:
            row_as_dict = dict(row._mapping)
            if "geom" in row_as_dict:
                row_as_dict["geom"] = convertWKBtoWKT(row_as_dict["geom"])

            if "timestamp" in row_as_dict:
                row_as_dict["timestamp_UTC"] = row_as_dict.pop("timestamp")

            # # add the sensor type name to the sensor id to make it easier to identify the sensor type in the geojson
            # if "type_name" in row_as_dict:
            #     row_as_dict["sensor_id"] = str(row_as_dict["sensor_id"]) + "_" + row_as_dict.pop("type_name")

            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorSummariesToGeoJson(results, averaging_methods, averaging_frequency)
