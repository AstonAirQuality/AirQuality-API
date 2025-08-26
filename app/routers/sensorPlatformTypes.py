# dependancies:
from core.authentication import AuthHandler
from core.models import SensorPlatformTypes as ModelSensorPlatformTypePlatform
from core.schema import SensorPlatformType as SchemaSensorType
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

sensorPlatformTypesRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
# example sensor_metadata: "{\"NO2\":\"ppb\",\"VOC\":\"ppb\",\"pm10\":\"ppb\",\"pm2.5\":\"ppb\",\"pm1\":\"ppb\"}"
@sensorPlatformTypesRouter.post("", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """create a sensor type using the sensor type schema
    \n :param sensorType: sensor type schema
    \n :return: sensor type"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_add(ModelSensorPlatformTypePlatform, sensorType.dict())


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorPlatformTypesRouter.get("")
def get_sensorTypes():
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    return CRUD().db_get_with_model(ModelSensorPlatformTypePlatform)


@sensorPlatformTypesRouter.get("/{page}/{limit}")
def get_sensorTypes_paginated(page: int, limit: int):
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    return CRUD().db_get_with_model(ModelSensorPlatformTypePlatform, page=page, limit=limit)


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorPlatformTypesRouter.put("/{sensorType_id}", response_model=SchemaSensorType)
def update_sensorType(sensorType_id: int, sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """update a sensor type using the sensor type schema
    \n :param sensorType_id: sensor type id
    \n :param sensorType: sensor type schema
    \n :return: sensor type"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelSensorPlatformTypePlatform, [ModelSensorPlatformTypePlatform.id == sensorType_id], sensorType.dict())


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorPlatformTypesRouter.delete("/{sensorType_id}")
def delete_sensorType(sensorType_id: int, payload=Depends(auth_handler.auth_wrapper)):
    """delete a sensor type using the sensor type id
    \n :param sensorType_id: sensor type id
    \n :return: sensor type"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelSensorPlatformTypePlatform, [ModelSensorPlatformTypePlatform.id == sensorType_id])
