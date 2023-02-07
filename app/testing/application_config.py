import requests
from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorType

# sqlalchemy dependacies
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def admin_session():
    session = requests.Session()
    response = requests.post("http://localhost:8000/auth/dev-login", params={"uid": "admin", "role": "admin"})
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update({"Authorization": f"Bearer {response.json()}"})
    return session


def database_config():
    # docker database connection
    engine = create_engine("postgresql+psycopg2://postgres:password@localhost:5432/air_quality_db")
    # Base = declarative_base()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    return db
