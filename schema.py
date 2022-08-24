import json
from typing import Optional

from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, validator


class SensorSummary(BaseModel):
    timestamp: int
    geom: Optional[str] = None
    measurement_count: int
    measurement_data: str
    sensor_id: int

    class Config:
        orm_mode = True

    @validator("geom", pre=True, always=True)
    def geom_must_contain(cls, v):
        try:
            WKTElement(v, srid=4326)
        except Exception as e:
            raise ValueError(f"geom must be a valid WKTE geometry: {e}")
        return v

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

    class Config:
        orm_mode = True


class SensorType(BaseModel):
    name: str
    description: str

    class Config:
        orm_mode = True


# https://pydantic-docs.helpmanual.io/usage/validators/


# ss = SensorSummary(
# **{
#   "timestamp": 62,
#   "geom": null,
#   "measurement_count": 1,
#   "measurement_data": "{\"action\": {\"name\": \"test\"}, \"reaction\": {\"name2\": \"test2\"}}",
#   "sensor_id": 1
# }
# )
