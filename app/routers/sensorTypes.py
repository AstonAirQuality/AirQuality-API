# dependancies:
from core.authentication import AuthHandler
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorType as SchemaSensorType
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

sensorsTypesRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
# example properties: "{\"NO2\":\"ppb\",\"VOC\":\"ppb\",\"pm10\":\"ppb\",\"pm2.5\":\"ppb\",\"pm1\":\"ppb\"}"
@sensorsTypesRouter.post("", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """create a sensor type using the sensor type schema
    \n :param sensorType: sensor type schema
    \n :return: sensor type"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_add(ModelSensorType, sensorType.dict())


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorsTypesRouter.get("")
def get_sensorTypes():
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    return CRUD().db_get_with_model(ModelSensorType)


@sensorsTypesRouter.get("/{page}/{limit}")
def get_sensorTypes_paginated(page: int, limit: int):
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    return CRUD().db_get_with_model(ModelSensorType, page=page, limit=limit)


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsTypesRouter.put("/{sensorType_id}", response_model=SchemaSensorType)
def update_sensorType(sensorType_id: int, sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """update a sensor type using the sensor type schema
    \n :param sensorType_id: sensor type id
    \n :param sensorType: sensor type schema
    \n :return: sensor type"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelSensorType, [ModelSensorType.id == sensorType_id], sensorType.dict())


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorsTypesRouter.delete("/{sensorType_id}")
def delete_sensorType(sensorType_id: int, payload=Depends(auth_handler.auth_wrapper)):
    """delete a sensor type using the sensor type id
    \n :param sensorType_id: sensor type id
    \n :return: sensor type"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelSensorType, [ModelSensorType.id == sensorType_id])
