# dependacies
import json
import math

# Dependancies for Haversine formula
from math import asin, cos, radians, sin, sqrt
from typing import Any, Iterator, Tuple

import numpy as np
import pandas as pd
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary


class SensorDTO:
    """Sensor Data transfer object, used to transfer and process data from api wrappers to the database and API"""

    def __init__(self, id_, merged_df: pd.DataFrame):
        """Initialises the SensorDTO object
        :param id_: sensor id
        :param merged_df: dataframe of sensor data"""
        self.id = id_
        self.df = merged_df

    def __iter__(self):
        """Iterator for the SensorDTO object
        :return: a tuple of the sensor id and the sensor summary"""
        return iter((self.id, self.df))

    def to_json(self, df: pd.DataFrame) -> str:
        """Converts the dataframe to a json string.
        :param df: dataframe of sensor data
        :return: json string of the dataframe"""
        return df.to_json(orient="index")

    def create_sensor_summaries(self, stationary_box: str) -> Iterator[SchemaSensorSummary]:
        """Creates a summary of the sensor data to be written to the database. skips generating a geometry if the sensor has a stationary box
        param stationary_box: geometry string of the stationary box
        :return: iterator of the sensor summaries
        """
        data_dict = self.dataframe_to_dict(self.df)
        # sensor_summaries = []

        for timestampKey in data_dict:
            df = data_dict[timestampKey]
            stationaryBool = False
            if stationary_box is None:
                geometry_string = self.generate_geomertyString(df)
            else:
                # TODO if df has location data, check if it is within the 2.5km from the centre point of the stationary box.
                # If not then do not use the stationary box

                (df, geometry_string) = self.is_within_stationary_box(df, stationary_box, threshold=2)

                stationaryBool = True if geometry_string == stationary_box else False

            # summaryArray = [timestamp_start,bounding_box,measurement_count,data_json]
            sensorSummary = SchemaSensorSummary(
                timestamp=timestampKey,
                sensor_id=self.id,
                geom=geometry_string,
                measurement_count=len(df.index.values),
                measurement_data=self.to_json(df),
                stationary=stationaryBool,
            )  # inserting row into temp array
            yield sensorSummary  # assign new dataframe to coressponding key

        # return sensor_summaries

    def generate_geomertyString(self, df: pd.DataFrame):
        """generates a geometry string from a dataframe of sensor data
        :param df: dataframe of sensor data
        :return: geometry string
        """
        try:
            if math.isnan(df["latitude"].min()):
                raise AssertionError("No location data found")

            min_y = df["latitude"].min()
            max_y = df["latitude"].max()

            min_x = df["longitude"].min()
            max_x = df["longitude"].max()

            # POLYGON(minx miny, minx Maxy, maxx Maxy, maxx miny, minx miny)
            geometry_string = "POLYGON(({} {}, {} {}, {} {}, {} {},{} {}))".format(min_x, min_y, min_x, max_y, max_x, max_y, max_x, min_y, min_x, min_y)

        except AssertionError:
            geometry_string = None

        return geometry_string

    def get_centre_of_polygon(self, geometryString: str):
        """gets the centre point of a polygon string, by averaging the x and y coordinates
        :param geometryString: string of the geometry of the polygon (e.g POLYGON ((long,lat)) )
        :return: tuple of the centre point (long,lat)
        """
        latitude = np.array([])
        longitude = np.array([])

        for coordsPair in geometryString.split("POLYGON ((")[1].split("))")[0].split(", "):
            long, lat = coordsPair.split(" ")
            latitude = np.append(latitude, float(lat))
            longitude = np.append(longitude, float(long))

        return longitude.mean(), latitude.mean()

    def is_within_stationary_box(self, df: pd.DataFrame, boxGeometry: str, threshold: float = 2) -> Tuple[pd.DataFrame, str]:
        """replaces the gps coordinates of the dataframe with the given coordinates if the distance between the two is less than 2km
        or if the coordinates are not valid/NaN

        :param df: dataframe to check
        :param boxGeometry: geometry string of the stationary box
        :param threshold: threshold distance in km to check if the coordinates are within the stationary box, default is 2km
        :return: dataframe, with the coordinates replaced only if the distance is less than 2km or if the coordinates are not valid/NaN. Bounding box string
        """

        (centerPoint_long, centerPoint_lat) = self.get_centre_of_polygon(boxGeometry)

        boundingBoxString = boxGeometry

        # if the dataframe has no location data, then replace the dataframe with the given coordinates
        if math.isnan(df["latitude"].min()):
            df["latitude"] = centerPoint_lat
            df["longitude"] = centerPoint_long
        else:
            # if locations are within the threshold then replace the dataframe with the given coordinates
            if self.haversine(centerPoint_long, centerPoint_lat, df["longitude"].min(), df["latitude"].max()) < threshold:
                df["latitude"] = centerPoint_lat
                df["longitude"] = centerPoint_long
            elif self.haversine(centerPoint_long, centerPoint_lat, df["longitude"].max(), df["latitude"].max()) < threshold:
                df["latitude"] = centerPoint_lat
                df["longitude"] = centerPoint_long
            # if locations are not within the threshold then generate a new bounding box
            else:
                boundingBoxString = self.generate_geomertyString(df)

        return df, boundingBoxString

    def haversine(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Calculate the great circle distance in kilometers between two points on the earth (specified in decimal degrees)
        :reference: https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        :param lon1: longitude of point 1
        :param lat1: latitude of point 1
        :param lon2: longitude of point 2
        :param lat2: latitude of point 2
        :return: Distance in km as a float
        """

        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6372.8  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    def dataframe_to_dict(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """converts a dataframe to a dictionary of dataframes with timestamp keys.
        :param df: dataframe to convert
        :return: dictionary of dataframes with timestamp keys
        """
        data = {}  # intialise empty dictionary to store each day of records

        # using the dates which are already supplied. This strategy in the line below converts them and rounds down to date using 'd' flag
        # This strategy (line below) will keep just the date
        df["day"] = pd.to_datetime(df.index, dayfirst=True, errors="coerce").date

        # remove any duplicate dates or only extract the unique ones
        the_unique_dates = df["day"].unique()

        # splitting the dataframe into separate days
        # for each day in unique dates set:
        for day in the_unique_dates:
            try:
                # In my code below I assign the subset of records to a new dataframe called dft
                # create 'midnight' timestamps
                timestampKey = int((pd.to_datetime(day, errors="coerce")).timestamp())

                # select the records for this day
                # TODO - this .copy() might be a problem since pandas is not thread safe
                df_day_subset = df[df["day"] == day].copy(deep=False)

                # drop the day column to save memory (we don't need this anymore)
                df_day_subset.drop("day", axis=1, inplace=True)
                df_day_subset.set_index("timestamp", inplace=True)

                data[timestampKey] = df_day_subset

            except KeyError as e:
                # TODO raise exception? or continue?
                print(e)

        return data

    ####################################################################################################################################
    # NOTE: these functions below are only used to convert and process sensor summaries from the postgres database to a sensorDTO object.
    #####################################################################################################################################

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
        df_location = df[["latitude", "longitude"]]

        # # calculate bounding box of the location data for each hour
        df_location = df_location.groupby(pd.Grouper(freq="H")).agg(["min", "max"])
        # drop null values
        df_location = df_location.dropna()

        # subset sensor data from the dataframe
        df_measurements = df.drop(columns=["latitude", "longitude", "timestamp"])
        measurements_columns = df_measurements.columns.to_list()

        # calculate the averages  of the sensor data
        df_measurements = df_measurements.groupby(pd.Grouper(freq=averaging_frequency)).agg(averaging_methods)

        # merge the location and sensor data
        self.df = pd.merge(df_location, df_measurements, left_index=True, right_index=True, how="outer")

        return measurements_columns

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

            # get the bounding box if coordinates are available else assign empty list
            if math.isnan(row["latitude"]["min"]):
                bounding_box = None

            else:
                bounding_box = [
                    [row["longitude"]["min"], row["latitude"]["min"]],
                    [row["longitude"]["max"], row["latitude"]["min"]],
                    [row["longitude"]["max"], row["latitude"]["max"]],
                    [row["longitude"]["min"], row["latitude"]["max"]],
                    [row["longitude"]["min"], row["latitude"]["min"]],
                ]

            # add the bounding box to the feature
            feature["geometry"]["coordinates"] = [bounding_box]

            # assign properties (measurement values) to the feature
            for col in measurement_columns:
                for method in averaging_methods:
                    feature["properties"][col + method] = row[col][method] if not math.isnan(row[col][method]) else None

            # add datetime to the feature
            feature["properties"]["datetime_UTC"] = row.name

            geojson["features"].append(feature)

        return geojson

    @staticmethod
    def JsonStringToDataframe(jsonb: tuple) -> pd.DataFrame:
        """converts a jsonb string to a dataframe
        :param jsonb: jsonb string
        :return: dataframe
        """
        # Preparing the json string to be read into dataframe
        my_json_string = str(jsonb)
        my_json_string = my_json_string.replace("'", '"').replace("None", "null")

        # reading the JSON data using json.loads(json string)
        # converting json dataset from dictionary to dataframe
        dict_data = json.loads(my_json_string)
        df = pd.DataFrame.from_dict(dict_data, orient="index")

        # TODO refractor into a function
        # set column name as timestamp and datatype to integer
        df.index.name = "timestamp"

        # add date col and set to index
        df.insert(0, "date", pd.to_datetime(df.index, unit="s", errors="coerce"))
        df.reset_index(inplace=True)
        df.set_index("date", drop=True, inplace=True)

        return df

    @staticmethod
    def from_json_list(sensor_id: str, values: list) -> Any:
        """Factory method to create SensorDTO from json list.
        :param sensor_id: sensor id
        :param values: list of values (JSON converted dataframes)
        :return: SensorDTO
        """
        dfList = []
        for value in values:
            dfList.append(SensorDTO.JsonStringToDataframe(value))

        df = pd.concat(dfList)

        return SensorDTO(sensor_id, df)
