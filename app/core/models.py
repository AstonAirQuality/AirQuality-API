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


class SensorPlatformTypes(Base):
    """SensorTypes table extends Base class from database.py
    :id (Integer), primary key
    :sensortype_name (String),
    :description (String)
    :sensor_metadata (JSON) - to be a csvw
    """

    __tablename__ = "SensorPlatformTypes"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(), nullable=False)
    sensor_metadata = Column(JSON, nullable=False)  # to be a csvw

    def columns_iter():
        for c in SensorPlatformTypes.__getattribute__("__table__").columns:
            yield c.name


class SensorPlatforms(Base):
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

    __tablename__ = "SensorPlatforms"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    lookup_id = Column(String(50), nullable=True)
    serial_number = Column(String(50), unique=True)
    active = Column(Boolean, nullable=False)
    active_reason = Column(String(250), nullable=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime, nullable=True)
    stationary_box = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), unique=False, nullable=True)
    user_id = Column(String(50), ForeignKey("Users.uid"), nullable=True)
    type_id = Column(Integer, ForeignKey("SensorPlatformTypes.id"), nullable=False)

    sensorTypeFK = relationship("SensorPlatformTypes")
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
    sensor_id = Column(Integer, ForeignKey("SensorPlatforms.id"), primary_key=True, nullable=False)

    # relationship to sensors table
    SensorId_fk = relationship("SensorPlatforms")

    def to_json(self):
        return {
            "timestamp": self.timestamp,
            "geom": to_shape(self.geom).wkt if self.geom else None,
            "measurement_count": self.measurement_count,
            "measurement_data": self.measurement_data,
            "stationary": self.stationary,
            "sensor_id": self.sensor_id,
        }


class SensorPlatformTypeConfig(Base):
    """SensorPlatformTypeConfig table extends Base class from database.py
    stores configuration for generic sensor platform types
    Args:
        sensor_type_id (Integer): foreign key to SensorPlatformTypes table
        authentication_url (String): URL for authentication
        authentication_method (JSON): JSON object containing authentication method details
        api_url (String): URL for the API endpoint for fetching sensor data of the platform type
        api_method (JSON): HTTP method for the API (GET, POST, etc. and its headers)
        sensor_mappings (JSON): JSON object mapping sensor data fields to database columns
    """

    __tablename__ = "SensorPlatformTypeConfig"
    sensor_type_id = Column(Integer, ForeignKey("SensorPlatformTypes.id"), primary_key=True, nullable=False)
    authentication_url = Column(String(), nullable=True)
    authentication_method = Column(JSON, nullable=True)
    api_url = Column(String(), nullable=False)
    api_method = Column(JSON, nullable=False)
    sensor_mappings = Column(JSON, nullable=False)

    SensorTypeFK = relationship("SensorPlatformTypes")


class ObservableProperties(Base):
    """ObservableProperties table extends Base class from database.py
    :id (Integer), primary key
    :name (String), unique
    :description (String)
    :url (String)
    :datatype (String): data type of the observable property (e.g. int, float, str)
    """

    __tablename__ = "ObservableProperties"
    name = Column(String(), primary_key=True, index=True, nullable=False)
    description = Column(String(), nullable=True)
    url = Column(String(), nullable=False)
    datatype = Column(String(), nullable=False)

    def columns_iter():
        for c in ObservableProperties.__getattribute__("__table__").columns:
            yield c.name


class UnitsOfMeasurement(Base):
    """UnitsOfMeasurement table extends Base class from database.py

    Args:
        id (Integer): primary key
        name (String): unique name of the unit
        url (String): URL for the unit of measurement
        symbol (String): symbol representing the unit of measurement
    """

    __tablename__ = "UnitsOfMeasurement"
    name = Column(String(), primary_key=True, unique=True, nullable=False)
    url = Column(String(), nullable=False)
    symbol = Column(String(), nullable=False)

    def columns_iter():
        for c in UnitsOfMeasurement.__getattribute__("__table__").columns:
            yield c.name
