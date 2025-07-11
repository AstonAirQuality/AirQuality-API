import datetime as dt
from os import environ as env
from typing import Iterator

# sensor summary
from core.schema import Sensor as SchemaSensor
from core.schema import SensorSummary as SchemaSensorSummary
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.factories.purpleAir_factory import PurpleAirFactory
from sensor_api_wrappers.concrete.factories.sensorCommunity_factory import SensorCommunityFactory
from sensor_api_wrappers.concrete.factories.zephyr_factory import ZephyrFactory


class SensorFactoryWrapper:
    """Wrapper class for all the different sensor factories, which fetch sensor data from the different apis"""

    def __init__(self):
        """initialise the api wrappers and load the environment variables"""
        load_dotenv()
        self.zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])
        self.scf = SensorCommunityFactory(env["SC_USERNAME"], env["SC_PASSWORD"])
        self.pf = PlumeFactory(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])
        self.paf = PurpleAirFactory(env["PURPLE_AIR_TOKEN_URL"], env["PURPLE_AIR_REFERER_URL"], env["PURPLE_AIR_API_KEY"])

    def fetch_plume_platform_lookupids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches a list of plume sensor lookup_ids from a list of serial numbers

        Args:
            serial_nums (list[str]): A list of serial numbers to fetch lookup_ids for.
        Returns:
            dict[str, str]: A dictionary mapping serial numbers to their corresponding lookup_ids.
        """
        self.pf.login()
        return self.pf.fetch_lookup_ids(serial_nums)

    def fetch_plume_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the plume data from the api and returns a list of sensor summaries.
        If the sensor has location data outside the stationary box, it will be overwrite the box and the location data will be saved.
        Avoid bulk (multiple days) ingest if you know the sensors have no location data for some of the days. Instead try to fetch data for the mobile and stationary portion separately

        Args:
            start (dt.datetime): The start date of the data to fetch.
            end (dt.datetime): The end date of the data to fetch.
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        self.pf.login()
        for sensor in self.pf.get_sensors(sensor_dict, start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    def fetch_zephyr_platform_lookupids(self) -> list[str]:
        """Fetches a list of zephyr sensor lookup_ids

        Returns:
            list[str]: A list of zephyr sensor lookup_ids.
        """
        return self.zf.fetch_lookup_ids()

    def fetch_zephyr_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the zephyr data from the api and returns a list of sensor summaries.

        Args:
            start (dt.datetime): The start date of the data to fetch
            end (dt.datetime): The end date of the data to fetch
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        for sensor in self.zf.get_sensors(sensor_dict, start, end, "B"):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    def fetch_sensorCommunity_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the sensor community data from the api and returns a list of sensor summaries.

        Args:
            start (dt.datetime): The start date of the data to fetch
            end (dt.datetime): The end date of the data to fetch
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        for sensor in self.scf.get_sensors(sensor_dict, start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    def fetch_purpleAir_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the purple air data from the api and returns a list of sensor summaries.
        If the sensor location has changed then do separate calls for the initial and changed static location data.

        Args:
            start (dt.datetime): The start date of the data to fetch
            end (dt.datetime): The end date of the data to fetch
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        self.paf.login()
        for sensor in self.paf.get_sensors(sensor_dict.copy(), start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])


# if __name__ == "__main__":
#     sfw = SensorFactoryWrapper()
#     summaries = list(sfw.fetch_sensor_community_data(dt.datetime(2023, 3, 31), dt.datetime(2023, 4, 1), {"60641,SDS011,60642,BME280": None}))
#     for summary in summaries:
#         print(summary.geom)
