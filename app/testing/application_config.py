import requests
from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorType
from fastapi.testclient import TestClient

# sqlalchemy dependacies
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def authenticate_client(client: TestClient, role: str = "admin"):
    response = client.post("http://localhost:8000/auth/dev-login", params={"uid": "admin", "role": "admin"})
    client.headers.update({"Content-Type": "application/json"})
    client.headers.update({"Authorization": f"Bearer {response.json()}"})
    return client


def database_config():
    # docker database connection
    engine = create_engine("postgresql+psycopg2://postgres:password@localhost:5432/air_quality_db")
    # Base = declarative_base()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    return db


def setUpSensorType(db, name, description, properties):
    """Setup a sensor type in the database"""
    try:
        result = db.query(ModelSensorType).filter(ModelSensorType.name == name).first()
        # if the sensor type does not exist then add it to the database and get the id
        if result is None:
            sensorType = ModelSensorType(name=name, description=description, properties=properties)
            db.add(sensorType)
            db.commit()
            return sensorType.id
        else:
            return result.id
    except Exception as e:
        db.rollback()
        raise e


def setUpSensor(db, lookup_id, serial_number, type_id, active, user_id, stationary_box):
    """Setup a sensor in the database"""
    try:
        result = db.query(ModelSensor).filter(ModelSensor.type_id == type_id and ModelSensor.lookup_id == lookup_id).first()
        # if the sensor type does not exist then add it to the database and get the id
        if result is None:
            sensor = ModelSensor(lookup_id=lookup_id, serial_number=serial_number, type_id=type_id, active=active, user_id=user_id, stationary_box=stationary_box)
            db.add(sensor)
            db.commit()
            return sensor.id
        else:
            return result.id
    except Exception as e:
        db.rollback()
        raise e
