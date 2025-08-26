# TODO generic factory for sensor API wrappers
# functions
# login -> api_key
# get_sensors -> sensor objects
# get_sensors_from_file -> sensor objects


# TODO:
# save params in a new table
# url params for login + response body for login
# url params for get_sensors
# sensor mapping definitions.
# processing steps: transformations, aggregations, etc.

# data fetching dependacies
import datetime as dt
import json
from typing import Iterator

import requests
from sensor_api_wrappers.concrete.products.generic_sensor import GenericSensor
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


class GenericFactory(SensorFactory):
    """Factory for Generic sensors, fetching data from a generic API.
    This factory is designed to be flexible and can be used with various APIs
    that return sensor data in JSON or CSV format.
    """

    def __init__(self, auth_url: str, auth_method: dict, api_url: str, api_method: dict, api_key: str):
        """Initializes the Generic Factory.
        Args:
            api_url (str): Base URL for the API.
            api_key (str): Optional API key for authentication.
        """
        self.auth_url = auth_url
        self.auth_method = auth_method
        self.api_url = api_url
        self.api_method = api_method
        self.api_key = api_key
        # self.auth_url = auth_url
        # self.auth_url_params = kwargs.get("auth_url_params", {})
        # self.api_url_params = kwargs.get("api_url_params", {})
        self.__session = requests.Session()  # to be used for all requests to maintain session state

    def login(self) -> str:
        """Logs into the API and retrieves an authentication token or session if no api_key is provided"""
        if self.api_key:
            return self.api_key
        try:
            # add url parameters for authentication if needed
            if auth_params := self.auth_method.get("url_params"):
                self.auth_url += "?" + "&".join(f"{k}={v}" for k, v in auth_params.items())
            response = self.__session.post(
                self.auth_url,
                json=self.auth_method.get("body", {}),  # e.g., {"username": "user", "password": "pass"}
                headers=self.auth_method.get("headers", {}),  # e.g., {"Authorization": f"Bearer {self.api_key}"}
                data=self.auth_method.get("data", {}),  # e.g., {"grant_type": "client_credentials"}
            )
            response.raise_for_status()

            # depending on the API response format, return the token
            if response.headers.get("Content-Type") == "application/json":
                token_key = self.auth_method.get("token_key", "token")  # default to "token" if not specified
                return response.json().get(token_key, "")
            elif response.headers.get("Content-Type") == "text/plain":
                return response.text.strip()
            else:
                raise ValueError("Unexpected response format from authentication endpoint.")

        except requests.RequestException as e:
            raise Exception(f"Login failed: {e}")

    def get_sensors(self, sensor_dict: dict[str, str], start: dt.datetime, end: dt.datetime) -> Iterator[GenericSensor]:
        """Fetches data from the Generic API and returns built Generic sensor objects.
        Args:
            sensor_dict (dict[str, str]): A dictionary of sensor ids.
            start (dt.datetime): Measurement start date.
            end (dt.datetime): Measurement end date.

        Yields:
            GenericSensor: GenericSensor objects with the fetched data.
        """
        lookupids = list(sensor_dict.keys())
        startDate = None  # default start date
        for sensor_lookupid in lookupids:
            # if the sensor has a time_updated field then use that as the start date
            if "time_updated" in sensor_dict[sensor_lookupid] and sensor_dict[sensor_lookupid]["time_updated"] is not None:
                startDate = sensor_dict[sensor_lookupid]["time_updated"]
            else:
                startDate = start
            try:
                url_params = self.api_method.get("url_params", None)
                if url_params is None:
                    raise ValueError("API method does not contain URL parameters.")
                datetime_params = url_params.get("datetime_params", None)
                if datetime_params is None:
                    raise ValueError("API method does not contain datetime parameters.")
                url_params.pop("datetime_params", None)

                # convert start and end dates to valid format
                # e.g.  YYYY-MM-DDTHH:MM:SS.sss+00:00 or  YYYY-MM-DDTHH:MM:SSZ
                datetime_formatting = datetime_params.get("format", "%Y-%m-%dT%H:%M:%S.%f+00:00")
                # if the format is timestamp, then use the timestamp directly
                start_date_str = startDate.strftime(datetime_formatting) if datetime_params.get("format") != "timestamp" else startDate.timestamp()
                end_date_str = end.strftime(datetime_formatting) if datetime_params.get("format") != "timestamp" else end.timestamp()
                # start_time_param and end_time_param
                start_time_param = {datetime_params.get("start_key", "start"): start_date_str}
                end_time_param = {datetime_params.get("end_key", "end"): end_date_str}

                # Need a new URL for each sensor
                request_url = self.api_url
                try:
                    # if the sensor id is in the URL, then replace the placeholder with the sensor id
                    request_url = request_url.format(sensor_id=sensor_lookupid)
                except KeyError:
                    # if the sensor id is not in the URL, then add it as a parameter
                    sensor_id_param = {url_params.get("sensor_id_key", "sensor_id"): sensor_lookupid}
                    request_url += "&" + "&".join(f"{k}={v}" for k, v in sensor_id_param.items())

                # add the start and end time parameters to the URL
                request_url += "?" + "&".join(f"{k}={v}" for k, v in start_time_param.items())
                request_url += "&" + "&".join(f"{k}={v}" for k, v in end_time_param.items())
                # construct the URL for fetching sensor data
                if api_params := url_params:
                    # e.g. {"fields": "pm25,pm10", "averaging": 0, ""}
                    request_url += "&" + "&".join(f"{k}={v}" for k, v in api_params.items())

                # headers for the request
                # make url token or header authentication
                if self.api_method.get("auth_type") == "url_token":
                    request_url += f"&{self.api_method.get('token_key', 'token')}={self.api_key}"
                elif self.api_method.get("auth_type") == "header_auth":
                    self.__session.headers.update({"Authorization": f"Bearer {self.api_key}"})
                elif self.api_method.get("auth_type") == "header_token":
                    self.__session.headers.update({self.api_method.get("token_key", "x-api-token"): self.api_key})
                    # print headers
                    print(f"Request headers: {self.__session.headers}")
                else:
                    # if no auth type is specified, assume it's a session-based authentication
                    pass
                # update any additional headers
                if additional_headers := self.api_method.get("headers", None):
                    self.__session.headers.update(additional_headers)
                    print(f"Request headers: {self.__session.headers}")

                # make the API request to fetch sensor data
                response = self.__session.get(url=request_url, headers=self.__session.headers, timeout=30)  # wait up to 30 seconds for the API to respond

                response.raise_for_status()  # raise an error if the request failed
                if "application/json" in response.headers.get("Content-Type", ""):
                    yield GenericSensor.from_json(sensor_lookupid, response.json(), sensor_dict[sensor_lookupid]["sensor_mappings"])
                elif "text/csv" in response.headers.get("Content-Type", "") or "text/plain" in response.headers.get("Content-Type", ""):
                    # if the response is in CSV format, parse it accordingly
                    yield GenericSensor.from_csv(sensor_lookupid, response.text, sensor_dict[sensor_lookupid]["sensor_mappings"])
                else:
                    # by default, assume the response is in JSON format
                    yield GenericSensor.from_json(sensor_lookupid, response.json(), sensor_dict[sensor_lookupid]["sensor_mappings"])

            except Exception as e:
                print(e)  # Debugging: print the error
                yield GenericSensor(sensor_lookupid, dataframe=None, error=f"Failed to fetch data for sensor {sensor_lookupid}: {e}")


# if __name__ == "__main__":
#     # test datetime formatting conversion
#     timestamp = dt.datetime.now()
#     formatted_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
#     print(f"Formatted timestamp: {formatted_timestamp}")

#     formatted_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
#     print(f"Formatted timestamp with seconds: {formatted_timestamp}")

#     # zulu format
#     formatted_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
#     print(f"Formatted timestamp in Zulu format: {formatted_timestamp}")
