from db.database import Base
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# TODO avoid names with '_'


class Logs(Base):
    """Logs table extends Base class from database.py
    :date (DateTime)
    :data (JSON), log data in JSON format of data ingestion of multiple sensors"""

    __tablename__ = "Logs"
    date = Column(DateTime, primary_key=True, default=func.now())
    data = Column(JSON, nullable=False)


class Users(Base):
    """Users table extends Base class from database.py
    :uid or userid (Integer), primary key
    :username (String)
    :email (String), unique
    :password (String)
    :role (String)
    """

    __tablename__ = "Users"
    uid = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), nullable=True)
    email = Column(String(50), unique=True, nullable=False)
    role = Column(String(50), nullable=False)


class SensorTypes(Base):
    """SensorTypes table extends Base class from database.py
    :id (Integer), primary key
    :sensortype_name (String),
    :description (String)"""

    __tablename__ = "SensorTypes"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(250), nullable=False)
    properties = Column(JSON, nullable=False)

    def columns_iter():
        for c in SensorTypes.__getattribute__("__table__").columns:
            yield c.name


class Sensors(Base):
    """Sensors table extends Base class from database.py
    :id (Integer): primary key
    :lookup_id (String), unique
    :serial_number (String), unique
    :active (Boolean)
    :active_reason (String)
    :time_created (DateTime)
    :time_updated (DateTime)
    :stationary_box (Geometry)
    :user_id (Integer), foreign key
    :type_id (Integer), foreign key"""

    __tablename__ = "Sensors"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    lookup_id = Column(String(50), nullable=True)
    serial_number = Column(String(50), unique=True)
    active = Column(Boolean, nullable=False)
    active_reason = Column(String(250), nullable=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime, nullable=True)
    stationary_box = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), unique=False, nullable=True)
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
            "active_reason": self.active_reason,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "stationary_box": to_shape(self.stationary_box).wkt if self.stationary_box else None,
            "user_id": self.user_id,
            "type_id": self.type_id,
        }


class SensorSummaries(Base):
    """SensorSummaries table extends Base class from database.py
    :timestamp (DateTime), primary key
    :geom (Geometry)
    :measurement_count (Integer)
    :measurement_data (JSON)
    :stationary (Boolean)
    :sensor_id (Integer), foreign key"""

    __tablename__ = "SensorSummaries"
    timestamp = Column(Integer, primary_key=True, nullable=False)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), unique=False, nullable=True)  # TODO check if spatial index is needed for alembic
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
