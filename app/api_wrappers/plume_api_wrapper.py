# data fetching dependacies
import datetime as dt
import io
import json
import pathlib
import time as t
import zipfile
from typing import Iterator, List

import requests

# class dependancies
from api_wrappers.base_wrapper import BaseWrapper
from api_wrappers.plume_sensor import PlumeSensor


class APITimeoutException(IOError):
    pass


class PlumeWrapper(BaseWrapper):
    """API wrapper for the Plume dashboard."""

    def __init__(self, email: str, password: str, API_KEY: str, org_number: int):
        self.org = str(org_number)
        self.__session = self.__login(email, password, API_KEY)

    def __login(self, email, password, apiKey) -> requests.Session:
        """Logs into the Plume API

        The API uses Google Firebase for auth, each subsequent request to the API after login must
        be made with the "Bearer" auth token for the API to respond.

        :param email: login email
        :param password: login password
        :return: Logged in session
        """
        session = requests.Session()
        res = requests.post(
            f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?" f"key={apiKey}",
            data={"email": email, "password": password, "returnSecureToken": True},
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

        return session

    ####################################################################################################################
    def request_json_sensors(self, timeout=30):
        return self.__session.get(
            f"https://api-preprod.plumelabs.com/2.0/user/organizations/{self.org}/sensors", timeout=timeout
        ).json()

    def check_last_sync(self, days: int = 4) -> Iterator[tuple]:
        """Returns a list of all sensors with sync status.
        Return is in the following structure (sensor_id, True or False or None) where True represents a synced sensor,
        False represents an un-synced sensor and None is when no last synced time is available.
        :param days: Number of days until the sensor is considered un-synced
        :return: generator of tuples
        """
        sensors = self.request_json_sensors()["sensors"]
        for sensor in sensors:
            last_sync, id_ = sensor["last_sync"], sensor["device_id"]
            if last_sync is None:
                yield id_, None
                continue
            yield id_, (dt.datetime.now() - dt.datetime.fromtimestamp(last_sync)).days < days

    def fetch_lookup_ids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches look ids from the dashboard
        return dict: {serial_num:lookup_id}
        """
        sensor_dict = dict.fromkeys(serial_nums, None)

        res = self.__session.get(
            "https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors".format(org=self.org)
        )
        _json = res.json()["sensors"]

        for sensor in _json:
            if sensor["device_id"] in sensor_dict.keys():
                sensor_dict[sensor["device_id"]] = sensor["id"]

        return sensor_dict

    ###################################################################################################################

    def get_sensors(self, sensors: List[str], start: dt.datetime, end: dt.datetime) -> Iterator[PlumeSensor]:
        """Fetches data from the Plume API for a given list of sensor lookup ids in the specified timeframe."""
        # TODO if assert fails then add error message to sensorDTO so that we can log it and add locations at a later date
        try:
            sensor_locations = list(self.get_sensor_location_data(sensors, start, end))
            assert sensor_locations != []
            for sensor in sensor_locations:
                sensor.add_measurements_json(self.get_sensor_measurement_data(sensor.id, start, end))
                yield sensor
        except (zipfile.BadZipFile, AssertionError):
            # if the zip file is corrupt, try get measurments only
            yield from self.get_sensors_m_only(sensors, start, end)

    def get_sensors_m_only(self, sensors: List[str], start: dt.datetime, end: dt.datetime) -> Iterator[PlumeSensor]:
        for sensor_id in sensors:
            yield PlumeSensor.from_json(sensor_id, self.get_sensor_measurement_data(sensor_id, start, end))

    ##measurement data - json export
    def get_sensor_measurement_data(self, sensorId: str, start: dt.datetime, end: dt.datetime) -> List:
        """Downloads the sensor data from the Plume API and loads to PlumeSensor objects.

        :param sensors: sensors to retrieve
        :param start: start time
        :param end: end time
        :return: Generator of PlumeSensor Objects for each sensor populated with data from the API
        """

        difference = end - start
        dataList = []
        offset = 0
        for i in range(difference.days + 1):
            if (i - 1) % 2 == 0:
                offset += 2000
            try:
                res = self.__session.get(
                    f"https://api-preprod.plumelabs.com/2.0/user/organizations/{self.org}/sensors/{sensorId}/measures?start_date={int(start.timestamp())}&end_date={int(end.timestamp())}&offset={offset}",
                    data={"start_date": start, "end_date": end, "offset": offset},
                )
                dataList.append(res.json()["measures"])
            except requests.exceptions.RequestException as e:
                # TODO - add logging
                continue

            # if response json is empty, continue to next timeframe
            except json.JSONDecodeError as e:
                continue

        return dataList

    ##Location data - csv export

    def get_sensor_location_data(
        self, sensors: List[str], start: dt.datetime, end: dt.datetime
    ) -> Iterator[PlumeSensor]:

        for sensor, buffer in self.extract_zip(self.get_zip_file_link(sensors, start, end)):
            yield PlumeSensor.from_csv(sensor, buffer)

    def get_zip_file_link(self, sensors: List[str], start: dt.datetime, end: dt.datetime, timeout=150) -> str:
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
            },
        ).json()["id"]
        for _ in range(timeout):
            # wait for Plume API to create zip
            link = self.__session.get(f"https://api-preprod.plumelabs.com/2.0/user/export-tasks/{task_id}").json()[
                "link"
            ]
            if link:
                break
            t.sleep(1)
        else:
            raise APITimeoutException("Plume API timed out when attempting to retrieve zip file link")
        return link

    def extract_zip(self, link):
        """Download and extract zip into memory using link URL.

        :param link: url to sensor data zip file
        :return:sensor id, sensor data in a string buffer
        """
        res = requests.get(link, stream=True)
        if not res.ok:
            raise IOError(f"Failed to download zip file from link: {link}")
        zip_ = zipfile.ZipFile(io.BytesIO(res.content))
        for name in zip_.namelist():

            # skip measurement data
            if "position" not in pathlib.PurePath(name).parts[3]:
                continue

            # split path and strip string to extract sensor id and data
            yield pathlib.PurePath(name).parts[2].lstrip("sensor_"), io.StringIO(zip_.read(name).decode())
