# dependancies:
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorType as SchemaSensorType
from db.database import SessionLocal
from fastapi import APIRouter, HTTPException, status

sensorsTypesRouter = APIRouter()

db = SessionLocal()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorsTypesRouter.post("/create", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType):
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
    try:
        result = db.query(ModelSensorType).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve sensorTypes")

    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@sensorsTypesRouter.put("/update/{sensorType_id}", response_model=SchemaSensorType)
def update_sensorType(sensorType_id: int, sensorType: SchemaSensorType):
    try:
        sensorType_updated = db.query(ModelSensorType).filter(ModelSensorType.id == sensorType_id).first()
        sensorType_updated.name = sensorType.name
        sensorType_updated.description = sensorType.description
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorType_updated


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@sensorsTypesRouter.delete("/delete/{sensorType_id}")
def delete_sensorType(sensorType_id: int):
    try:
        sensorType_deleted = db.query(ModelSensorType).filter(ModelSensorType.id == sensorType_id).first()
        db.delete(sensorType_deleted)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return sensorType_deleted
