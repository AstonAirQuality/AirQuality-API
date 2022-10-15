import datetime as dt
import json  # TODO remove this

from api_wrappers.Sensor_DTO import SensorDTO

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


# def generateHourlySummaries(sensors: list[SensorDTO], averaging_method: str) -> list[SensorDTO]:
#     # 28-09-2022

#     # TODO in SENSOR DTO add a method to replace the measurement data with the hourly summaries
#     for sensor in sensors:
#         sensor.hourlySummaries(averaging_method)
#         sensor.df.
#     return sensors

# import pandas as pd

# def ConvertDFToAverages(df: pd.DataFrame, averaging_method: str, averaging_frequency: str = "H"):
#     """Given a dataframe with a datetime index, this function will return a dataframe with the hourly summary of the data.
#     :param df: dataframe to convert
#     :param averaging_method: method to use for averaging (e.g. mean, median, min, max)
#     :param averaging_frequency: frequency to use for averaging (e.g. H for hourly, D for daily, M for monthly)
#     """
#     # subset location data from the dataframe
#     df_location = df[["latitude", "longitude"]]

#     # # calculate bounding box of the location data for each hour
#     df_location = df_location.groupby(pd.Grouper(freq=averaging_frequency)).agg(["min", "max"], axis=0)
#     # drop null values
#     df_location = df_location.dropna()

#     # calcualte a bounding box for each hour
#     df_location["bounding_box"] = df_location.apply(
#         lambda row: "POLYGON(({} {}, {} {}, {} {}, {} {},{} {}))".format(
#             row["latitude"]["min"],
#             row["longitude"]["min"],
#             row["latitude"]["min"],
#             row["longitude"]["max"],
#             row["latitude"]["max"],
#             row["longitude"]["max"],
#             row["latitude"]["max"],
#             row["longitude"]["min"],
#             row["latitude"]["min"],
#             row["longitude"]["min"],
#         ),
#         axis=1,
#     )

#     # drop the latitude and longitude columns
#     df_location = df_location.drop(columns=["latitude", "longitude"])
#     # drop dataframe level
#     # df_location.columns = df_location.columns.droplevel(1)

#     # subset sensor data from the dataframe
#     df_measurements = df.drop(columns=["latitude", "longitude"])
#     # calculate the hourly summary of the sensor data
#     df_measurements = df_measurements.groupby(pd.Grouper(freq=averaging_frequency)).agg(averaging_method)

#     # merge the location and sensor data
#     df = pd.merge(df_location, df_measurements, left_index=True, right_index=True, how="outer")

#     return df


if __name__ == "__main__":
    data = json
    file = open("./routers/helpers/testdata.json", "r")
    results = json.load(file)
    file.close()
    sensors = JsonToSensorDTO(results)

    # write to dict to file
    with open("./routers/helpers/testoutput.json", "w") as file:
        file.write(json.dumps(sensors[0].to_geojson()))

    # sensors[0].ConvertDFToAverages("mean", "H")
    # df = sensors[0].df

    # TODO seperate columns fomr multiindex to single index
    # for col in sensors[0].df.groupby(level=0).columns:
    #     print(col)

    # print(sensors[0].df.columns)

    # print(hourlySummary(sensors[0].df, "mean").head())

    # print(hourlySummary(sensors[0].df, "max").head())
    # print(hourlySummary(sensors[0].df, "min").head())
    # print(hourlySummary(sensors[0].df, "sum").head())
