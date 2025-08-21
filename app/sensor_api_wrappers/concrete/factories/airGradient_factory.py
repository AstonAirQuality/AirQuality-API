# data fetching dependacies
import datetime as dt
import json
from typing import Iterator

import requests
from sensor_api_wrappers.concrete.products.airGradient_sensor import AirGradientSensor
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory

# lookup_id = 163763
# sensor_id = 2020:airgradient


class AirGradientFactory(SensorFactory):
    """Factory for AirGradient sensors, fetching data from the AirGradient API.
    docs page: https://api.airgradient.com/public/docs/api/v1/
    """

    def __init__(self, api_key: str):
        """Initializes the AirGradient Factory.
        Args:
            api_key (str): API key for AirGradient.
        """
        self.api_key = api_key

    def login(self) -> str:
        """Returns the API key for AirGradient.
        :return: The API key as a string."""
        if not self.api_key:
            raise ValueError("API key must be provided to login.")
        return self.api_key

    def get_sensors_two_day_limit(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[AirGradientSensor]:
        """Fetches data from the AirGradient API with a two-day limit and returns built AirGradient sensor objects.
        Args:
            sensor_dict (dict[str, str]): A dictionary of sensor ids.
            start (dt.datetime): Measurement start date.
            end (dt.datetime): Measurement end date.

        Yields:
            AirGradientSensor: AirGradientSensor objects with the fetched data.
        """
        # convert start and end to strings in the format YYYYMMDDTHHMMSSZ
        start_str = start.strftime("%Y%m%dT%H%M%SZ")
        end_str = end.strftime("%Y%m%dT%H%M%SZ")

        for sensor_id in sensor_dict.keys():
            try:
                response = requests.get(
                    f"https://api.airgradient.com/public/api/v1/locations/{sensor_id}/measures/raw?token={self.api_key}&from={start_str}&to={end_str}",
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                yield AirGradientSensor.from_json(sensor_id, data)
            except requests.RequestException:
                yield AirGradientSensor(sensor_id, dataframe=None, error=f"failed to fetch data")

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[AirGradientSensor]:
        """Fetches data from the AirGradient API and returns built AirGradient sensor objects.
        Args:
            sensor_dict (dict[str, str]): A dictionary of sensor ids.
            start (dt.datetime): Measurement start date.
            end (dt.datetime): Measurement end date.

        Yields:
            AirGradientSensor: AirGradientSensor objects with the fetched data.
        """

        num_days = (end - start).days
        if num_days > 10:
            # raise ValueError("The time period for AirGradient data fetching cannot exceed 10 days.")
            for sensor_id in sensor_dict.keys():
                yield AirGradientSensor(sensor_id, dataframe=None, error="The time period for AirGradient data fetching cannot exceed 10 days.")
        elif num_days <= 2:
            # do as normal
            yield from self.get_sensors_two_day_limit(sensor_dict, start, end)
        else:
            # fetch data in chunks of 2 days
            current_start = start
            while current_start < end:
                current_end = min(current_start + dt.timedelta(days=2), end)
                yield from self.get_sensors_two_day_limit(sensor_dict, current_start, current_end)
                current_start = current_end

    def get_sensors_from_file(self, sensor_dict: dict[str, str], file: bytes) -> Iterator[AirGradientSensor]:
        """Fetches data from local files and returns built AirGradient sensor objects.
        Args:
            sensor_dict (dict[str, str]): A dictionary of sensor ids.
            file (bytes): The csv file containing sensor data.

        Yields:
            AirGradientSensor: AirGradientSensor objects with the fetched data.
        """
        for sensor_id in sensor_dict.keys():
            try:
                yield AirGradientSensor.from_csv(sensor_id, file.decode("utf-8"))
            except Exception as e:
                yield AirGradientSensor(sensor_id, dataframe=None, error=str(e))


# if __name__ == "__main__":
#     import os

#     from dotenv import load_dotenv

#     load_dotenv()

#     api_key = os.getenv("AIR_GRADIENT_API_KEY")
#     agf = AirGradientFactory(api_key)
#     sensor_dict = {"163763": {"stationary_box": None, "time_updated": None}}
#     start = dt.datetime(2025, 7, 15)
#     end = dt.datetime(2025, 7, 16)
#     sensors = agf.get_sensors(sensor_dict, start, end)
#     for sensor in sensors:
#         print(sensor.id, sensor.df)
#         print(sensor.id, sensor.df)
