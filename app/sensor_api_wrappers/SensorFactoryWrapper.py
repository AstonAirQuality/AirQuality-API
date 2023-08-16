import datetime as dt
from os import environ as env
from typing import Iterator

# sensor summary
from core.schema import Sensor as SchemaSensor
from core.schema import SensorSummary as SchemaSensorSummary
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.factories.sensorCommunity_factory import (
    SensorCommunityFactory,
)
from sensor_api_wrappers.concrete.factories.zephyr_factory import ZephyrFactory


class SensorFactoryWrapper:
    """Wrapper class for all the different sensor factories, which fetch sensor data from the different apis"""

    def __init__(self):
        """initialise the api wrappers and load the environment variables"""
        load_dotenv()
        self.zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])
        self.scf = SensorCommunityFactory(env["SC_USERNAME"], env["SC_PASSWORD"])
        self.pf = PlumeFactory(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])

    def fetch_plume_platform_lookupids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches a list of plume sensor lookup_ids from a list of serial numbers
        :param serial_nums: A list of plume sensor serial numbers
        :return dict: {str(serial_num):str(lookup_id)}
        """
        self.pf.login()
        return self.pf.fetch_lookup_ids(serial_nums)

    def fetch_plume_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the plume data from the api and returns a list of sensor summaries.
        Should not be used for bulk (multiple days) ingest if you want to ignore empty location data for sensors
        :param start: The start date of the data to fetch
        :param end: The end date of the data to fetch
        :param sensor_dict: A dictionary of lookup_ids, stationary_boxes and time updated [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :return: A list of sensor summaries
        """
        self.pf.login()
        for sensor in self.pf.get_sensors(sensor_dict, start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    # TODO add fetch measurement only then add stationary box to sensor
    # def fetch_plume_data_measurenments_only(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]):
    #     """param sensor_dict: [lookup_id:stationary_box]"""
    #     for sensor in self.pf.get_sensors_m_only(list(sensor_dict.keys()), start, end):
    #         if sensor is not None:
    #             yield from sensor.create_sensor_summaries(sensor_dict[sensor.id])

    def fetch_zephyr_platform_lookupids(self) -> list[str]:
        """Fetches a list of zephyr sensor lookup_ids
        return list: [str(lookup_id)]
        """
        return self.zf.fetch_lookup_ids()

    def fetch_zephyr_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the zephyr data from the api and returns a list of sensor summaries.
        :param start: The start date of the data to fetch
        :param end: The end date of the data to fetch
        :param sensor_dict: A dictionary of lookup_ids, stationary_boxes and time updated [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :return: A list of sensor summaries
        """
        for sensor in self.zf.get_sensors(sensor_dict, start, end, "B"):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    def fetch_sensorCommunity_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the sensor community data from the api and returns a list of sensor summaries.
        :param start: The start date of the data to fetch
        :param end: The end date of the data to fetch
        :param sensor_dict: A dictionary of lookup_ids, stationary_boxes and time updated [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :return: A list of sensor summaries
        """
        for sensor in self.scf.get_sensors(sensor_dict, start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])


# if __name__ == "__main__":
#     sfw = SensorFactoryWrapper()
#     summaries = list(sfw.fetch_sensor_community_data(dt.datetime(2023, 3, 31), dt.datetime(2023, 4, 1), {"60641,SDS011,60642,BME280": None}))
#     for summary in summaries:
#         print(summary.geom)
