# dependancies:
import datetime as dt
from enum import Enum

from core.authentication import AuthHandler
from core.models import SensorPlatforms as ModelSensorPlatform
from core.models import SensorPlatformTypes as ModelSensorPlatformTypePlatforms
from core.models import Users as ModelUser
from core.schema import PlumeSerialNumbers as SchemaPlumeSerialNumbers
from core.schema import SensorPlatform as SchemaSensor
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from routers.services.crud.crud import CRUD
from routers.services.enums import ActiveReason
from routers.services.formatting import convertWKBtoWKT, format_sensor_joined_data
from routers.services.query_building import joinQueryBuilder
from sensor_api_wrappers.sensorPlatform_factory_wrapper import SensorPlatformFactoryWrapper

sensorPlatformsRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorPlatformsRouter.post("", response_model=SchemaSensor)
def add_sensor(sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):
    """Adds a sensor platform to the database using the sensor schema
    \n :param sensor: Sensor object to be added to the database
    \n :param payload: auth payload
    \n :return: sensor platform object"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    if sensor.active == True:
        sensor.active_reason = ActiveReason.ACTIVE_BY_USER.value
    else:
        sensor.active_reason = ActiveReason.DEACTVATE_BY_USER.value

    return CRUD().db_add(ModelSensorPlatform, sensor.dict())


@sensorPlatformsRouter.post("/plume-sensors")
def add_plume_sensors(serialnumbers: SchemaPlumeSerialNumbers, payload=Depends(auth_handler.auth_wrapper)):
    """Adds plume sensor platforms by scraping the plume dashboard to fetch the lookupids of the inputted serial numbers
    \n :param serialnumbers: list of serial numbers
    \n :param payload: auth payload
    \n :return: log of added/failed to add sensor platforms"""

    if auth_handler.checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    sfw = SensorPlatformFactoryWrapper()

    sensor_platforms = sfw.fetch_plume_platform_lookupids(serialnumbers.serial_numbers)

    addedSensors = {}

    for key, value in sensor_platforms.items():
        if value is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serial number not found")

        else:
            sensor = {
                "lookup_id": value,
                "serial_number": key,
                "type_id": 1,
                "active": False,
                "active_reason": ActiveReason.DEACTVATE_BY_USER.value,
                "user_id": None,
                "stationary_box": None,
            }

            CRUD().db_add(ModelSensorPlatform, sensor)

            # write successfully added sensors to the return dict
            addedSensors[key] = value
    return addedSensors


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorPlatformsRouter.get("")
def get_sensors():
    """Returns all sensor platforms in the database
    \n :return: list of sensors"""

    return CRUD().db_get_with_model(ModelSensorPlatform)


@sensorPlatformsRouter.get("/joined")
def get_sensors_joined(
    columns: list[str] = Query(default=["id", "lookup_id", "serial_number", "active", "active_reason", "stationary_box", "time_updated"]),
    join_sensor_types: bool = Query(default=True),
    join_user: bool = Query(default=True),
):
    """Returns all sensor platforms in the database
    \n :param columns: list of columns to return
    \n :param join_sensor_types: boolean to join sensor types
    \n :param join_user: boolean to join user
    \n :return: list of sensor platform"""

    join_dict = {}
    if join_user:
        join_dict[getattr(ModelUser, "username")] = "username"
        join_dict[getattr(ModelUser, "uid")] = "uid"
    if join_sensor_types:
        join_dict[getattr(ModelSensorPlatformTypePlatforms, "name")] = "type_name"

    fields = joinQueryBuilder(columns, ModelSensorPlatform, columns, join_dict)

    return format_sensor_joined_data(CRUD().db_get_fields_using_filter_expression(None, fields, ModelSensorPlatform, [ModelSensorPlatformTypePlatforms, ModelUser], first=False))


# get sensors joined paginated
@sensorPlatformsRouter.get("/joined/{page}/{limit}")
def get_sensors_joined_paginated(
    page: int,
    limit: int,
    columns: list[str] = Query(default=["id", "lookup_id", "serial_number", "active", "active_reason", "stationary_box", "time_updated"]),
    join_sensor_types: bool = Query(default=True),
    join_user: bool = Query(default=True),
):
    """Returns all paginated sensor platforms in the database
    \n :param page: page number
    \n :param limit: number of items per page
    \n :param columns: list of columns to return
    \n :param join_sensor_types: boolean to join sensor types
    \n :param join_user: boolean to join user
    \n :return: list of sensor platform"""

    join_dict = {}
    if join_user:
        join_dict[getattr(ModelUser, "username")] = "username"
        join_dict[getattr(ModelUser, "uid")] = "uid"
    if join_sensor_types:
        join_dict[getattr(ModelSensorPlatformTypePlatforms, "name")] = "type_name"

    fields = joinQueryBuilder(columns, ModelSensorPlatform, columns, join_dict)

    return format_sensor_joined_data(
        CRUD().db_get_fields_using_filter_expression(None, fields, ModelSensorPlatform, [ModelSensorPlatformTypePlatforms, ModelUser], first=False, page=page, limit=limit)
    )


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorPlatformsRouter.put("/{sensor_id}", response_model=SchemaSensor)
def update_sensor(sensor_id: int, input_sensor: SchemaSensor, payload=Depends(auth_handler.auth_wrapper)):
    """Updates a sensor platform in the database by sensor id using the sensor schema
    \n :param sensor_id: id of the sensor to be updated
    \n :param input_sensor: sensor object
    \n :param payload: auth payload
    \n :return: updated sensor platform"""

    if auth_handler.checkRoleAboveUser(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    sensor_to_update = CRUD().db_get_by_id(ModelSensorPlatform, sensor_id)
    if sensor_to_update is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    else:
        # only allow update if user is admin or sensor belongs to user (the auth token matches the user_id of the sensor)
        # if no user is asignned to the sensor, then anyone above user can update it
        if auth_handler.checkRoleAdmin(payload) == False:
            if sensor_to_update.user_id is not None & sensor_to_update.user_id != payload["sub"]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

        else:
            if input_sensor.active_reason is None:
                if input_sensor.active == True:
                    input_sensor.active_reason = ActiveReason.ACTIVE_BY_USER.value
                else:
                    input_sensor.active_reason = ActiveReason.DEACTVATE_BY_USER.value

            CRUD().clear_db_session()
            CRUD().db_update(ModelSensorPlatform, [ModelSensorPlatform.id == sensor_id], input_sensor.dict())

    return input_sensor


@sensorPlatformsRouter.patch("/active-status")
def set_active_sensors(
    sensor_serialnumbers: list[str] = Query(default=[]),
    active_state: bool = True,
    active_reason: ActiveReason = None,
    payload=Depends(auth_handler.auth_wrapper),
):
    """Sets all sensor platforms whose serialnumber matches to active
    \n :param sensor_serialnumbers: list of serialnumbers
    \n :param active_state: boolean to set active state
    \n :param payload: auth payload
    \n :return: list of updated sensor platforms"""

    auth_handler.checkRoleAdmin(payload)

    if active_reason is None:
        if active_state == True:
            active_reason = ActiveReason.ACTIVE_BY_USER.value
        else:
            active_reason = ActiveReason.DEACTVATE_BY_USER.value
    CRUD().db_update(ModelSensorPlatform, [ModelSensorPlatform.serial_number.in_(sensor_serialnumbers)], {ModelSensorPlatform.active: active_state, ModelSensorPlatform.active_reason: active_reason})
    return dict.fromkeys(sensor_serialnumbers, active_state)


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorPlatformsRouter.delete("/{sensor_id}")
def delete_sensor(sensor_id: int, payload=Depends(auth_handler.auth_wrapper)):
    """Deletes a sensor from the database
    \n :param sensor_id: id of the sensor to be deleted
    \n :param payload: auth payload
    \n :return: deleted sensor"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelSensorPlatform, [ModelSensorPlatform.id == sensor_id])
