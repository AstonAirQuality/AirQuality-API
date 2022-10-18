# dependancies:
from core.auth import AuthHandler
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorType as SchemaSensorType
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status

from routers.helpers.authSharedFunctions import checkRoleAdmin

sensorsTypesRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorsTypesRouter.post("/create", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """create a sensor type using the sensor type schema
    :param sensorType: sensor type schema
    :return: sensor type"""

    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensorType = ModelSensorType(name=sensorType.name, description=sensorType.description)
        db.add(sensorType)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return sensorType


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorsTypesRouter.get("/read")
def get_sensorTypes():
    """read all sensor types and return a json of sensor types
    :return: sensor types"""
    try:
        result = db.query(ModelSensorType).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve sensorTypes")
    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsTypesRouter.put("/update/{sensorType_id}", response_model=SchemaSensorType)
def update_sensorType(sensorType_id: int, sensorType: SchemaSensorType, payload=Depends(auth_handler.auth_wrapper)):
    """update a sensor type using the sensor type schema
    :param sensorType_id: sensor type id
    :param sensorType: sensor type schema
    :return: sensor type"""
    if checkRoleAdmin(payload) == False:
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
@sensorsTypesRouter.delete("/delete/{sensorType_id}")
def delete_sensorType(sensorType_id: int, payload=Depends(auth_handler.auth_wrapper)):
    """delete a sensor type using the sensor type id
    :param sensorType_id: sensor type id
    :return: sensor type"""
    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        sensorType_deleted = db.query(ModelSensorType).filter(ModelSensorType.id == sensorType_id).first()
        db.delete(sensorType_deleted)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorType_deleted
