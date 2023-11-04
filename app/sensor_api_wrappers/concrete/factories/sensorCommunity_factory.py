# data fetching dependacies
import datetime as dt
from typing import Iterator

import requests
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import (
    SensorCommunitySensor,
)
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


class SensorCommunityFactory(SensorFactory):
    def __init__(self, username: str, password: str):
        """Initializes the SensorCommunity Factory.
        :param username: username address of the SensorCommunity account
        :param password: password of the SensorCommunity account
        """
        self.username = username
        self.password = password

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

    def get_columns_from_db(self) -> dict[str, str]:
        """
        Get all column names from the API and return them as a dict.
        :return: dict with all column names and their type
        """
        # get all column names from the API
        try:
            payload = {"db": "feinstaub", "q": 'SHOW FIELD KEYS FROM "autogen"."feinstaub" ', "epoch": "ms"}

            r = requests.get("https://api-rrd.madavi.de:3000/grafana/api/datasources/proxy/uid/hoUeJn4Gz/query", params=payload)

            # convert to json
            r = r.json()

            # create a dict with all column names and their type
            column_dict = {}
            for i in r["results"][0]["series"][0]["values"]:
                column_dict[i[0]] = i[1]

            return column_dict

        except Exception:
            return None

    def get_sensor_columns(self, column_dict: dict[str, str], sensors: dict[str, str]) -> list[str]:
        """
        Filter column names by sensor type and return them as a list.
        :param column_dict: dict with all column names and their type [column_name: column_type]
        :param sensors: dict with all sensors [node_id: sensor_type]
        :return: list with all sensor columns
        """
        # get all column names from the API
        try:
            # create a list with all sensor columns
            sensor_columns = []
            for col in column_dict.keys():
                for sensor_type in sensors.values():
                    if sensor_type.lower() in col:
                        sensor_columns.append(col)

            return sensor_columns

        except Exception:
            return None

    def prepare_sensor_platform_dict(self, sensor_dict: dict[str, str], startDate: dt.datetime) -> dict[str, str]:
        """Set the sensor platform for each sensor in the sensor dictionary.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :return: A dictionary of lookup_ids and sensor platforms [lookup_id] = {"sensor_platform": sensor_platform, "time_updated": time_updated}
        """
        sensorPlatforms = {}
        lookupids = list(sensor_dict.keys())
        for sensor_lookupid in lookupids:
            # split the sensor ids and sensor types into a dictionary for each sensor platform
            sensor_id_type_pairs = sensor_lookupid.split(",")
            sensorPlatform = {}
            for i in range(0, len(sensor_id_type_pairs), 2):
                sensorPlatform[sensor_id_type_pairs[i]] = sensor_id_type_pairs[i + 1]
            sensorPlatforms[sensor_lookupid] = sensorPlatform
            sensorPlatforms[sensor_lookupid]["startDate"] = startDate
        return sensorPlatforms

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[SensorCommunitySensor]:
        """Fetch csv from API and return built SensorCommunity sensor objects.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :param start: measurement start date
        :param end:  measurement end date
        :return: SensorCommunitySensor objects
        """

        sensorPlatforms = self.prepare_sensor_platform_dict(sensor_dict, start)

        # for each sensor platform combine all the dataframes into one
        for key in sensorPlatforms:
            startDate = sensorPlatforms[key].pop("startDate")
            startDate = startDate.isoformat("T") + "Z"
            endDate = end.isoformat("T") + "Z"
            node_ids = list(sensorPlatforms[key].keys())
            sensor_columns = str(self.get_sensor_columns(self.get_columns_from_db(), sensorPlatforms[key])).strip("[]").replace("'", "")
            sensor_columns += ", geohash"
            try:
                payload = {
                    "db": "feinstaub",
                    "q": f'SELECT {sensor_columns} FROM "autogen"."feinstaub" WHERE ("node" =~ /{"|".join(node_ids)}/) AND time >= \'{startDate}\' AND time <= \'{endDate}\'',
                    "epoch": "ms",
                }
                res = requests.get("https://api-rrd.madavi.de:3000/grafana/api/datasources/proxy/uid/hoUeJn4Gz/query", params=payload)
                yield SensorCommunitySensor.from_json(key, res.json())

            except Exception:
                yield SensorCommunitySensor(key, None)

    # @DeprecationWarning
    def get_sensors_from_csv(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[SensorCommunitySensor]:
        """Fetch csv from API and return built SensorCommunity sensor objects.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :param start: measurement start date
        :param end:  measurement end date
        :return: SensorCommunitySensor objects
        """
        sensorPlatforms = self.prepare_sensor_platform_dict(sensor_dict, start)

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


# import json
# if __name__ == "__main__":
#     scf = SensorCommunityFactory("username", "password")
#     start = dt.datetime(2023, 10, 30)
#     end = dt.datetime(2023, 10, 31)
# # sensor_dict = {"60641,SDS011,60642,BME280": {"stationary_box": None, "time_updated": None}}
# # sensors = list(scf.get_sensors_from_csv(sensor_dict, start, end))
# # for sensor in sensors:
# #     print(sensor.id)
# #     print(sensor.df)
# sensor_dict = {"83636,SDS011,83637,DHT22": {"stationary_box": None, "time_updated": None}}
# sensors = list(scf.get_sensors(sensor_dict, start, end))
# for sensor in sensors:
#     print(sensor.id)
#     print(sensor.df)
