# from sqlalchemy.ext.declarative import declarative_base
from db.database import Base
from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# TODO avoid names with '_'


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
    type_id = Column(Integer, ForeignKey("SensorTypes.id"), nullable=False)

    sensorTypeFK = relationship("SensorTypes")


class SensorSummaries(Base):

    __tablename__ = "SensorSummaries"

    timestamp = Column(Integer, primary_key=True, nullable=False)
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326), unique=False, nullable=True
    )  # here your Geometry column
    measurement_count = Column(Integer, nullable=False)
    measurement_data = Column(JSON, nullable=False)
    sensor_id = Column(Integer, ForeignKey("Sensors.id"), primary_key=True, nullable=False)

    # relationship to sensors table
    SensorId_fk = relationship("Sensors")


# class Book(Base):
#     __tablename__ = "book"
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     rating = Column(Integer)
#     time_created = Column(DateTime(timezone=True), server_default=func.now())
#     time_updated = Column(DateTime(timezone=True), onupdate=func.now())
#     author_id = Column(Integer, ForeignKey("author.id"))

#     author = relationship("Author")


# class Author(Base):
#     __tablename__ = "author"
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     age = Column(Integer)
#     time_created = Column(DateTime(timezone=True), server_default=func.now())
#     time_updated = Column(DateTime(timezone=True), onupdate=func.now())
