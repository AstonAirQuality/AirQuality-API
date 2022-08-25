# TODO check postgres sensors table for active sensors. Then only write to the currently active sensors
# TODO add zephyr and other sensors to api functions and wrappers

import datetime as dt
from os import environ as env
from typing import Iterator

from dotenv import load_dotenv

from api_wrappers.plume_api_wrapper import PlumeWrapper
from api_wrappers.Sensor_DTO import SensorDTO
from models import Sensors
from schema import Sensor as SchemaSensor


class Nomans:
    def __init__(self):
        load_dotenv()
        self.pw = PlumeWrapper(
            env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"]
        )

    # TODO add match case on python 3.10 to match sensor types
    def generate_plume_platform(self, serial_nums: list[str]) -> Iterator[SchemaSensor]:

        sensor_platforms = self.pw.fetch_lookup_ids(serial_nums)

        sensors = []

        for (key, value) in sensor_platforms.items():
            sensors.append(SchemaSensor(lookup_id=value, serial_number=key, type_id=1, active=False))

        for sensor in sensors:
            yield sensor
