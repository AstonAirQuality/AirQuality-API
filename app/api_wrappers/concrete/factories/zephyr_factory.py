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
        averaging_id = 0
        for id_ in sensorids:
            res = requests.get(
                f"https://data.earthsense.co.uk/measurementdata/v1/{id_}/{start.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/{slot}/{averaging_id}",
                headers={"username": self.username, "userkey": self.password},
            )
            if res.ok:
                yield ZephyrSensor.from_json(id_, res.json()["data"]["Unaveraged"][f"slot{slot}"])

    @DeprecationWarning
    def get_sensor_data(self, sensorids: list[str], start: dt.datetime, end: dt.datetime, slot: str = "B") -> Iterator[ZephyrSensor]:
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
                print(f"https://data.earthsense.co.uk/dataForViewBySlots/{self.username}/{self.password}/{id_}/{start.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/{slot}/def/json/api")
                yield ZephyrSensor.from_json(id_, res.json()[f"slot{slot}"])


# from os import environ as env

# from dotenv import load_dotenv

# if __name__ == "__main__":
#     load_dotenv()
#     zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])

#     sensors = zf.get_sensors(["814"], dt.datetime(2023, 3, 30), dt.datetime(2023, 3, 31))

#     for sensor in sensors:
#         print(sensor.df.head())
#         break
