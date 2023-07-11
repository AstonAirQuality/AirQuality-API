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
    :sensor_id (str)"""

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
                    "measurement_data": '{"name":"Riyad","age":22,"course":"CS"}',
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


class Sensor(BaseModel):
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
    def stationary_box_must_be_valid_geometry(cls, v):
        try:
            if v is not None:
                shapely.wkt.loads(v)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
        return v


class SensorType(BaseModel):
    """SensorType Schema extends BaseModel used to validate form data from the API
    :name (str)
    :description (str)
    :properties (Dict[str, str])
    """

    name: str
    description: str
    properties: Dict[str, str]

    class Config:
        orm_mode = True
        read_with_orm_mode = True


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
