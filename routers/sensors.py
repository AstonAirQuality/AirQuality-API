# dependancies:
from core.models import Sensors as ModelSensor
from core.schema import PlumePlatform as SchemaPlumePlatform
from core.schema import Sensor as SchemaSensor
from database import SessionLocal
from fastapi import APIRouter, HTTPException, status
from nomans_functions import Nomans

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


@sensorsRouter.post("/add-plume-platform/", response_model=SchemaPlumePlatform)
def add_plume_sensors(plumeSensors: SchemaPlumePlatform):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers"""
    api = Nomans()

    sensors = list(api.generate_plume_platform(plumeSensors.serial_numbers))

    for sensor in sensors:
        add_sensor(sensor)

    return plumeSensors


@sensorsRouter.get("/read-active-sensors/")
def get_active_sensors():
    sensors = db.query(ModelSensor.type_id, ModelSensor.lookup_id).filter(ModelSensor.active == True).all()
    return sensors


@sensorsRouter.patch("/set-active-sensors/", response_model=SchemaPlumePlatform)
def set_active_sensors(sensors: SchemaPlumePlatform):
    """Sets all sensors whose serialnumber matches to active"""

    try:
        db.query(ModelSensor).filter(ModelSensor.serial_number.in_(sensors.serial_numbers)).update(
            {ModelSensor.active: True}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensors


# other functions
@sensorsRouter.get("/get-id-from-lookup/")
def sensor_id_from_lookup_id(lookup_id: str):
    sensor_id = db.query(ModelSensor.id).filter(ModelSensor.lookup_id == lookup_id).first()
    return sensor_id
