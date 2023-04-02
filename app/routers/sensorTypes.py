# dependancies:
from unittest import result

from core.authentication import AuthHandler
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorType as SchemaSensorType
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status

sensorsTypesRouter = APIRouter()

db = SessionLocal()
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

    try:
        sensorType = ModelSensorType(name=sensorType.name, description=sensorType.description, properties=sensorType.properties)
        db.add(sensorType)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return sensorType


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorsTypesRouter.get("")
def get_sensorTypes():
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    try:
        # NOTE: using the model ModelSensorType does not allow for response to be ordered by id,name,description,properties we must explicitly state the columns if we want to order the response
        result = db.query(ModelSensorType.id, ModelSensorType.name, ModelSensorType.description, ModelSensorType.properties).all()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve sensorTypes")
    return result


@sensorsTypesRouter.get("/{page}/{limit}")
def get_sensorTypes_paginated(page: int, limit: int):
    """read all sensor types and return a json of sensor types
    \n :return: sensor types"""
    try:
        # NOTE: using the model ModelSensorType does not allow for response to be ordered by id,name,description,properties we must explicitly state the columns if we want to order the response
        result = db.query(ModelSensorType.id, ModelSensorType.name, ModelSensorType.description, ModelSensorType.properties).offset((page - 1) * limit).limit(limit).all()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve sensorTypes")
    return result


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

    try:
        db.query(ModelSensorType).filter(ModelSensorType.id == sensorType_id).update(sensorType.dict())
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorType


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

    try:
        sensorType_deleted = db.query(ModelSensorType).filter(ModelSensorType.id == sensorType_id).first()
        db.delete(sensorType_deleted)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorType_deleted
