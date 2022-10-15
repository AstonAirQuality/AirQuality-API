# TODO add zephyr and other sensors to api functions and wrappers
import datetime as dt
from os import environ as env
from typing import Iterator

from core.models import Sensors

# sensor summary
from core.schema import Sensor as SchemaSensor
from core.schema import SensorSummary as SchemaSensorSummary
from dotenv import load_dotenv

from api_wrappers.plume_api_wrapper import PlumeWrapper
from api_wrappers.Sensor_DTO import SensorDTO


class ScraperWrapper:
    def __init__(self):
        """initialise the api wrappers"""
        load_dotenv()
        self.pw = PlumeWrapper(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])

    def fetch_plume_platform_lookupids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches a list of plume sensor lookup_ids from a list of serial numbers
        return dict: {serial_num:lookup_id}
        """
        return self.pw.fetch_lookup_ids(serial_nums)

    def fetch_plume_data(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """fetches the plume data from the api and returns a list of sensor summaries.
        Should not be used for bulk (multiple days) ingest if you want to ignore empty location data for sensors

        param sensor_dict: [lookup_id:stationary_box]
        lookupid must be a string
        """

        for sensor in self.pw.get_sensors(sensor_dict, start, end):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id])

    # TODO add fetch measurement only then add stationary box to sensor
    # def fetch_plume_data_measurenments_only(self, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]):
    #     """param sensor_dict: [lookup_id:stationary_box]"""
    #     for sensor in self.pw.get_sensors_m_only(list(sensor_dict.keys()), start, end):
    #         if sensor is not None:
    #             yield from sensor.create_sensor_summaries(sensor_dict[sensor.id])

    # TODO add zephyr and other sensors to api functions and wrappers
