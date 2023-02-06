import datetime as dt

from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorTypes
from db.database import SessionLocal
from fastapi import HTTPException, Query, status
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT

db = SessionLocal()


def get_sensor_dict(idtype: str, ids: list[int] = Query(default=[])):
    """Get all active sensors data scraping information from the database
    :param type_ids: list of sensor type ids to filter by
    :return: list of sensor data scraping information"""
    try:
        query = db.query(
            ModelSensorTypes.name.label("type_name"),
            ModelSensor.lookup_id.label("lookup_id"),
            ModelSensor.stationary_box.label("stationary_box"),
        ).join(ModelSensorTypes, isouter=True)

        if idtype == "sensor_type_id":
            query = query.filter(ModelSensor.active == True, ModelSensor.type_id.in_(ids))
        elif idtype == "sensor_id":
            query = query.filter(ModelSensor.id.in_(ids))
        result = query.all()

        # because the query returned row type we must convert wkb to wkt string to be be api friendly
        results = []
        for row in result:
            row_as_dict = dict(row._mapping)
            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            results.append(row_as_dict)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return results


# # used by background tasks
# def get_active_sensor_dict_from_type_id(type_ids: list[int] = Query(default=[])):
#     """Get all active sensors data scraping information from the database
#     :param type_ids: list of sensor type ids to filter by
#     :return: list of sensor data scraping information"""
#     try:
#         result = (
#             db.query(
#                 ModelSensorTypes.name.label("type_name"),
#                 ModelSensor.lookup_id.label("lookup_id"),
#                 ModelSensor.stationary_box.label("stationary_box"),
#             )
#             .filter(ModelSensor.active == True, ModelSensor.type_id.in_(type_ids))
#             .join(ModelSensorTypes, isouter=True)
#             .all()
#         )
#         # because the query returned row type we must convert wkb to wkt string to be be api friendly
#         results = []
#         for row in result:
#             row_as_dict = dict(row._mapping)
#             row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
#             results.append(row_as_dict)

#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#     return results


# # used by background tasks
# def get_sensor_dict_from_id(sensor_ids: list[int] = Query(default=[])):
#     """Get all active sensors data scraping information from the database
#     :param type_ids: list of sensor type ids to filter by
#     :return: list of sensor data scraping information"""
#     try:
#         result = (
#             db.query(
#                 ModelSensorTypes.name.label("type_name"),
#                 ModelSensor.lookup_id.label("lookup_id"),
#                 ModelSensor.stationary_box.label("stationary_box"),
#             )
#             .filter(ModelSensor.id.in_(sensor_ids))
#             .join(ModelSensorTypes, isouter=True)
#             .all()
#         )
#         # because the query returned row type we must convert wkb to wkt string to be be api friendly
#         results = []
#         for row in result:
#             row_as_dict = dict(row._mapping)
#             row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
#             results.append(row_as_dict)

#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#     return results


# used by background tasks
def get_sensor_id_and_serialnum_from_lookup_id(lookup_id: str):
    """Get the sensor id and serial number from the lookup id
    :param lookup_id: lookup id of the sensor
    :return: tuple (sensor id and serial number)"""
    try:
        result = db.query(ModelSensor.id.label("id"), ModelSensor.serial_number.label("serial_number")).filter(ModelSensor.lookup_id == lookup_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return result


# used by background tasks
def set_last_updated(sensor_id: int, timestamp: int):
    """Sets all sensors last updated field whose id matches to sensor_id
    :param sensor_id: sensor id
    :param timestamp: timestamp to set last updated to
    :return: dict of sensor id and last updated"""
    try:
        db.query(ModelSensor).filter(ModelSensor.id == sensor_id).update({ModelSensor.time_updated: dt.datetime.fromtimestamp(timestamp)})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {sensor_id: timestamp}
