# data fetching dependacies
import datetime as dt
import json
from typing import Iterator

import requests
from sensor_api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


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

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime, slot: str = "B") -> Iterator[ZephyrSensor]:
        """Fetch json from API and return built Zephyr sensor objects.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :param start: measurement start date
        :param end:  measurement end date
        :param slot: sensor slot (A or B)
        :return: ZephyrSensor objects
        """
        lookupids = list(sensor_dict.keys())
        startDate = start

        averaging_id = 0
        for sensor_lookupid in lookupids:
            # if the sensor has a time_updated field then use that as the start date
            if "time_updated" in sensor_dict[sensor_lookupid] and sensor_dict[sensor_lookupid]["time_updated"] is not None:
                startDate = sensor_dict[sensor_lookupid]["time_updated"]
            else:
                startDate = start

            # then try to fetch the data for the given time period
            try:
                res = requests.get(
                    f"https://data.earthsense.co.uk/measurementdata/v1/{sensor_lookupid}/{startDate.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/{slot}/{averaging_id}",
                    headers={"username": self.username, "userkey": self.password},
                )

                yield ZephyrSensor.from_json(sensor_lookupid, res.json()["data"]["Unaveraged"][f"slot{slot}"])
            # if the sensor has no data for the given time period then return an empty sensor
            except Exception as e:
                yield ZephyrSensor(sensor_lookupid, None)


# from os import environ as env

# from dotenv import load_dotenv

# if __name__ == "__main__":
#     load_dotenv()
#     zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])

#     sensors = zf.get_sensors(["814"], dt.datetime(2023, 3, 22), dt.datetime(2023, 3, 31))

#     for sensor in sensors:
#         print(sensor.df.head(-1))
#         break
