# dependancies:
import datetime as dt

from celeryWrapper import CeleryWrapper
from core.models import Sensors as ModelSensor
from core.schema import Sensor as SchemaSensor
from database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status

# error handling
from sqlalchemy.exc import IntegrityError

sensorsRouter = APIRouter()

db = SessionLocal()


@sensorsRouter.post("/add-sensor-platform/", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor):
    sensor = ModelSensor(
        lookup_id=sensor.lookup_id,
        serial_number=sensor.serial_number,
        type_id=sensor.type_id,
        active=sensor.active,
    )

    try:
        db.add(sensor)
        db.commit()
        return sensor
    except IntegrityError as e:
        #  if isinstance(e.orig, PG2UniqueViolation):
        #     raise UniqueViolation from e
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        db.rollback()


@sensorsRouter.get("/read-sensor-platform/")
def get_sensors():
    sensors = db.query(ModelSensor).all()
    return sensors


@sensorsRouter.put("/update-sensor-platform/{sensor_id}", response_model=SchemaSensor)
def update_sensor(sensor_id: int, sensor: SchemaSensor):

    sensor_updated = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
    sensor_updated.lookup_id = sensor.lookup_id
    sensor_updated.serial_number = sensor.serial_number
    sensor_updated.type_id = sensor.type_id
    sensor_updated.active = sensor.active

    try:
        db.commit()
        return sensor_updated
    except Exception as e:
        db.rollback()
        return None


@sensorsRouter.delete("/delete-sensor-platform/{sensor_id}", response_model=SchemaSensor)
def delete_sensor(sensor_id: int):
    sensor_deleted = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()

    try:
        db.delete(sensor_deleted)
        db.commit()
        return sensor_deleted
    except Exception as e:
        db.rollback()
        return None


@sensorsRouter.post("/add-plume-platform/")
def add_plume_sensors(sensor_serialnumbers: list[str] = Query(default=[])):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers"""
    api = CeleryWrapper()

    sensors = list(api.generate_plume_platform(sensor_serialnumbers))

    addedSensors = {}

    for sensor in sensors:
        addedSensors[sensor.serial_number] = sensor.lookup_id
        add_sensor(sensor)

    return addedSensors


@sensorsRouter.get("/read-active-sensors/")
def get_active_sensors(type_ids: list[int] = Query(default=[])):
    sensors = (
        db.query(ModelSensor.type_id, ModelSensor.lookup_id)
        .filter(ModelSensor.active == True, ModelSensor.type_id.in_(type_ids))
        .all()
    )
    return sensors


@sensorsRouter.patch("/set-active-sensors/")
def set_active_sensors(sensor_serialnumbers: list[str] | None = Query(None), active_state: bool = True):
    """Sets all sensors whose serialnumber matches to active"""

    try:
        db.query(ModelSensor).filter(ModelSensor.serial_number.in_(sensor_serialnumbers)).update(
            {ModelSensor.active: active_state}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return dict.fromkeys(sensor_serialnumbers, active_state)


@sensorsRouter.patch("/set-lastUpdated/{sensor_id}/{timestamp}")
def set_last_updated(sensor_id: int, timestamp: int):
    """Sets all sensors whose serialnumber matches to active"""

    try:
        db.query(ModelSensor).filter(ModelSensor.id == sensor_id).update(
            {ModelSensor.time_updated: dt.datetime.fromtimestamp(timestamp)}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {sensor_id: timestamp}


# functions for celery tasks
@sensorsRouter.get("/get-id-from-lookup/")
def sensor_id_from_lookup_id(lookup_id: str):
    sensor_id = db.query(ModelSensor.id).filter(ModelSensor.lookup_id == lookup_id).first()
    return sensor_id
