# data fetching dependacies
import datetime as dt
import json
from typing import Iterator

import requests
from api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from api_wrappers.interfaces.sensor_factory import SensorFactory


class ZephyrFactory(SensorFactory):
    def __init__(self, username: str, password: str):
        """Initializes the Zephyr Factory.
        :param username: username address of the Zephyr account
        :param password: password of the Zephyr account
        """
        self.username = username
        self.password = password

    def fetch_lookup_ids(self) -> Iterator[str]:
        """Fetches sensor ids from Earth sense API"""
        try:
            json_ = requests.get(f"https://data.earthsense.co.uk/zephyrsForUser/{self.username}/{self.password}").json()["usersZephyrs"]
        except json.JSONDecodeError:
            return []
        for key in json_:
            yield str(json_[key]["zNumber"])

    def get_sensors(self, sensorids: list[str], start: dt.datetime, end: dt.datetime, slot: str = "B") -> Iterator[ZephyrSensor]:
        """Fetch json from API and return built Zephyr sensor objects.
        :param sensorids: list of sensor ids
        :param start: measurement start date
        :param end:  measurement end date
        :param slot: sensor slot (A or B)
        :return: ZephyrSensor objects
        """
        for id_ in sensorids:
            res = requests.get(
                f"https://data.earthsense.co.uk/dataForViewBySlots/{self.username}/{self.password}/{id_}/{start.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/{slot}/def/json/api"
            )
            if res.ok:
                yield ZephyrSensor.from_json(id_, res.json()[f"slot{slot}"])
