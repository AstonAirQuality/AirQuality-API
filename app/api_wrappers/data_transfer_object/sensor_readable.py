# dependacies
import json
import math

# Dependancies for Haversine formula
from typing import Any, Iterator, Tuple

import numpy as np
import pandas as pd
from api_wrappers.data_transfer_object.sensorDTO import SensorDTO
from core.schema import SensorSummary as SchemaSensorSummary


class SensorReadable(SensorDTO):
    """Readable Sensor Data Transfer Object, used to transfer and process data between api wrappers, main API and the database"""

    def __init__(self, id_, merged_df: pd.DataFrame):
        """Initialises the SensorReadable object
        :param id_: sensor id
        :param merged_df: dataframe of sensor data"""
        super().__init__(id_, merged_df)

    def ConvertDFToAverages(self, averaging_methods: list[str], averaging_frequency: str = "H") -> list[str]:
        """converts the object's dataframe to a list of averages based on the averaging method and frequency

        Given a dataframe with a datetime index, this function will return a dataframe with the hourly summary of the data.

        :param df: dataframe to convert
        :param averaging_method: method to use for averaging (e.g. mean, median, min, max)
        :param averaging_frequency: frequency to use for averaging (e.g. H for hourly, D for daily, M for monthly)
        :return: dataframe with the hourly summary of the data
        """
        df = self.df
        # subset location data from the dataframe
        df_location = df[["latitude", "longitude", "boundingBox"]]

        # # calculate bounding box of the location data for each hour
        df_location = df_location.groupby(pd.Grouper(freq="H")).agg({"latitude": ["min", "max"], "longitude": ["min", "max"], "boundingBox": ["first"]})

        # print(df_location.head(-1))
        # # drop null values
        # df_location = df_location.dropna()

        # subset sensor data from the dataframe
        df_measurements = df.drop(columns=["latitude", "longitude", "boundingBox", "timestamp"])
        measurements_columns = df_measurements.columns.to_list()

        # calculate the averages  of the sensor data
        df_measurements = df_measurements.groupby(pd.Grouper(freq=averaging_frequency)).agg(averaging_methods)

        # merge the location and sensor data
        self.df = pd.merge(df_location, df_measurements, left_index=True, right_index=True, how="outer")

        return measurements_columns

    def generate_geojson_coords(self, min_long: float, min_lat: float, max_long: float, max_lat: float) -> list[list[float]]:
        """generate a geojson coordinate list from the min and max longitudes and latitudes
        :param min_long: minimum longitude
        :param min_lat: minimum latitude
        :param max_long: maximum longitude
        :param max_lat: maximum latitude
        :return: list of coordinates
        """
        return [[min_long, min_lat], [min_long, max_lat], [max_long, max_lat], [max_long, min_lat], [min_long, min_lat]]

    def to_geojson(self, averaging_methods: list[str], averaging_frequency: str = "H") -> dict[str, Any]:
        """Converts a dataframe to a geojson object
        :param df: dataframe to convert
        :param averaging_method: method to use for averaging (e.g. mean, median, min, max)
        :param averaging_frequency: frequency to use for averaging (e.g. H for hourly, D for daily, M for monthly)
        :return: geojson dictionary"""

        measurement_columns = self.ConvertDFToAverages(averaging_methods, averaging_frequency)

        geojson = {"type": "FeatureCollection", "features": []}

        # loop through each row in the dataframe and convert each row to geojson feature format
        for _, row in self.df.iterrows():

            # feature
            feature = {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": []}}

            # check if a stationary bounding box is available from the data, otherwise generate one from the min and max longitudes and latitudes
            if row["boundingBox"]["first"] is None:

                # generate bounding box if coordinates are available else assign empty list
                if math.isnan(row["latitude"]["min"]):
                    bounding_box = None

                else:
                    bounding_box = self.generate_geojson_coords(
                        min_long=row["longitude"]["min"],
                        min_lat=row["latitude"]["min"],
                        max_long=row["longitude"]["max"],
                        max_lat=row["latitude"]["max"],
                    )

                # add the bounding box to the feature
                feature["geometry"]["coordinates"] = [bounding_box]
            else:
                # extract the min and max coords from the polygon POLYGON(minx miny, minx Maxy, maxx Maxy, maxx miny, minx miny)
                coords = row["boundingBox"]["first"].split("(")[2].split(",")
                # remove any whitespace after the comma
                coords = [x.strip() for x in coords]
                min_long, min_lat = (float(x) for x in coords[0].split(" "))
                max_long, max_lat = (float(x) for x in coords[2].split(" "))

                feature["geometry"]["coordinates"] = [self.generate_geojson_coords(min_long, min_lat, max_long, max_lat)]

            # assign properties (measurement values) to the feature
            for col in measurement_columns:
                for method in averaging_methods:
                    feature["properties"][col + "_" + method] = row[col][method] if not math.isnan(row[col][method]) else None

            # add datetime to the feature
            feature["properties"]["datetime_UTC"] = row.name

            geojson["features"].append(feature)

        return geojson

    @staticmethod
    def JsonStringToDataframe(jsonb: str, boundingBox: str) -> pd.DataFrame:
        """converts a jsonb string to a dataframe
        :param jsonb: jsonb string
        :param boundingBox: string of polygon
        :return: dataframe
        """
        # Preparing the json string to be read into dataframe
        my_json_string = str(jsonb)
        my_json_string = my_json_string.replace("'", '"').replace("None", "null")

        # reading the JSON data using json.loads(json string)
        # converting json dataset from dictionary to dataframe
        dict_data = json.loads(my_json_string)
        df = pd.DataFrame.from_dict(dict_data, orient="index")

        # TODO refactor into a function
        # set column name as timestamp and datatype to integer
        df.index.name = "timestamp"

        # add date col and set to index
        df.insert(0, "date", pd.to_datetime(df.index, unit="s", errors="coerce"))
        df.reset_index(inplace=True)
        df.set_index("date", drop=True, inplace=True)

        # amend dtypes for timestamp, latitude and longitude
        df = df.astype({"timestamp": "int64", "latitude": "float64", "longitude": "float64"})

        # add bounding box to dataframe for stationary sensors
        if boundingBox:
            df["boundingBox"] = boundingBox
        else:
            df["boundingBox"] = None
        return df

    @staticmethod
    def from_json_list(sensor_id: str, values: list) -> Any:
        """Factory method to create SensorReadable from json list and bounding box geometry string.
        :param sensor_id: sensor id
        :param values: list of dictionaries {json_: JSON string converted dataframes, boundingBox : bounding box geometry}
        :return: SensorReadable
        """
        dfList = []
        for sensor_dict in values:
            dfList.append(SensorReadable.JsonStringToDataframe(sensor_dict["json_"], sensor_dict["boundingBox"]))

        df = pd.concat(dfList)

        return SensorReadable(sensor_id, df)

    # @staticmethod
    # def JsonStringToDataframe(jsonb: tuple) -> pd.DataFrame:
    #     """converts a jsonb string to a dataframe
    #     :param jsonb: jsonb string
    #     :return: dataframe
    #     """
    #     # Preparing the json string to be read into dataframe
    #     my_json_string = str(jsonb)
    #     my_json_string = my_json_string.replace("'", '"').replace("None", "null")

    #     # reading the JSON data using json.loads(json string)
    #     # converting json dataset from dictionary to dataframe
    #     dict_data = json.loads(my_json_string)
    #     df = pd.DataFrame.from_dict(dict_data, orient="index")

    #     # TODO refractor into a function
    #     # set column name as timestamp and datatype to integer
    #     df.index.name = "timestamp"

    #     # add date col and set to index
    #     df.insert(0, "date", pd.to_datetime(df.index, unit="s", errors="coerce"))
    #     df.reset_index(inplace=True)
    #     df.set_index("date", drop=True, inplace=True)

    #     return df

    # @staticmethod
    # def from_json_list(sensor_id: str, values: list) -> Any:
    #     """Factory method to create SensorReadable from json list.
    #     :param sensor_id: sensor id
    #     :param values: list of values (JSON converted dataframes)
    #     :return: SensorReadable
    #     """
    #     dfList = []
    #     for value in values:
    #         dfList.append(SensorReadable.JsonStringToDataframe(value))

    #     df = pd.concat(dfList)

    #     return SensorReadable(sensor_id, df)
