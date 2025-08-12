This document provides instructions for adding new sensor platforms to the AirQuality-API project. It includes guidelines on how to implement the necessary code changes, update existing files, and ensure compatibility with the current system architecture.

# Adding Sensor Platforms
To add a new sensor platform to the AirQuality-API, you will need to follow these steps:

## Using the backend
1. Authenticate with the AirQuality-API backend, you can use the dev_login endpoint to get a token in the development environment.
2. Create a new sensor platform type using the **POST** endpoint `/sensor_platform-type`. 
    - This will require you to provide the following:
        - Name: A unique identifier for the sensor platform.
        - Description: A brief description of the sensor platform.
        - Properties: (JSON) Define the measurements and units for the sensor platform.

## Using the frontend
1. Login to the Webapp and navigate to the "Manage Sensor Platform Types" section.
2. Click on "Create New SensorPlatformType" and fill in the required fields:
    - Name: A unique identifier for the sensor platform.
    - Description: A brief description of the sensor platform.
    - Properties: (JSON) Define the measurements and units for the sensor platform.
3. Click submit to create the new sensor platform type.

# Adding A New Sensor Platform
To add a new sensor platform to the AirQuality-API, you will need to follow these steps:

## Using the backend
1. Authenticate with the AirQuality-API backend, you can use the dev_login endpoint to get a token in the development environment.
2. Create a new sensor platform using the **POST** endpoint `/sensor_platform`.
    - This will require you to provide the following:
        - Lookup ID: A unique identifier for the sensor platform.
            - If a sensor platform is made up of multiple sensors you should use comma separated values for each sensor's lookup ID. For example: `"lookup_id": "60641,SDS011,60642,BME280"`.
        - Serial Number: A unique serial number of the sensor platform.
        - Type ID: The ID of the sensor platform type you created earlier.
        - Active: A boolean indicating if the sensor platform is active.
        - Active Reason (Optionsal): A reason for the sensor platform's active status. Optionally leave it as null.
        - User ID (Optional): The ID of the user who owns the sensor platform.
        - Stationary Box (Optional): A JSON string defining the stationary box for the sensor platform.

## Using the frontend
1. Login to the Webapp and navigate to the "Manage Sensor Platforms" section.
2. Click on "Create New SensorPlatform" and fill in the required fields:
    - Lookup ID: A unique identifier for the sensor platform.
        - If a sensor platform is made up of multiple sensors you should use comma separated values for each sensor's lookup ID. For example: `"lookup_id": "60641,SDS011,60642,BME280"`.
    - Serial Number: A unique serial number of the sensor platform.
    - Type ID: The ID of the sensor platform type you created earlier.
    - Active: A boolean indicating if the sensor platform is active.
    - Active Reason (Optional): A reason for the sensor platform's active status. Optionally leave it as null.
    - User ID (Optional): The ID of the user who owns the sensor platform.
    - Stationary Box (Optional): A JSON string defining the stationary box for the sensor platform.

# Developing The Sensor Data Ingestion Pipeline
To develop the sensor data ingestion pipeline for the new sensor platform, you will need to implement the following steps:
1. **Create A Sensor Factory**: Implement a new sensor factory class that inherits from the `SensorFactory` base class. This class should handle the specific logic for fetching data for the new sensor platform via an API, web scraping, web hooks, or any other method. Preprocessing for fethcing data like authentication, pagination, and rate limiting should be handled in this class.
    - The factory should implement the `fetch_data` method which will return an iterator of sensor data.
    - If the sensor platform requires authentication, ensure that the factory handles the login process before fetching data.
    - If the sensor platform has multiple sensors, ensure that the factory can handle fetching data for each sensor individually and return the data in a unified format.

2. **Create A Sensor Product**: Implement a new sensor product class that inherits from the `SensorProduct` base class. This class should process the data fetched by the sensor factory and convert it into a a timeseries dataframe. 
    - Longitude and latitude columns should be added to the dataframe if they are not already present. Leave them as null if they are not available or you are dealing with a stationary sensor.
    - The timestamp column should be in UTC format and should be named `timestamp`.
    - Map the sensor measurements to the columns in the `SensorMeasurementsColumns` enum. If the sensor platform has additional measurements that are not in the enum, you can add them to the `SensorMeasurementsColumns` enum.

3. **Update Sensor Factory Wrapper**: Update the `SensorFactoryWrapper.py` class to include the new sensor factory and product classes. This will allow the wrapper to handle the new sensor platform when fetching data.

4. **Update Background Tasks**: Update the `backgroundTasks.py` to include the new sensor platform in the data ingestion pipeline. This is only required for the **POST** endpoint `/upload-file` where users can upload sensor data files. The background task will need to handle the new sensor platform and process the data accordingly.


# Testing
To ensure that the new sensor platform is working correctly, you should implement the following tests:
1. **Manual Testing**: Manually test the new sensor platform by starting a data ingestion task using the cron job **GET** endpoint `api-task/cron/ingest-active-sensors/` (You need to set your sensor platform as active), or the **POST** endpoint `api-task/schedule/ingest-bysensorid`.
    - Verify that the data is being fetched correctly by checking the data ingestion logs for any errors
    - Check the sensor summary data using the **GET** endpoint `/sensor_summary/as-json`(you can use as-geojson, or as-csv too) to ensure that the data is being processed correctly.
2. **Automated Tests**: Implement automated unit/integration tests for the new sensor platform in the `tests` directory.
    - Create a new test file for the sensor platform in the `testing/` directory.
    - Use the `unittest` framework to write tests for the sensor factory and product classes.
    - Ensure that the tests cover the following:
        - Fetching data from the sensor platform
        - Processing the data into a timeseries dataframe
        - Handling of authentication, pagination, and rate limiting, if applicable
        - Handling of multiple sensors if applicable
        - Error handling and edge cases
    - Add the tests to the relevant test suite in the `tests` directory to ensure for coverage and test reports or for CI/CD pipelines.
