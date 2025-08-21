# data fetching dependacies
import datetime as dt
import io
import json
import pathlib
import time as t
import zipfile
from io import StringIO
from typing import Iterator, List, Tuple

import requests
from core.exception_utils import APITimeoutException
from sensor_api_wrappers.concrete.products.purpleAir_sensor import PurpleAirSensor
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


class PurpleAirFactory(SensorFactory):
    """Factory class for creating PurpleAir sensors.
    Extends the SensorFactory class.

    Link to docs:
        https://api.purpleair.com/
        https://community.purpleair.com/t/api-fields-descriptions/4652
    """

    def __init__(self, token_url: str, referer_url: str, api_key: str):
        """Initialize the factory with a url to fetch the API token."""
        self.token_url = token_url
        self.referer_url = referer_url
        self.api_key = api_key
        self.retry_count = 0

    def login(self) -> str:
        """Fetch the API token from the provided URL.
        :return: The API key as a string."""
        if self.token_url is None:
            raise ValueError("Token URL must be provided to login.")

        response = requests.get(self.token_url, headers={"referer": self.referer_url}, timeout=30)  # wait up to 30 seconds for the API to respond
        response.raise_for_status()  # raise an error if the request failed
        if response.status_code != 200:
            if self.api_key is None:
                raise ValueError("API key must be provided if the authentication fails")
            else:
                return self.api_key  # return the api key from the environment variable if the request fails
        else:
            self.api_key = response.text.strip()
            return self.api_key

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[PurpleAirSensor]:
        """Factory method for creating PurpleAir sensor objects by fetching data from the PurpleAir API.

        Args:
            sensor_dict (dict[str, str]): A dictionary where keys are sensor lookup IDs and values are stationary boxes.
            start (dt.datetime): The start date for fetching sensor data.
            end (dt.datetime): The end date for fetching sensor data.

        Yields:
            PlumeSensor: An instance of PlumeSensor for each sensor in the sensor_dict.
        """
        lookupids = list(sensor_dict.keys())
        startDate = None  # default start date

        for sensor_lookupid in lookupids:
            # if the sensor has a time_updated field then use that as the start date
            if "time_updated" in sensor_dict[sensor_lookupid] and sensor_dict[sensor_lookupid]["time_updated"] is not None:
                startDate = sensor_dict[sensor_lookupid]["time_updated"]
            else:
                startDate = start

            # then try to fetch the data for the given time period
            try:
                # convert start and end date to valid format YYYY-MM-DDTHH:MM:SS.sss+00:000,
                # Format with milliseconds and timezone offset as required: YYYY-MM-DDTHH:MM:SS.sss+00:00
                start_date_str = startDate.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"
                end_date_str = end.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"

                sensor_id = sensor_lookupid.split(",")[0]  # split by comma to get the sensor id
                outside = False
                if sensor_lookupid.split(",")[1] == "outdoor":
                    # if the sensor is outside then set the outside flag to True
                    outside = True

                field_list = [
                    # ["pm1.0_a", "pm1.0_b", "pm2.5_a", "pm2.5_b", "pm10.0_a", "pm10.0_b"], # these fields are not available in the API only for sensor summaries on the map
                    ["pm1.0_atm_a", "pm1.0_atm_b", "pm2.5_atm_a", "pm2.5_atm_b", "pm10.0_atm_a", "pm10.0_atm_b"],
                    ["pm1.0_cf_1_a", "pm1.0_cf_1_b", "pm2.5_cf_1_a", "pm2.5_cf_1_b", "pm10.0_cf_1_a", "pm10.0_cf_1_b"],
                    ["temperature", "humidity", "pressure", "voc", "scattering_coefficient", "deciviews", "visual_range"],
                ]

                # Flatten the list of lists into a single list of fields and filter based on the sensor type
                # if outside then remove all cf_1 fields
                if outside:
                    fields = [item for sublist in field_list for item in sublist if "cf_1" not in item]
                else:
                    # if inside then remove all atm fields
                    fields = [item for sublist in field_list for item in sublist if "atm" not in item]

                # convert the fields list to a string
                fields_str = ",".join(fields)

                url = "https://map.purpleair.com/v1/sensors/{sensor_id}/history/csv?fields={fields}&start_timestamp={start_date}&end_timestamp={end_date}&average={averaging_id}".format(
                    sensor_id=sensor_id, fields=fields_str, start_date=start_date_str, end_date=end_date_str, averaging_id=0
                )

                headers = {
                    "accept": "text/plain",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "referer": self.referer_url,  # referer is required by the API
                    "x-api-token": self.api_key,  # Use the token retrieved earlier
                }
                res = requests.get(
                    url=url,
                    timeout=30,  # wait up to 30 seconds for the API to respond
                    headers=headers,
                )
                # wait for the API to respond
                if res.status_code != 200:
                    if res.json()["error"] == "DataInitializingError":
                        # if the API is still loading data then wait for 15 seconds and try again
                        self.retry_count += 1
                        if self.retry_count < 3:
                            t.sleep(10)
                            return self.get_sensors(sensor_dict, start, end)
                        else:
                            raise APITimeoutException(res.text)
                else:
                    # pop the sensor from the sensor_dict to avoid fetching it again
                    sensor_dict.pop(sensor_lookupid, None)
                    yield PurpleAirSensor.from_csv(sensor_lookupid, res.text)
            # if the sensor has no data for the given time period then return an empty sensor
            except Exception as e:
                # print(f"Error fetching data for sensor {sensor_lookupid}: {e}")
                yield PurpleAirSensor(sensor_lookupid, dataframe=None, error="failed to fetch data:")

    def get_sensors_from_file(self, sensor_dict: dict[str, str], file: bytes) -> Iterator[PurpleAirSensor]:
        """Factory method for creating PurpleAir sensor objects from a csv file.

        Args:
            sensor_dict (dict[str, str]): A dictionary where keys are sensor lookup IDs and values are stationary boxes.
            file (bytes): The file containing sensor data in CSV format.

        Yields:
            PurpleAirSensor: An instance of PurpleAirSensor for each sensor in the sensor_dict.
        """
        # read the file as a string
        file_str = io.StringIO(file.decode("utf-8"))
        # create a zip file object from the string
        for sensor_lookupid in sensor_dict.keys():
            try:
                yield PurpleAirSensor.from_csv(sensor_lookupid, file_str.getvalue())
            except Exception as e:
                # if the sensor has no data for the given time period then return an empty sensor
                yield PurpleAirSensor(sensor_lookupid, dataframe=None, error=str(e))


if __name__ == "__main__":
    from os import environ as env

    from dotenv import load_dotenv

    load_dotenv()

    pf = PurpleAirFactory(token_url=env["PURPLE_AIR_TOKEN_URL"], referer_url=env["PURPLE_AIR_REFERER_URL"], api_key=env["PURPLE_AIR_API_KEY"])
    pf.login()

    sensor_dict = {"132169,outdoor": {"stationary_box": None, "time_updated": None}}

    sensors = pf.get_sensors(sensor_dict, dt.datetime(2025, 8, 12), dt.datetime(2025, 8, 13))

    for sensor in sensors:
        print(sensor.df.head(-1))
        # write df to csv file
        sensor.df.to_csv(f"purple_air_sensor_{sensor.id}.csv")
        break
