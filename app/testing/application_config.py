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
