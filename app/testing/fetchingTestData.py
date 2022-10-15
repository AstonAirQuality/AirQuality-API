# import json

# json_ = json.load(open("app\\testing\\test_data\\plume_LookupIds.json", "r"))
# print(json_)

import datetime as dt
import io  # TODO remove
import json
import pathlib  # TODO remove
import zipfile  # TODO remove
from os import environ as env

import pandas as pd
import requests  # TODO remove
from api_wrappers.plume_api_wrapper import PlumeWrapper
from dotenv import load_dotenv


class FetchTestData:
    def __init__(self):
        load_dotenv()
        self.pw = PlumeWrapper(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])

    def write_measurement_data_to_testdata_directory(self, sensor_id, start_date, end_date):
        """Fetches the measurement data for a given sensor"""
        try:
            sensor_data = {"measures": self.pw.get_sensor_measurement_data(sensor_id, start_date, end_date)}
            with open("./testing/test_data/plume_measurements.json", "w") as f:
                json.dump(sensor_data, f)

        except Exception as e:
            print(e)

    def read_measurement_data_from_testdata_directory(self):
        """Reads the measurement data from the testdata directory"""
        with open("./testing/test_data/measurementData.json", "r") as f:
            sensor_data = json.load(f)["measures"]
        return sensor_data

    def read_sensor_zip_from_testdata_directory(self):
        """Reads the sensor zip from the testdata directory"""
        with open("./testing/test_data/plume_sensor_data_with_locations.zip", "rb") as f:
            sensor_zip = f.read()
        zip_ = zipfile.ZipFile(io.BytesIO(sensor_zip))
        for name in zip_.namelist():

            # skip measurement data
            if "position" not in pathlib.PurePath(name).parts[3]:
                continue

        return pathlib.PurePath(name).parts[2].lstrip("sensor_"), io.StringIO(zip_.read(name).decode())

    # def extract_zip(self, link):
    #     """Download and extract zip into memory using link URL.

    #     :param link: url to sensor data zip file
    #     :return:sensor id, sensor data in a string buffer
    #     """
    #     res = requests.get(link, stream=True)
    #     if not res.ok:
    #         raise IOError(f"Failed to download zip file from link: {link}")
    #     zip_ = zipfile.ZipFile(io.BytesIO(res.content))
    #     for name in zip_.namelist():

    #         # skip measurement data
    #         if "position" not in pathlib.PurePath(name).parts[3]:
    #             continue

    #         # split path and strip string to extract sensor id and data
    #         yield pathlib.PurePath(name).parts[2].lstrip("sensor_"), io.StringIO(zip_.read(name).decode())


if __name__ == "__main__":
    ftd = FetchTestData()
    # (sensor, buffer) = ftd.read_sensor_zip_from_testdata_directory()
    # print(sensor)
    # print(buffer)
    ftd.write_measurement_data_to_testdata_directory(18749, dt.datetime(2022, 9, 28), dt.datetime(2022, 9, 30))
    # print(ftd.read_measurement_data_from_testdata_directory())


##################### getting measurements from plume #####################
# Note run as python module (testing) to avoid import errors
# import datetime as dt
# import json
# from os import environ as env

# from api_wrappers.plume_api_wrapper import PlumeWrapper
# from dotenv import load_dotenv

# load_dotenv()
# pw = PlumeWrapper(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])

# sensor_id = 18749
# start = dt.datetime(2022, 9, 10)
# end = dt.datetime(2022, 9, 12)

# data = pw.get_sensor_measurement_data(sensor_id, start, end)
# data = {"measures": data}

# # Directly from dictionary
# with open("./testing/test_data/measurementData.json", "w") as outfile:
#     json.dump(data, outfile)
##################### getting measurements from plume #####################

##################### reading measurements locally #####################
# import json

# import pandas as pd

# json_ = json.load(open("./testing/test_data/measurementData.json", "r"))

# dfList = []

# for measurements in json_[0]:
#     temp_df = pd.DataFrame([measurements])
#     dfList.append(temp_df)

# # concatenate all dataframes and prepare dataframe
# df = pd.concat(dfList, ignore_index=True)

# print(df)
##################### reading measurements locally #####################
