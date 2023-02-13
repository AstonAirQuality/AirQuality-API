# dependancies:
import datetime as dt

from api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from core.authentication import AuthHandler
from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorTypes  # TODO
from core.models import Users as ModelUser  # TODO
from core.schema import PlumeSerialNumbers as SchemaPlumeSerialNumbers
from core.schema import Sensor as SchemaSensor
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from psycopg2.errors import ForeignKeyViolation, UniqueViolation
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

# error handling
from sqlalchemy.exc import IntegrityError

sensorsRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorsRouter.post("", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):
    """Adds a sensor to the database using the sensor schema
    \n :param sensor: Sensor object to be added to the database
    \n :param payload: auth payload
    \n :return: Sensor object"""

    if auth_handler.checkRoleAdmin(payload) == False:
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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sensorsRouter.post("/plume-sensors")
def add_plume_sensors(serialnumbers: SchemaPlumeSerialNumbers, response: Response, payload=Depends(auth_handler.auth_wrapper)):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers
    \n :param serialnumbers: list of serial numbers
    \n :param response: response object
    \n :param payload: auth payload
    \n :return: log of added/failed to add sensors"""

    if auth_handler.checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    sfw = SensorFactoryWrapper()

    sensor_platforms = sfw.fetch_plume_platform_lookupids(serialnumbers.serial_numbers)

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
@sensorsRouter.get("")
def get_sensors():
    """Returns all sensors in the database
    \n :return: list of sensors"""
    try:
        result = db.query(ModelSensor).all()

        # here we use the model to convert the result (geometry) into json since the query returned the model
        results = []
        for res in result:
            results.append(res.to_json())

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


@sensorsRouter.get("/joined")
def get_sensors_joined(
    columns: list[str] = Query(default=["id", "lookup_id", "serial_number", "active", "stationary_box", "time_updated"]),
    join_sensor_types: bool = Query(default=True),
    join_user: bool = Query(default=True),
):
    """Returns all sensors in the database
    \n :param columns: list of columns to return
    \n :param join_sensor_types: boolean to join sensor types
    \n :param join_user: boolean to join user
    \n :return: list of sensors"""

    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensor, col))

        if join_sensor_types:
            fields.append(getattr(ModelSensorTypes, "name").label("type_name"))
        if join_user:
            fields.append(getattr(ModelUser, "username").label("username"))
            fields.append(getattr(ModelUser, "uid").label("uid"))

        result = db.query(*fields).select_from(ModelSensor).join(ModelSensorTypes, ModelUser, isouter=True).all()

        # must convert wkb to wkt string to be be api friendly
        results = []
        for row in result:
            row_as_dict = dict(row._mapping)
            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            if "username" in row_as_dict and "uid" in row_as_dict:
                row_as_dict["username"] = str(row_as_dict["username"]) + " " + str(row_as_dict["uid"])
                del row_as_dict["uid"]
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


# get sensors joined paginated
@sensorsRouter.get("/joined/{page}/{limit}")
def get_sensors_joined_paginated(
    page: int,
    limit: int,
    columns: list[str] = Query(default=["id", "lookup_id", "serial_number", "active", "stationary_box", "time_updated"]),
    join_sensor_types: bool = Query(default=True),
    join_user: bool = Query(default=True),
):

    """Returns all paginated sensors in the database
    \n :param page: page number
    \n :param limit: number of items per page
    \n :param columns: list of columns to return
    \n :param join_sensor_types: boolean to join sensor types
    \n :param join_user: boolean to join user
    \n :return: list of sensors"""

    try:
        fields = []
        for col in columns:
            fields.append(getattr(ModelSensor, col))

        if join_sensor_types:
            fields.append(getattr(ModelSensorTypes, "name").label("type_name"))
        if join_user:
            fields.append(getattr(ModelUser, "username").label("username"))
            fields.append(getattr(ModelUser, "uid").label("uid"))

        # result = db.query(*fields).select_from(ModelSensor).join(ModelSensorTypes, ModelUser, isouter=True).all()
        result = db.query(*fields).select_from(ModelSensor).join(ModelSensorTypes, ModelUser, isouter=True).offset((page - 1) * limit).limit(limit).all()

        # must convert wkb to wkt string to be be api friendly
        results = []
        for row in result:
            row_as_dict = dict(row._mapping)
            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            if "username" in row_as_dict and "uid" in row_as_dict:
                row_as_dict["username"] = str(row_as_dict["username"]) + " " + str(row_as_dict["uid"])
                del row_as_dict["uid"]
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsRouter.put("/{sensor_id}", response_model=SchemaSensor)
def update_sensor(sensor_id: int, sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):
    """Updates a sensor in the database by sensor id using the sensor schema
    \n :param sensor_id: id of the sensor to be updated
    \n :param sensor: sensor object
    \n :param payload: auth payload
    \n :return: updated sensor"""

    if auth_handler.checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensor_updated = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        if sensor_updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
        else:
            # only allow update if user is admin or sensor belongs to user (the auth token matches the user_id of the sensor)
            # if no user is asignned to the sensor, then anyone above user can update it
            if auth_handler.checkRoleAdmin(payload) == False:
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

    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
        elif isinstance(e.orig, ForeignKeyViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])

        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor


@sensorsRouter.patch("/active-status")
def set_active_sensors(
    sensor_serialnumbers: list[str] = Query(default=[]),
    active_state: bool = True,
    payload=Depends(auth_handler.auth_wrapper),
):
    """Sets all sensors whose serialnumber matches to active
    \n :param sensor_serialnumbers: list of serialnumbers
    \n :param active_state: boolean to set active state
    \n :param payload: auth payload
    \n :return: list of updated sensors"""

    auth_handler.checkRoleAdmin(payload)

    try:
        db.query(ModelSensor).filter(ModelSensor.serial_number.in_(sensor_serialnumbers)).update({ModelSensor.active: active_state})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return dict.fromkeys(sensor_serialnumbers, active_state)


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorsRouter.delete("/{sensor_id}", response_model=SchemaSensor)
def delete_sensor(sensor_id: int, payload=Depends(auth_handler.auth_wrapper)):
    """Deletes a sensor from the database
    \n :param sensor_id: id of the sensor to be deleted
    \n :param payload: auth payload
    \n :return: deleted sensor"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensor_deleted = db.query(ModelSensor).filter(ModelSensor.id == sensor_id).first()
        db.delete(sensor_deleted)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensor_deleted
