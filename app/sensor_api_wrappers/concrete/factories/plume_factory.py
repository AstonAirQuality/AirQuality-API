# data fetching dependacies
import datetime as dt
import io
import json
import pathlib
import time as t
import zipfile
from typing import Iterator, List, Tuple

import requests
from core.exception_utils import APITimeoutException
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


class PlumeFactory(SensorFactory):
    """Concrete Factory class which creates Plume Sensor Products using the Plume dashboard & API."""

    def __init__(self, email: str, password: str, API_KEY: str, org_number: int):
        """Initializes the Plume Factory.
        :param email: email address of the Plume account
        :param password: password of the Plume account
        :param API_KEY: API key of the Plume account
        :param org_number: organization number of the Plume account
        """
        self.email = email
        self.password = password
        self.API_KEY = API_KEY
        self.org = str(org_number)
        self.__session = None

    def login(self) -> requests.Session:
        """Logs into the Plume API

        The API uses Google Firebase for auth, each subsequent request to the API after login must
        be made with the "Bearer" auth token for the API to respond.

        :param email: login email
        :param password: login password
        :return: Logged in session
        """
        if self.__session is None:
            session = requests.Session()
            res = requests.post(
                f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?" f"key={self.API_KEY}",
                data={"email": self.email, "password": self.password, "returnSecureToken": True},
                headers={"referer": "https://dashboard-flow.plumelabs.com/"},
            )
            if not res.ok:
                raise IOError("Login failed")

            json_ = json.loads(res.content)
            auth_token = json_["idToken"]
            auth_key = json_["localId"]
            json_ = json.loads(
                session.post(
                    "https://api-preprod.plumelabs.com/2.0/user/token",
                    data={"auth_type": "FIREBASE", "auth_key": auth_key, "auth_token": auth_token, "auth_secret": ""},
                ).content
            )
            bearer = json_["token"]
            # add bearer to session header
            session.headers["authorization"] = f"Bearer {bearer}"

            # update session in class instance
            self.__session = session
        return self.__session

    ####################################################################################################################
    # def check_last_sync(self, days: int = 4) -> Iterator[tuple]:
    #     """Returns a list of all sensors with sync status.
    #     Return is in the following structure (sensor_id, True or False or None) where True represents a synced sensor,
    #     False represents an un-synced sensor and None is when no last synced time is available.
    #     :param days: Number of days until the sensor is considered un-synced
    #     :return: generator of tuples
    #     """
    #     sensors = self.__session.get(
    #         f"https://api-preprod.plumelabs.com/2.0/user/organizations/{self.org}/sensors", timeout=30
    #     ).json()["sensors"]

    #     for sensor in sensors:
    #         last_sync, id_ = sensor["last_sync"], sensor["device_id"]
    #         if last_sync is None:
    #             yield id_, None
    #             continue
    #         yield id_, (dt.datetime.now() - dt.datetime.fromtimestamp(last_sync)).days < days

    def fetch_lookup_ids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches look ids from the dashboard
        :param serial_nums: list of serial numbers
        :return dict: {serial_num:lookup_id}
        """
        sensor_dict = dict.fromkeys(serial_nums, None)

        res = self.__session.get("https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors".format(org=self.org))
        _json = res.json()["sensors"]

        for sensor in _json:
            if sensor["device_id"] in sensor_dict.keys():
                sensor_dict[sensor["device_id"]] = sensor["id"]

        return sensor_dict

    ###################################################################################################################
    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> list[PlumeSensor]:
        """Fetches data from the Plume API for a given list of sensor lookup ids in the specified timeframe.
        :param sensor_dict: A dictionary of lookup_ids and stationary_boxes [lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
        :param start: start time of the data
        :param end: end time of the data
        :return: list of PlumeSensor objects"""
        plumeSensors = []
        lookupids = list(sensor_dict.keys())
        lookupids_without_location_data = []
        lookupids_with_location_data = []
        sensors_with_location_data = []

        # STEP 1: get location and measurement data for all sensors using the start and end time of last synced
        for sensor_lookupid in lookupids:
            # if the sensor has a time_updated value and it is not None then get the location data using the time_updated value
            if "time_updated" in sensor_dict[sensor_lookupid] and sensor_dict[sensor_lookupid]["time_updated"] is not None:
                try:
                    sensors = self.get_sensor_location_data(sensor_lookupid, sensor_dict[sensor_lookupid]["time_updated"], end, link=None)
                    if len(sensors) > 0:
                        sensor = sensors[0]
                        sensor.add_measurements_json(self.get_sensor_measurement_data(sensor_lookupid, sensor_dict[sensor_lookupid]["time_updated"], end))
                        plumeSensors.append(sensor)
                        lookupids_with_location_data.append(sensor.id)
                # create a null sensor to be logged as a failed fetch if any errors occur
                except Exception as e:
                    plumeSensors.append(PlumeSensor(sensor_lookupid, dataframe=None, error=str(e)))

            # STEP 2: for sensors without a time_updated value, get the location data using the start and end time parameters
            else:
                try:
                    sensors_with_location_data += self.get_sensor_location_data(sensor_lookupid, start, end, link=None)
                # create a null sensor to be logged as a failed fetch
                except Exception:
                    plumeSensors.append(PlumeSensor(sensor_lookupid, dataframe=None, error="Failed to fetch location data"))

        # STEP 3: for sensors whose location data is not empty, get the measurements using the start and end time parameters
        if sensors_with_location_data != []:
            # add measurements to the sensors with location data
            for sensor in sensors_with_location_data:
                try:
                    sensor.add_measurements_json(self.get_sensor_measurement_data(sensor.id, start, end))
                    plumeSensors.append(sensor)
                    lookupids_with_location_data.append(sensor.id)
                except Exception:
                    plumeSensors.append(PlumeSensor(sensor.id, dataframe=None, error="Failed to fetch measurements for sensor with location data"))
                    # remove sensor id from lookupids list (prevents a sensor that has location and stationay box data from being fetched twice)
                    lookupids.remove(sensor.id)

        # create a list of sensor ids that do not have location data
        lookupids_without_location_data = list(set(lookupids) - set(lookupids_with_location_data))

        # STEP 4: for sensors without location data check if they have a stationary box value, and if they do then get the measurements using the start and end time parameters
        for sensorid in lookupids_without_location_data:
            if sensor_dict[sensorid]["stationary_box"] is not None:
                try:
                    sensor = self.get_sensors_measurement_only([sensorid], start, end)[0]
                    # sensor = PlumeSensor.from_json(sensorid, self.get_sensor_measurement_data(sensorid, start, end))
                    plumeSensors.append(sensor)
                except Exception:
                    plumeSensors.append(PlumeSensor(sensorid, dataframe=None, error="Failed to fetch measurements for sensor without location data"))

        return plumeSensors

    def get_sensors_merged_from_zip(self, lookupids: list[str], start: dt.datetime, end: dt.datetime) -> list[PlumeSensor]:
        """Fetches data from the Plume API for a given sensor lookup id in the specified timeframe.
        :param lookupids: list of sensor lookup ids
        :param start: start time of the data
        :param end: end time of the data
        :return: list of PlumeSensor objects"""
        plumeSensors = []

        link = self.get_zip_file_link(lookupids, start, end, include_measurements=True)

        for sensorid, buffer in self.extract_zip_from_link(link, include_measurements=True):
            plumeSensors.append(PlumeSensor.from_zip(sensorid, buffer))
        return plumeSensors

    def get_sensors_measurement_only(self, lookupids: list[str], start: dt.datetime, end: dt.datetime) -> list[PlumeSensor]:
        sensors = []
        for sensor_id in lookupids:
            sensors.append(PlumeSensor.from_json(str(sensor_id), self.get_sensor_measurement_data(str(sensor_id), start, end)))
        return sensors

    ###############################################################################################

    ##measurement data - json export
    def get_sensor_measurement_data(self, sensorId: str, start: dt.datetime, end: dt.datetime) -> List:
        """Downloads the sensor data from the Plume API and converts to List of JSON measurements.
        :param sensorId: sensor lookup id
        :param start: start time of the data
        :param end: end time of the data
        :return: list of JSON measurement objects"""

        difference = end - start
        dataList = []
        offset = 0
        for i in range(difference.days + 1):
            # apply offset for every 2 days of data
            if (i - 1) % 2 == 0:
                # don't apply offset for first iteration
                if i > 1:
                    offset += 2000
                res = self.__session.get(
                    "https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors/{sensorId}/measures?start_date={start}&end_date={end}&offset={offset}".format(
                        org=self.org,
                        sensorId=sensorId,
                        start=int(start.timestamp()),
                        end=int(end.timestamp()),
                        offset=offset,
                    )
                )
                dataList.append(res.json()["measures"])

        if len(dataList) <= 0:
            raise Exception("No data found for sensor: " + sensorId)

        return dataList

    ##Location data - csv export
    def get_sensor_location_data(self, sensors: list[str], start: dt.datetime, end: dt.datetime, link: str) -> List[PlumeSensor]:
        """Downloads the sensor data from the Plume API and loads to PlumeSensor objects.
        :param sensors: list of sensor lookup ids
        :param start: start time of the data
        :param end: end time of the data
        :param link: link to the zip file
        :return: list of PlumeSensor objects"""

        plumeSensors = []

        # if link is not provided, get the link
        if link is None:
            link = self.get_zip_file_link(sensors, start, end, include_measurements=False)

        for sensorid, buffer in self.extract_zip_from_link(link, include_measurements=False):
            plumeSensors.append(PlumeSensor.from_csv(sensorid, buffer))
        return plumeSensors

    def get_zip_file_link(self, sensors: list[str], start: dt.datetime, end: dt.datetime, include_measurements: bool, timeout=150) -> str:
        """Gets the link to the zip file containing the sensor data from the Plume API.
        :param sensors: list of sensor lookup ids
        :param start: start time of the data
        :param end: end time of the data
        :param include_measurements: boolean to include measurements in the zip file
        :param timeout: timeout for the request"""
        task_id = self.__session.post(
            f"https://api-preprod.plumelabs.com/2.0/user/organizations/" f"{self.org}/sensors/export",
            json={
                "sensors": sensors,
                "end_date": int(end.timestamp()),
                "start_date": int(start.timestamp()),
                "gps": True,
                "kml": False,
                "id": self.org,
                "no2": False,
                "pm1": False,
                "pm10": False,
                "pm25": False,
                "voc": False,
                "merged": include_measurements,
            },
        ).json()["id"]
        for _ in range(timeout):
            # wait for Plume API to create zip
            link = self.__session.get(f"https://api-preprod.plumelabs.com/2.0/user/export-tasks/{task_id}").json()["link"]
            if link:
                break
            t.sleep(1)
        else:
            raise APITimeoutException("Plume API timed out when attempting to retrieve zip file link")
        return link

    def extract_zip_from_link(self, link: str, include_measurements: bool):
        """Download and extract zip into memory using link URL.
        :param link: url to sensor data zip file
        :param include_measurements: boolean to include measurements in the zip file
        :return: list of tuples containing sensor id and buffer"""

        res = requests.get(link, stream=True)
        if not res.ok:
            raise IOError(f"Failed to download zip file from link: {link}")
        zip_ = zipfile.ZipFile(io.BytesIO(res.content))
        return PlumeFactory.extract_zip_content(zip_, include_measurements)

    @staticmethod
    def extract_zip_content(zip_: zipfile.ZipFile, include_measurements: bool) -> Iterator[Tuple[str, io.StringIO]]:
        """Extract zip into memory.
        :param zip_: zip file
        :param include_measurements: boolean to include measurements in the zip file
        :return:sensor id, sensor data in a string buffer
        """
        for name in zip_.namelist():
            if include_measurements:
                # if include_measurements is true, then use the merged csv file
                if "merged" in pathlib.PurePath(name).parts[3]:
                    yield (pathlib.PurePath(name).parts[2].lstrip("sensor_"), io.StringIO(zip_.read(name).decode()))
                else:
                    continue

            else:
                # skip all csv files except for position csv
                if "position" in pathlib.PurePath(name).parts[3]:
                    yield (pathlib.PurePath(name).parts[2].lstrip("sensor_"), io.StringIO(zip_.read(name).decode()))
                else:
                    continue


# Testing as a standalone script
# if __name__ == "__main__":
#     zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

#     (id_, buffer) = next(zip_contents)
#     sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)
#     # print dataframe columns
#     print(sensor.df.loc["2023-09-23 09:06:00":"2023-09-23 09:26:00"])

# import json
# import zipfile

# import pandas as pd

# if __name__ == "__main__":
#     # get the test data
#     zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

#     (id_, buffer) = next(zip_contents)
#     sensor = PlumeSensor.from_csv(sensor_id=id_, csv_file=buffer)
#     # print(sensor.df.loc["2023-09-23 09:06:00":"2023-09-23 09:26:00"])

#     file = open("testing/test_data/plume_measurements.json", "r")
#     json_ = json.load(file)
#     file.close()

#     sensor.add_measurements_json(json_["measures"])
#     # print df between dates"2023-09-23 09:06:00", "2023-09-23 09:26:00"
#     # print(sensor.df.loc["2023-09-23 09:06:00":"2023-09-23 09:26:00"])

#     # print timestamp as whole number
#     pd.options.display.float_format = "{:0}".format
