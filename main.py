import datetime as dt
import json
from os import environ as env

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware, db
from geoalchemy2 import functions  # used to convert WKBE geometry to GEOSJON
from geoalchemy2.shape import to_shape  # used to convert WKBE geometry to WKT string
from sqlalchemy.exc import IntegrityError

from api_wrappers import plume
from models import Sensors
from models import Sensors as ModelSensor
from models import SensorSummaries
from models import SensorSummaries as ModelSensorSummary
from models import SensorTypes
from models import SensorTypes as ModelSensorType
from schema import Sensor as SchemaSensor
from schema import SensorSummary as SchemaSensorSummary
from schema import SensorType as SchemaSensorType

load_dotenv()

app = FastAPI()

app.add_middleware(DBSessionMiddleware, db_url=env["DATABASE_URL"])


@app.get("/")
async def root():
    sensor = plume.Plume(1, "test", 1, 1)
    return {"message": sensor}


@app.get("/read-sensors/")
def get_sensors():
    sensors = db.session.query(Sensors).all()

    return sensors


@app.get("/read-sensorTypes/")
def get_sensorTypes():
    result = db.session.query(SensorTypes).all()
    return result


# https://gis.stackexchange.com/questions/233184/converting-geoalchemy2-elements-wkbelement-to-wkt
@app.get("/read-sensorSummaries/{start}/{end}")
def get_sensorSummaries(start: str, end: str):

    # try:
    #     startDate = dt.datetime.strptime(start, "%Y-%m-%d")
    #     endDate = dt.datetime.strptime(end, "%Y-%m-%d")

    #     timestampStart = int(dt.datetime.timestamp(startDate.replace(tzinfo=dt.timezone.utc)))
    #     timestampEnd = int(dt.datetime.timestamp(endDate.replace(tzinfo=dt.timezone.utc)))
    # except (ValueError, TypeError):
    #     return "Http error bad request"

    result = (
        db.session.query(
            SensorSummaries.timestamp,
            SensorSummaries.sensor_id,
            functions.ST_AsGeoJSON(SensorSummaries.geom).label("geom"),
            SensorSummaries.measurement_data,
        )
        .filter(SensorSummaries.timestamp >= 0, SensorSummaries.timestamp <= 50)
        .all()
    )
    return result


@app.post("/add-sensorType/", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType):
    sensorType = ModelSensorType(name=sensorType.name, description=sensorType.description)
    db.session.add(sensorType)
    db.session.commit()
    return sensorType


@app.post("/add-sensor/", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor):
    sensor = ModelSensor(
        lookup_id=sensor.lookup_id,
        serial_number=sensor.serial_number,
        type_id=sensor.type_id,
        active=sensor.active,
    )
    db.session.add(sensor)
    db.session.commit()
    return sensor


@app.post("/add-sensorSummary/", response_model=SchemaSensorSummary)
def add_sensorSummary(sensorSummary: SchemaSensorSummary):
    sensorSummary = ModelSensorSummary(
        timestamp=sensorSummary.timestamp,
        sensor_id=sensorSummary.sensor_id,
        geom=sensorSummary.geom,
        measurement_count=sensorSummary.measurement_count,
        measurement_data=sensorSummary.measurement_data,
    )

    # wkt string is auto converted to wkb element in the model
    db.session.add(sensorSummary)
    db.session.commit()

    # converting wkb element to wkt string
    if sensorSummary.geom is not None:
        sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    # sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    return sensorSummary


@app.post("/upsert/", response_model=SchemaSensorSummary)
def upsert_sensorSummary(sensorSummary: SchemaSensorSummary):
    sensorSummary = ModelSensorSummary(
        timestamp=sensorSummary.timestamp,
        sensor_id=sensorSummary.sensor_id,
        geom=sensorSummary.geom,
        measurement_count=sensorSummary.measurement_count,
        measurement_data=sensorSummary.measurement_data,
    )

    try:
        # wkt string is auto converted to wkb element in the model
        db.session.add(sensorSummary)
        db.session.commit()
    # if the sensorSummary already exists, update it
    except IntegrityError as e:
        db.session.rollback()
        db.session.query(ModelSensorSummary).filter(
            ModelSensorSummary.timestamp == sensorSummary.timestamp,
            ModelSensorSummary.sensor_id == sensorSummary.sensor_id,
        ).update(
            {
                ModelSensorSummary.geom: sensorSummary.geom,
                ModelSensorSummary.measurement_count: sensorSummary.measurement_count,
                ModelSensorSummary.measurement_data: sensorSummary.measurement_data,
            }
        )
        db.session.commit()

    # converting wkb element to wkt string
    if sensorSummary.geom is not None:
        sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    # sensorSummary.geom = to_shape(sensorSummary.geom).wkt

    return sensorSummary


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
