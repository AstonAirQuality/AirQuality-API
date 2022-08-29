# dependancies:
from celeryWrapper import CeleryWrapper
from core.models import SensorTypes as ModelSensorType
from core.schema import SensorType as SchemaSensorType
from database import SessionLocal
from fastapi import APIRouter

sensorsTypesRouter = APIRouter()

db = SessionLocal()


@sensorsTypesRouter.get("/read-sensorTypes/")
def get_sensorTypes():
    result = db.query(ModelSensorType).all()
    return result


@sensorsTypesRouter.post("/add-sensorType/", response_model=SchemaSensorType)
def add_sensorType(sensorType: SchemaSensorType):
    sensorType = ModelSensorType(name=sensorType.name, description=sensorType.description)
    db.add(sensorType)
    db.commit()
    return sensorType
