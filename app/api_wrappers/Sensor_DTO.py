# dependacies
import json
import math
from typing import Any, Iterator

import pandas as pd
from core.models import SensorSummaries as ModelSensorSummary
from core.schema import SensorSummary as SchemaSensorSummary


class SensorDTO:
    """Data transfer object for sensor data. (database-application)

    Example Usage:

    """

    def __init__(self, id_, merged_df: pd.DataFrame):
        self.id = id_
        self.df = merged_df

    def __iter__(self):
        return iter((self.id, self.df))

    def to_json(self, df: pd.DataFrame) -> str:
        """Converts the dataframe to a json string."""
        return df.to_json(orient="index")

    def create_sensor_summaries(self, stationary_box: str) -> Iterator[SchemaSensorSummary]:
        """Creates a summary of the sensor data to be written to the database. skips generating a geometry if the sensor has a stationary box"""
        data_dict = self.dataframe_to_dict(self.df)
        # sensor_summaries = []

        for timestampKey in data_dict:
            df = data_dict[timestampKey]
            stationaryBool = False
            if stationary_box is None:
                try:
                    if math.isnan(df["latitude"].min()):
                        geometry_string = "NULL"
                        raise Exception("No data found")

                    min_y = df["latitude"].min()
                    max_y = df["latitude"].max()

                    min_x = df["longitude"].min()
                    max_x = df["longitude"].max()

                    # POLYGON(minx miny, minx Maxy, maxx Maxy, maxx miny, minx miny)
                    geometry_string = "POLYGON(({} {}, {} {}, {} {}, {} {},{} {}))".format(
                        min_x, min_y, min_x, max_y, max_x, max_y, max_x, min_y, min_x, min_y
                    )

                except Exception as e:
                    geometry_string = None
            else:
                geometry_string = stationary_box
                stationaryBool = True
                # subset dataframe to only include the columns measurement columns
                df = df[df.columns.difference(["latitude", "longitude"])]

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

    def dataframe_to_dict(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """converts a dataframe to a dictionary of dataframes with timestamp keys."""

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

                # drop the day column to save space (we don't need this anymore)
                df_day_subset.drop("day", axis=1, inplace=True)
                df_day_subset.set_index("timestamp", inplace=True)

                data[timestampKey] = df_day_subset

            except KeyError as e:
                # TODO raise exception? or continue?
                print(e)

        return data

    @staticmethod
    def JsonStringToDataframe(jsonb: tuple) -> pd.DataFrame:

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
        """Factory method to create SensorDTO from json list."""
        dfList = []
        for value in values:
            dfList.append(SensorDTO.JsonStringToDataframe(value))

        df = pd.concat(dfList)

        return SensorDTO(sensor_id, df)
