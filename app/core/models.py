from db.database import Base
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# TODO avoid names with '_'


class Logs(Base):
    __tablename__ = "Logs"
    date = Column(DateTime, primary_key=True, default=func.now())
    data = Column(JSON, nullable=False)


class Users(Base):
    __tablename__ = "Users"
    uid = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), nullable=True)
    email = Column(String(50), unique=True, nullable=False)
    role = Column(String(50), nullable=False)


class SensorTypes(Base):
    __tablename__ = "SensorTypes"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(50), nullable=False)


class Sensors(Base):
    __tablename__ = "Sensors"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    lookup_id = Column(String(50), nullable=True)
    serial_number = Column(String(50), unique=True)
    active = Column(Boolean, nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime, nullable=True)
    stationary_box = Column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), unique=False, nullable=True
    )
    user_id = Column(String(50), ForeignKey("Users.uid"), nullable=True)
    type_id = Column(Integer, ForeignKey("SensorTypes.id"), nullable=False)

    sensorTypeFK = relationship("SensorTypes")
    userFK = relationship("Users")

    def to_json(self):
        return {
            "id": self.id,
            "lookup_id": self.lookup_id,
            "serial_number": self.serial_number,
            "active": self.active,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "stationary_box": to_shape(self.stationary_box).wkt if self.stationary_box else None,
            "user_id": self.user_id,
            "type_id": self.type_id,
        }


class SensorSummaries(Base):

    __tablename__ = "SensorSummaries"
    timestamp = Column(Integer, primary_key=True, nullable=False)
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), unique=False, nullable=True
    )  # TODO check if spatial index is needed for alembic
    measurement_count = Column(Integer, nullable=False)
    measurement_data = Column(JSON, nullable=False)
    stationary = Column(Boolean, nullable=False)
    sensor_id = Column(Integer, ForeignKey("Sensors.id"), primary_key=True, nullable=False)

    # relationship to sensors table
    SensorId_fk = relationship("Sensors")

    def to_json(self):
        return {
            "timestamp": self.timestamp,
            "geom": to_shape(self.geom).wkt if self.geom else None,
            "measurement_count": self.measurement_count,
            "measurement_data": self.measurement_data,
            "stationary": self.stationary,
            "sensor_id": self.sensor_id,
        }
