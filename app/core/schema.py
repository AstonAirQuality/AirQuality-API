import json
from typing import Dict, List, Optional

import shapely.wkt
from fastapi import HTTPException, status
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, constr, validator


# TODO add validation for fields
class SensorSummary(BaseModel):
    """SensorSummary Schema extends BaseModel, used to validate form data from the API
    :timestamp (int)
    :geom (Optional[str]), WKTElement format
    :measurement_count (int)
    :measurement_data (str), JSON format
    :stationary (bool)
    :sensor_id (str)
    """

    timestamp: int
    geom: Optional[str] = None
    measurement_count: int
    measurement_data: str
    stationary: bool
    sensor_id: str

    class Config:
        orm_mode = True
        # TODO example schema
        schema_extra = {
            "examples": [
                {
                    "timestamp": 0,
                    "geom": None,
                    "measurement_count": 0,
                    "measurement_data": '{"name":"Test","age":22,"course":"CS"}',
                    "sensor_id": 51,
                }
            ]
        }

    @validator("geom", pre=True, always=True)
    def geom_must_be_valid_geometry(cls, v):
        """Validate that geom is a valid geometry
        :param v: geom
        :return: v if valid, raise HTTPException if not"""
        try:
            if v is not None:
                shapely.wkt.loads(v)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
        return v

    # TODO OPTIONAL additional validation - load to dataframe and check if columns exists (e.g timestamp,NO2,etc.)
    @validator("measurement_data", pre=True, always=True)
    def measurement_data_must_be_json(cls, v):
        """Validate that measurement_data is a valid JSON
        :param v: measurement_data
        :return: v if valid, raise HTTPException if not"""
        try:
            json.loads(v)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"measurement_data must be a valid json: {e}")
        return v


class SensorPlatform(BaseModel):
    """Sensor Schema extends BaseModel used to validate form data from the API
    :lookup_id (str)
    :serial_number (str)
    :type_id (int)
    :active (bool)
    :active_reason (Optional[str])
    :stationary_box (str), WKTElement format
    :user_id (str)
    """

    lookup_id: str
    serial_number: str
    type_id: int
    active: bool
    active_reason: Optional[str] = None
    user_id: Optional[str] = None
    stationary_box: Optional[str] = None

    class Config:
        orm_mode = True

    @validator("stationary_box", pre=True, always=True)
    def stationary_box_must_be_box_polygon(cls, v):
        try:
            if v is not None:
                geom = shapely.wkt.loads(v)
                if geom.geom_type != "Polygon":
                    raise ValueError("stationary_box must be a Polygon")
                # Check if the polygon is a rectangle (box) by getting the coordinates from the string
                if len(geom.exterior.coords) != 5:
                    raise ValueError("stationary_box must be a rectangular box polygon (WKT)")
                # Check if the first and last coordinates are the same (closed polygon)
                if geom.exterior.coords[0] != geom.exterior.coords[-1]:
                    raise ValueError("stationary_box must be a closed polygon (first and last coordinates must be the same)")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"stationary_box must be a valid rectangular box polygon (WKT): {e}")
        return v


class SensorPlatformType(BaseModel):
    """SensorType Schema extends BaseModel used to validate form data from the API
    :name (str)
    :description (str)
    :sensor_metadata (Dict[str, str])
    """

    name: str
    description: str
    sensor_metadata: Dict[str, object]

    class Config:
        orm_mode = True
        read_with_orm_mode = True

    @validator("sensor_metadata", pre=True, always=True)
    def sensor_metadata_must_be_valid_csvw(cls, v):
        """Validate that sensor_metadata is a valid CSVW JSON
        :param v: sensor_metadata
        :return: v if valid, raise HTTPException if not"""
        try:
            if isinstance(v, str):
                v = json.loads(v)
            if not isinstance(v, dict):
                raise ValueError("sensor_metadata must be a valid JSON object")

            if "columns" not in v["tableSchema"] or not isinstance(v["tableSchema"]["columns"], list) or len(v["tableSchema"]["columns"]) == 0:
                raise ValueError("sensor_metadata must contain a 'columns' key with a non-empty list")
            for column in v["tableSchema"]["columns"]:
                if not isinstance(column, dict):
                    raise ValueError("each column in sensor_metadata must be a JSON object")
                if "name" not in column or not isinstance(column["name"], str):
                    raise ValueError("each column in sensor_metadata must contain a 'name' key of type string")
                if "datatype" not in column or not isinstance(column["datatype"], str):
                    raise ValueError("each column in sensor_metadata must contain a 'datatype' key of type string")
                # if a processing step is defined, it must be a list of dictionaries
                if "http://www.w3.org/ns/sosa/usedProcedure" in column:
                    if not isinstance(column["http://www.w3.org/ns/sosa/usedProcedure"], list) or not all(isinstance(proc, dict) for proc in column["http://www.w3.org/ns/sosa/usedProcedure"]):
                        raise ValueError("the 'http://www.w3.org/ns/sosa/usedProcedure' key in each column must be a list of JSON objects")

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"metadata must be a valid CSVW JSON: {e}")
        return v


