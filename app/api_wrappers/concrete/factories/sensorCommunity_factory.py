# data fetching dependacies
import datetime as dt
import json
from typing import Iterator

import requests
from api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor
from api_wrappers.interfaces.sensor_factory import SensorFactory


class SensorCommunityFactory(SensorFactory):
    def __init__(self, username: str, password: str):
        """Initializes the SensorCommunity Factory.
        :param username: username address of the SensorCommunity account
        :param password: password of the SensorCommunity account
        """
        self.username = username
        self.password = password

    # def fetch_lookup_ids(self) -> Iterator[str]:
    #     """Fetches sensor ids from Earth sense API"""
    #     pass

    # def login(self) -> requests.Session:
    #     """Logs into the SensorCommunity API and returns a session object"""
    #     pass

    def ExtractDataFromCsv(self, start: dt.datetime, end: dt.datetime, sensor_platform: dict[str, str]) -> dict[str, any]:
        """Extract data from sensorCommunity archives from a start-end daterange for each sensors in sensor_platforms

        :param start: the start date for extracting date
        :param end: the end date for extracting data (Can not be today's date)
        :param sensor_platform: a dicitonary of sensor id and sensor types (key-value)
        :return: dictionary of sensor measurements
        """

        difference = end - start

        measurement_dictionary = {}

        for id_ in sensor_platform:
            measurements = {}
            sensortype = sensor_platform[id_].lower()

            for i in range(difference.days + 1):
                day = start + dt.timedelta(days=i)
                timestamp = int(day.replace(tzinfo=dt.timezone.utc).timestamp())
                day = day.strftime("%Y-%m-%d")

                try:
                    url = f"https://archive.sensor.community/{day}/{day}_{sensortype}_sensor_{id_}.csv"
                    res = requests.get(url, stream=True)

                    if res.ok:
                        measurements[timestamp] = res.content

                    else:
                        url = f"https://archive.sensor.community/{day}/_{sensortype}_sensor_{id_}_indoor.csv"
                        res = requests.get(url, stream=True)

                        if res.ok:
                            measurements[timestamp] = res.content

                        else:
                            print(f"🛑: No sensor data available for sensor {id_}, ({sensortype}) on the day: {day} ")
                            continue

                except requests.exceptions.ConnectionError:
                    raise (ConnectionError)

            measurement_dictionary[int(id_)] = measurements

        return measurement_dictionary

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[SensorCommunitySensor]:
        """Fetch csv from API and return built SensorCommunity sensor objects.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :param start: measurement start date
        :param end:  measurement end date
        :return: SensorCommunitySensor objects
        """

        sensorPlatforms = {}
        lookupids = list(sensor_dict.keys())
        startDate = start

        for sensor_lookupid in lookupids:
            # if the sensor has a time_updated field then use that as the start date
            if "time_updated" in sensor_dict[sensor_lookupid] and sensor_dict[sensor_lookupid]["time_updated"] is not None:
                startDate = sensor_dict[sensor_lookupid]["time_updated"]
            else:
                startDate = start

            # split the sensor ids and sensor types into a dictionary for each sensor platform
            sensor_id_type_pairs = sensor_lookupid.split(",")
            sensorPlatform = {}
            for i in range(0, len(sensor_id_type_pairs), 2):
                sensorPlatform[sensor_id_type_pairs[i]] = sensor_id_type_pairs[i + 1]
            sensorPlatforms[sensor_lookupid] = sensorPlatform
            sensorPlatforms[sensor_lookupid]["startDate"] = startDate

        # for each sensor platform combine all the dataframes into one
        for key in sensorPlatforms:
            try:
                # pop the start date from the dictionary
                startDate = sensorPlatforms[key].pop("startDate")
                sensorPlatforms[key] = self.ExtractDataFromCsv(startDate, end, sensorPlatforms[key])
                yield SensorCommunitySensor.from_csv(key, sensorPlatforms[key])
            # if the sensor has no data for the given time period then return an empty sensor
            except Exception as e:
                yield SensorCommunitySensor(key, None)


# if __name__ == "__main__":
#     scf = SensorCommunityFactory("username", "password")
#     sensorids = ["60641,SDS011,60642,BME280"]
#     start = dt.datetime(2023, 4, 1)
#     end = dt.datetime(2023, 4, 3)
#     sensors = list(scf.get_sensors(sensorids, start, end))
#     for sensor in sensors:
#         print(sensor.id)
#         print(sensor.df)
