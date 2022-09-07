# dependancies:
import datetime as dt

from api_wrappers.scraperWrapper import ScraperWrapper
from core.models import Sensors as ModelSensor
from core.schema import Sensor as SchemaSensor
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

from routers.helperfunctions import convertWKBtoWKT

sensorsRouter = APIRouter()

db = SessionLocal()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorsRouter.post("/create", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor):
    sensor = ModelSensor(
        lookup_id=sensor.lookup_id,
        serial_number=sensor.serial_number,
        type_id=sensor.type_id,
        active=sensor.active,
        user_id=sensor.user_id,
        stationary_box=sensor.stationary_box,
    )

    try:
        db.add(sensor)
        db.commit()
        return sensor
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sensorsRouter.post("/create/plume")
def add_plume_sensors(sensor_serialnumbers: list[str] = Query(default=[])):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers"""
    api = ScraperWrapper()

    sensors = list(api.generate_plume_platform(sensor_serialnumbers))

    addedSensors = {}

    for sensor in sensors:
        try:
            add_sensor(sensor)
        except Exception:
            db.rollback()
            addedSensors[sensor.serial_number] = "failed to add sensor: " + sensor.lookup_id
            continue

        # write successfully added sensors to the return dict
        addedSensors[sensor.serial_number] = sensor.lookup_id

    return addedSensors


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorsRouter.get("/read")
def get_sensors():
    try:
        result = db.query(ModelSensor).all()

        # here we use the model to convert the result (geometry) into json since the query returned the model
        results = []
        for res in result:
            results.append(res.to_json())

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


@sensorsRouter.get("/read/active")
def get_active_sensors(type_ids: list[int] = Query(default=[])):
    try:
        result = (
            db.query(ModelSensor.type_id, ModelSensor.lookup_id, ModelSensor.stationary_box)
            .filter(ModelSensor.active == True, ModelSensor.type_id.in_(type_ids))
            .all()
        )
        # because the query returned row type we must convert wkb to wkt string to be be api friendly
        results = []
        for res in result:
            results.append((res[0], res[1], convertWKBtoWKT(res[2])))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return results


# functions for background tasks
@sensorsRouter.get("/read/sensorid-from-lookup/{lookup_id}")
def sensor_id_from_lookup_id(lookup_id: str):
    try:
        result = db.query(ModelSensor.id).filter(ModelSensor.lookup_id == lookup_id).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return result


@sensorsRouter.put("/update/{sensor_id}", response_model=SchemaSensor)
def update_sensor(sensor_id: int, sensor: SchemaSensor):
    try:
        sensor_updated = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        sensor_updated.lookup_id = sensor.lookup_id
        sensor_updated.serial_number = sensor.serial_number
        sensor_updated.type_id = sensor.type_id
        sensor_updated.active = sensor.active
        sensor_updated.stationary_box = sensor_updated.stationary_box
        sensor_updated.user_id = sensor_updated.user_id
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor_updated


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsRouter.patch("/update/active")
def set_active_sensors(sensor_serialnumbers: list[str] = Query(default=[]), active_state: bool = True):
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


@sensorsRouter.patch("/update/lastupdated/{sensor_id}/{timestamp}")
def set_last_updated(sensor_id: int, timestamp: int):
    """Sets all sensors last updated field whose id matches to sensor_id"""

    try:
        db.query(ModelSensor).filter(ModelSensor.id == sensor_id).update(
            {ModelSensor.time_updated: dt.datetime.fromtimestamp(timestamp)}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {sensor_id: timestamp}


@sensorsRouter.patch("/update/stationary_box/{sensor_id}/")
def set_stationary_box(sensor_id: int, stationary_box: str = Query(default=None)):
    """Sets all sensors stationary box field whose id matches to sensor_id"""
    try:
        db.query(ModelSensor).filter(ModelSensor.id == sensor_id).update({ModelSensor.stationary_box: stationary_box})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {sensor_id: stationary_box}


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorsRouter.delete("/delete/{sensor_id}", response_model=SchemaSensor)
def delete_sensor(sensor_id: int):
    try:
        sensor_deleted = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        db.delete(sensor_deleted)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor_deleted
