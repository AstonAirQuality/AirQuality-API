import datetime as dt
from os import environ as env
from typing import Iterator

# sensor summary
from core.schema import SensorPlatform as SchemaSensor
from core.schema import SensorSummary as SchemaSensorSummary
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.airGradient_factory import AirGradientFactory
from sensor_api_wrappers.concrete.factories.generic_factory import GenericFactory
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.factories.purpleAir_factory import PurpleAirFactory
from sensor_api_wrappers.concrete.factories.sensorCommunity_factory import SensorCommunityFactory
from sensor_api_wrappers.concrete.factories.zephyr_factory import ZephyrFactory
from sensor_api_wrappers.interfaces.sensor_factory import SensorFactory


class SensorPlatformFactoryWrapper:
    """Wrapper class for all the different sensor platform factories, which fetch sensor data from the different apis"""

    def __init__(self):
        """initialise the api wrappers and load the environment variables"""
        load_dotenv()
        self.zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])
        self.scf = SensorCommunityFactory(env["SC_USERNAME"], env["SC_PASSWORD"])
        self.pf = PlumeFactory(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])
        self.paf = PurpleAirFactory(env["PURPLE_AIR_TOKEN_URL"], env["PURPLE_AIR_REFERER_URL"], env["PURPLE_AIR_API_KEY"])
        self.agf = AirGradientFactory(env["AIR_GRADIENT_API_KEY"])

    def fetch_plume_platform_lookupids(self, serial_nums: list[str]) -> dict[str, str]:
        """Fetches a list of plume sensor lookup_ids from a list of serial numbers

        Args:
            serial_nums (list[str]): A list of serial numbers to fetch lookup_ids for.
        Returns:
            dict[str, str]: A dictionary mapping serial numbers to their corresponding lookup_ids.
        """
        self.pf.login()
        return self.pf.fetch_lookup_ids(serial_nums)

    def fetch_zephyr_platform_lookupids(self) -> list[str]:
        """Fetches a list of zephyr sensor lookup_ids

        Returns:
            list[str]: A list of zephyr sensor lookup_ids.
        """
        return self.zf.fetch_lookup_ids()

    def fetch_data(self, sensor_factory: SensorFactory, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str], *args) -> Iterator[SchemaSensorSummary]:
        """Fetches data from the specified sensor factory and returns sensor summaries.

        Args:
            sensor_factory (SensorFactory): The sensor factory to fetch data from.
            start (dt.datetime): The start date of the data to fetch.
            end (dt.datetime): The end date of the data to fetch.
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
            *args: Additional arguments to pass to the sensor factory's get_sensors method (for example, slot for zephyr sensors).
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        # we use a copy because for some sensor platforms (purple air) we edit the dictionary on retry (pop off completed sensor tasks)
        for sensor in sensor_factory.get_sensors(start=start, end=end, sensor_dict=sensor_dict.copy(), *args):
            if sensor is not None:
                yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])

    def fetch_sensor_data(self, sensor_type: str, start: dt.datetime, end: dt.datetime, sensor_dict: dict[str, str]) -> Iterator[SchemaSensorSummary]:
        """Fetches sensor data based on the sensor type and returns sensor summaries.

        Args:
            sensor_type (str): The type of the sensor.
            start (dt.datetime): The start date of the data to fetch.
            end (dt.datetime): The end date of the data to fetch.
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        if "plume" in sensor_type.lower():
            self.pf.login()
            yield from self.fetch_data(self.pf, start, end, sensor_dict)
        elif "zephyr" in sensor_type.lower():
            yield from self.fetch_data(self.zf, start, end, sensor_dict, "B")
        elif "sensorcommunity" in sensor_type.lower():
            yield from self.fetch_data(self.scf, start, end, sensor_dict)
        elif "purpleair" in sensor_type.lower():
            self.paf.login()
            # we use a copy because we edit the dictionary on retry (pop off completed sensor tasks)
            yield from self.fetch_data(self.paf, start, end, sensor_dict)
        elif "airgradient" in sensor_type.lower():
            yield from self.fetch_data(self.agf, start, end, sensor_dict)
        elif "generic" in sensor_type.lower():
            # We need to group the generic sensors by sensor platform type, because if they are the same type, they can share the same factory instance
            sensor_dicts = {}
            for sensor_id, sensor_info in sensor_dict.items():
                api_url = sensor_info["api_url"]
                if api_url not in sensor_dicts:
                    sensor_dicts[api_url] = {}
                sensor_dicts[api_url][sensor_id] = {
                    "stationary_box": sensor_info["stationary_box"],
                    "authentication_url": sensor_info["authentication_url"],
                    "api_url": api_url,
                    "authentication_method": sensor_info["authentication_method"],
                    "api_method": sensor_info["api_method"],
                    "sensor_mappings": sensor_info["sensor_mappings"],
                }

            for api_url in sensor_dicts:
                sensor_dictionary = sensor_dicts[api_url]
                shared_sensor_config = sensor_dictionary[next(iter(sensor_dictionary))]  # get the first sensor's config
                generic_sensor_factory = GenericFactory(
                    auth_url=shared_sensor_config["authentication_url"],
                    auth_method=shared_sensor_config["authentication_method"],
                    api_url=shared_sensor_config["api_url"],
                    api_method=shared_sensor_config["api_method"],
                    api_key=shared_sensor_config["api_method"].get("api_key_value", None),
                )
                yield from self.fetch_data(generic_sensor_factory, start, end, sensor_dictionary)
        else:
            raise ValueError(f"Unsupported sensor type: {sensor_type}")

    def upload_user_input_sensor_data(self, sensor_type: str, sensor_dict: dict[str, str], file: bytes) -> Iterator[SchemaSensorSummary]:
        """Uploads user input sensor data from a file and returns sensor summaries.

        Args:
            sensor_type (str): The type of the sensor.
            sensor_dict (dict[str, str]): A dictionary of the data ingestion information for each sensor, where keys are sensor lookup_ids and values are stationary boxes.
            file (bytes): The file containing sensor data.
        Returns:
            Iterator[SchemaSensorSummary]: An iterator yielding sensor summaries.
        """
        if "plume" in sensor_type.lower():
            raise Exception("Plume sensor data will not be implemented until plumelabs fix their csv data export issue")
        elif "zephyr" in sensor_type.lower():
            raise Exception("Unbucketed zephyr data upload is not supported. Please use the Zephyr API to fetch data.")
        elif "sensorcommunity" in sensor_type.lower():
            raise Exception("SensorCommunity data upload is not supported because there is no bulk export feature in the SensorCommunity API for users")
        elif "purpleair" in sensor_type.lower():
            for sensor in self.paf.get_sensors_from_file(sensor_dict, file):
                if sensor is not None:
                    yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])
        elif "airgradient" in sensor_type.lower():
            for sensor in self.agf.get_sensors_from_file(sensor_dict, file):
                if sensor is not None:
                    yield from sensor.create_sensor_summaries(sensor_dict[sensor.id]["stationary_box"])
        else:
            raise ValueError(f"Unsupported sensor type: {sensor_type}")


# if __name__ == "__main__":
#     sfw = SensorFactoryWrapper()
#     summaries = list(sfw.fetch_sensor_community_data(dt.datetime(2023, 3, 31), dt.datetime(2023, 4, 1), {"60641,SDS011,60642,BME280": None}))
#     for summary in summaries:
#         print(summary.geom)
#     sfw = SensorFactoryWrapper()
#     summaries = list(sfw.fetch_sensor_community_data(dt.datetime(2023, 3, 31), dt.datetime(2023, 4, 1), {"60641,SDS011,60642,BME280": None}))
#     for summary in summaries:
#         print(summary.geom)
#     summaries = list(sfw.fetch_sensor_community_data(dt.datetime(2023, 3, 31), dt.datetime(2023, 4, 1), {"60641,SDS011,60642,BME280": None}))
#     for summary in summaries:
#         print(summary.geom)