class SensorTypeConfig(BaseModel):
    """SensorPlatformTypeConfig table extends Base class from database.py
    stores configuration for generic sensor platform types

    Args:
        sensor_type_id (int): foreign key to SensorTypes table
        authentication_url (Optional[str]): URL for authentication
        authentication_method (Optional[Dict[str, str]]): JSON object containing authentication method details
        api_url (str): URL for the API endpoint for fetching sensor data of the platform type
        api_method (Dict[str, str]): HTTP method for the API (GET, POST, etc. and its headers)
    """

    sensor_type_id: int
    authentication_url: Optional[str] = None
    authentication_method: Optional[Dict[str, object]] = None
    api_url: str
    api_method: Dict[str, object]
    sensor_mappings: Dict[str, str]

    class Config:
        orm_mode = True
        read_with_orm_mode = True


class ObservableProperties(BaseModel):
    """ObservableProperties Schema extends BaseModel used to validate form data from the API

    Args:
        name (str): unique name of the observable property
        url (str): URL for the observable property
        description (Optional[str]): description of the observable property
        datatype (str): data type of the observable property (e.g., int, float, str)
    """

    name: str
    url: str
    description: Optional[str] = None
    datatype: str

    class Config:
        orm_mode = True
        read_with_orm_mode = True


class UnitsOfMeasurement(BaseModel):
    """UnitsOfMeasurement Schema extends BaseModel used to validate form data from the API

    Args:
        name (str): unique name of the unit of measurement (primary key)
        url (str): URL for the unit of measurement
        symbol (str): symbol representing the unit of measurement
    """

    name: str
    url: str
    symbol: str

    class Config:
        orm_mode = True
        read_with_orm_mode = True


class UserCredentials(BaseModel):
    """UserCredentials Schema extends BaseModel used to validate form data from the API"""

    username: str
    password: str


class User(BaseModel):
    """User Schema extends BaseModel used to validate form data from the API
    :uid (str)
    :username (Optional[str])
    :email (str)
    :role (str)
    """

    uid: str
    username: Optional[str] = None
    email: str
    role: str

    class Config:
        orm_mode = True


class Log(BaseModel):
    """Log Schema extends BaseModel used to validate form data from the API
    :log_data (str)
    """

    log_data: str

    class Config:
        orm_mode = True

        # TODO OPTIONAL additional validation - load to dataframe and check if columns exists (e.g timestamp,sensorid,etc.)
        @validator("log_data", pre=True, always=True)
        def data_must_be_json(cls, v):
            try:
                json.loads(v)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"measurement_data must be a valid json: {e}")
            return v


class DataIngestionLog(BaseModel):
    """DataIngestionLog Schema extends BaseModel used to validate form data from the API
    :sensor_id (int)
    :timestamp (int)
    :sensor_serial_number (str)
    :success_status (bool)
    :error_message (str)
    """

    sensor_id: int
    sensor_serial_number: str
    timestamp: int
    success_status: bool
    message: Optional[str] = None

    class Config:
        orm_mode = True


class PlumeSerialNumbers(BaseModel):
    """PlumeSerialNumbers Schema extends BaseModel used to validate form data from the API
    :serial_numbers (List[str])
    """

    serial_numbers: List[str]


class GeoJsonExport(BaseModel):
    """GeoJsonExport Schema extends BaseModel used to validate form data from the API
    :sensorid (int)
    :sensorType (Optional[str])
    :geojson (Dict), GeoJSON format
    """

    sensorid: int
    sensorType: Optional[str] = None
    geojson: Dict
