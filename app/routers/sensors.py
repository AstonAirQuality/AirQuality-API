# dependancies:
import datetime as dt

from api_wrappers.scraperWrapper import ScraperWrapper
from core.auth import AuthHandler
from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorTypes  # TODO
from core.models import Users as ModelUser  # TODO
from core.schema import PlumeSerialNumbers as SchemaPlumeSerialNumbers
from core.schema import Sensor as SchemaSensor
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

from routers.helpers.authSharedFunctions import checkRoleAboveUser, checkRoleAdmin
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

sensorsRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorsRouter.post("/create", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):

    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

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
def add_plume_sensors(
    serialnumbers: SchemaPlumeSerialNumbers, response: Response, payload=Depends(auth_handler.auth_wrapper)
):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers"""

    if checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    api = ScraperWrapper()

    sensor_platforms = api.fetch_plume_platform_lookupids(serialnumbers.serial_numbers)

    addedSensors = {}

    for (key, value) in sensor_platforms.items():
        sensor = ModelSensor(
            lookup_id=value,
            serial_number=key,
            type_id=1,
            active=False,
            user_id=None,
            stationary_box=None,
        )

        try:
            add_sensor(sensor, payload)

        except HTTPException as e:
            # if the sensor already exists continue adding other sensors but change status code to 409
            if e.status_code == 409:
                addedSensors[key] = "Sensor already exists"
                response.status_code = status.HTTP_409_CONFLICT
                continue
            else:
                raise e
        except Exception as e:
            db.rollback()
            addedSensors[key] = "failed to add sensor: " + str(value)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=addedSensors)

        # write successfully added sensors to the return dict
        addedSensors[key] = value

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


@sensorsRouter.get("/read/join-users-sensor-types")
def get_sensors_joined(
    columns: list[str] = Query(
        default=["id", "lookup_id", "serial_number", "active", "stationary_box", "time_updated"]
    ),
    join_sensor_types: bool = Query(default=True),
    join_user: bool = Query(default=True),
):
    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensor, col))

        if join_sensor_types:
            fields.append(getattr(ModelSensorTypes, "name").label("type_name"))
        if join_user:
            fields.append(getattr(ModelUser, "username").label("username"))

        result = db.query(*fields).select_from(ModelSensor).join(ModelSensorTypes, ModelUser, isouter=True).all()

        # must convert wkb to wkt string to be be api friendly
        results = []
        for row in result:
            row_as_dict = dict(row._mapping)
            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            results.append(row_as_dict)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


# functions for background tasks
# @sensorsRouter.get("/read/active")
def get_active_sensors(type_ids: list[int] = Query(default=[])):
    try:
        result = (
            db.query(
                ModelSensor.type_id.label("type_id"),
                ModelSensor.lookup_id.label("lookup_id"),
                ModelSensor.stationary_box.label("stationary_box"),
            )
            .filter(ModelSensor.active == True, ModelSensor.type_id.in_(type_ids))
            .all()
        )
        # because the query returned row type we must convert wkb to wkt string to be be api friendly
        results = []
        for row in result:
            row_as_dict = dict(row._mapping)
            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            results.append(row_as_dict)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return results


# functions for background tasks
# @sensorsRouter.get("/read/sensorid-from-lookup/{lookup_id}")
def sensor_id_from_lookup_id(lookup_id: str):
    try:
        result = db.query(ModelSensor.id.label("id")).filter(ModelSensor.lookup_id == lookup_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsRouter.put("/update/{sensor_id}", response_model=SchemaSensor)
def update_sensor(sensor_id: int, sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):

    if checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensor_updated = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        if sensor_updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
        else:
            # only allow update if user is admin or sensor belongs to user (the auth token matches the user_id of the sensor)
            # if no user is asignned to the sensor, then anyone above user can update it
            if checkRoleAdmin(payload) == False:
                if sensor_updated.user_id is not None & sensor_updated.user_id != payload["sub"]:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

            # else update sensor
            sensor_updated.lookup_id = sensor.lookup_id
            sensor_updated.serial_number = sensor.serial_number
            sensor_updated.type_id = sensor.type_id
            sensor_updated.active = sensor.active
            sensor_updated.user_id = sensor.user_id
            sensor_updated.stationary_box = sensor.stationary_box
            db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor


@sensorsRouter.patch("/update/active")
def set_active_sensors(
    sensor_serialnumbers: list[str] = Query(default=[]),
    active_state: bool = True,
    payload=Depends(auth_handler.auth_wrapper),
):
    """Sets all sensors whose serialnumber matches to active"""

    checkRoleAdmin(payload)

    try:
        db.query(ModelSensor).filter(ModelSensor.serial_number.in_(sensor_serialnumbers)).update(
            {ModelSensor.active: active_state}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return dict.fromkeys(sensor_serialnumbers, active_state)


# used for background tasks
# @sensorsRouter.patch("/update/lastupdated/{sensor_id}/{timestamp}")
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


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorsRouter.delete(
    "/delete/{sensor_id}",
    response_model=SchemaSensor,
)
def delete_sensor(sensor_id: int, payload=Depends(auth_handler.auth_wrapper)):

    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensor_deleted = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        db.delete(sensor_deleted)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor_deleted
