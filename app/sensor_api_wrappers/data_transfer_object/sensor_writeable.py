# dependacies
import datetime as dt
import json
import math

# Dependancies for Haversine formula
from math import asin, cos, radians, sin, sqrt
from typing import Any, Iterator, Tuple

import numpy as np
import pandas as pd
from core.schema import SensorSummary as SchemaSensorSummary
from sensor_api_wrappers.data_transfer_object.sensorDTO import SensorDTO


class SensorWritable(SensorDTO):
    """Sensor Data Transfer Object, used to transfer and process data between api wrappers, main API and the database"""

    def __init__(self, id_, merged_df: pd.DataFrame):
        """Initialises the SensorDTO object
        :param id_: sensor id
        :param merged_df: dataframe of sensor data"""
        super().__init__(id_, merged_df)

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

        # if the dataframe is empty or None then yield an empty sensor summary with an error message
        if self.df is None or self.df.empty:
            yield SchemaSensorSummary(
                timestamp=int(dt.datetime.utcnow().timestamp()), sensor_id=self.id, geom=None, measurement_count=0, measurement_data='{"message": "no data found"}', stationary=False
            )
        else:
            data_dict = self.dataframe_to_dict(self.df)
            # sensor_summaries = []

            for timestampKey in data_dict:
                df = data_dict[timestampKey]
                stationaryBool = False
                if stationary_box is None:
                    geometry_string = self.generate_geomertyString(df)
                    # if there is no location data then yield an empty sensor summary with an error message
                    if geometry_string is None:
                        yield SchemaSensorSummary(
                            timestamp=timestampKey,
                            sensor_id=self.id,
                            geom=None,
                            measurement_count=0,
                            measurement_data='{"message": "no location data found or an error occured while generating the geometry string"}',
                            stationary=False,
                        )
                        continue

                else:
                    (df, geometry_string) = self.is_within_stationary_box(df, stationary_box, threshold=2)

                    stationaryBool = True if geometry_string == stationary_box else False

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

    def generate_geomertyString(self, df: pd.DataFrame) -> str:
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

            # if there is only one location, then create a bounding box of 0.0001 degrees
            if min_y == max_y and min_x == max_x:
                min_y -= 0.0001
                max_y += 0.0001
                min_x -= 0.0001
                max_x += 0.0001

            # POLYGON(minx miny,minx Maxy,maxx Maxy,maxx miny,minx miny)
            geometry_string = "POLYGON(({} {},{} {},{} {},{} {},{} {}))".format(min_x, min_y, min_x, max_y, max_x, max_y, max_x, min_y, min_x, min_y)

        except AssertionError:
            geometry_string = None

        return geometry_string

    def get_centre_of_polygon(self, geometryString: str) -> Tuple[float, float]:
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
        if not df.columns.__contains__("latitude") or math.isnan(df["latitude"].min()):
            df["latitude"] = centerPoint_lat
            df["longitude"] = centerPoint_long
        else:
            # check if the center point is within the threshold of the min coordinates, if so then replace the coordinates with the stationary box coordinates
            if self.haversine(centerPoint_long, centerPoint_lat, df["longitude"].min(), df["latitude"].min()) < threshold:
                df["latitude"] = centerPoint_lat
                df["longitude"] = centerPoint_long
            # check if the center point is within the threshold of the max coordinates, if so then replace the coordinates with the stationary box coordinates
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
