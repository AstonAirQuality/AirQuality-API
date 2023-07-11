import datetime as dt

from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorTypes
from db.database import SessionLocal
from fastapi import HTTPException, Query, status
from routers.helpers.spatialSharedFunctions import convertWKBtoWKT
from routers.sensors import ActiveReason

db = SessionLocal()


def get_sensor_dict(idtype: str, ids: list[int] = Query(default=[])) -> tuple[list[dict], list[dict]]:
    """Get all active sensors data scraping information from the database. Flag sensors that have not been updated in over 90 days
    :param type_ids: list of sensor type ids to filter by
    :return tuple: list of sensor data scraping information and list of flagged sensors"""
    try:
        query = db.query(
            ModelSensor.id,
            ModelSensorTypes.name.label("type_name"),
            ModelSensor.lookup_id.label("lookup_id"),
            ModelSensor.stationary_box.label("stationary_box"),
            ModelSensor.time_updated.label("time_updated"),
        ).join(ModelSensorTypes, isouter=True)

        if idtype == "sensor_type_id":
            query = query.filter(ModelSensor.active == True, ModelSensor.type_id.in_(ids))
        elif idtype == "sensor_id":
            query = query.filter(ModelSensor.id.in_(ids))
        result = query.all()

        # because the query returns bounding box as a wkb we convert it to wkt string
        results = []
        flagged_sensors = []
        for row in result:
            row_as_dict = dict(row._mapping)
            # if the sensor has been not been updated in over 90 days then include it in the flagged sensors list
            if row_as_dict["time_updated"] is not None and (dt.datetime.today() - row_as_dict["time_updated"]).days > 90:
                serial_number = db.query(ModelSensor.serial_number).filter(ModelSensor.id == row_as_dict["id"]).first()[0]
                flagged_sensors.append({"id": row_as_dict["id"], "serial_number": serial_number})
                # do not include the sensor in the data scraping list
                continue

            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            results.append(row_as_dict)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return (results, flagged_sensors)


# used by background tasks
def get_sensor_id_and_serialnum_from_lookup_id(lookup_id: str):
    """Get the sensor id and serial number from the lookup id
    :param lookup_id: lookup id of the sensor
    :return: tuple (sensor id and serial number)"""
    try:
        result = db.query(ModelSensor.id.label("id"), ModelSensor.serial_number.label("serial_number")).filter(ModelSensor.lookup_id == lookup_id).first()
    except Exception as e:
        db.rollback()
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


# used by background tasks
def deactivate_unsynced_sensor(sensor_id: int):
    """Deactivate a sensor if it has not been updated in over 90 days
    :param sensor_id: sensor id
    """
    try:
        db.query(ModelSensor).filter(ModelSensor.id == sensor_id).update({ModelSensor.active: False, ModelSensor.active_reason: ActiveReason.NO_DATA.value})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
