import json
from typing import Dict, List, Optional

from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, constr, validator


# TODO add validation for fields
class SensorSummary(BaseModel):
    timestamp: int
    geom: Optional[str] = None
    measurement_count: int
    measurement_data: str
    stationary: bool
    sensor_id: int

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
    def geom_must_contain(cls, v):
        try:
            WKTElement(v, srid=4326)
        except Exception as e:
            raise ValueError(f"geom must be a valid WKTE geometry: {e}")
        return v

    # TODO add validation - load to dataframe and check if timestamp is included
    @validator("measurement_data", pre=True, always=True)
    def measurement_data_must_be_json(cls, v):
        try:
            json.loads(v)
        except Exception as e:
            raise ValueError(f"measurement_data must be a valid JSON: {e}")
        return v


class Sensor(BaseModel):
    lookup_id: str
    serial_number: str
    type_id: int
    active: bool
    user_id: Optional[str] = None
    stationary_box: Optional[str] = None

    class Config:
        orm_mode = True

    @validator("stationary_box", pre=True, always=True)
    def stationary_box_must_contain(cls, v):
        try:
            WKTElement(v, srid=4326)
        except Exception as e:
            raise ValueError(f"stationary_box must be a valid WKTE geometry: {e}")
        return v


class SensorType(BaseModel):
    name: str
    description: str

    class Config:
        orm_mode = True


class User(BaseModel):
    uid: str
    username: Optional[str] = None
    email: str
    role: str

    class Config:
        orm_mode = True


class Log(BaseModel):
    log_data: str

    class Config:
        orm_mode = True

        # TODO add validation - load to dataframe and check if timestamp is included
        @validator("log_data", pre=True, always=True)
        def data_must_be_json(cls, v):
            try:
                json.loads(v)
            except Exception as e:
                raise ValueError(f"data must be a valid JSON: {e}")
            return v


class PlumeSerialNumbers(BaseModel):
    serial_numbers: List[str]
