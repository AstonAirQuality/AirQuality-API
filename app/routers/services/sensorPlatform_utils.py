import datetime as dt

from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorTypes
from fastapi import HTTPException, Query, status
from routers.services.crud.crud import CRUD
from routers.services.enums import ActiveReason
from routers.services.formatting import convertWKBtoWKT


def get_sensor_dict(active_only: bool, idtype: str, ids: list[int] = Query(default=[])) -> tuple[list[dict], list[dict]]:
    """Get all sensors data scraping information from the database. Flag sensors that have not been updated in over 90 days

    Args:
        active_only (bool): If True, only return active sensors.
        idtype (str): Type of id. Can be sensor_id or sensor_type_id.
        ids (list[int], optional): List of sensor ids or sensor type ids. Defaults to [].
    Returns:
        tuple: A tuple containing a list of sensors and a list of flagged sensors.
    """
    try:
        fields = [
            ModelSensor.id,
            ModelSensorTypes.name.label("type_name"),
            ModelSensor.lookup_id.label("lookup_id"),
            ModelSensor.stationary_box.label("stationary_box"),
            ModelSensor.time_updated.label("time_updated"),
        ]

        filter_expressions = []
        if idtype == "sensor_type_id" and active_only:
            filter_expressions = [ModelSensor.active == active_only, ModelSensor.type_id.in_(ids)]
        elif idtype == "sensor_type_id" and not active_only:
            filter_expressions = [ModelSensor.type_id.in_(ids)]
        elif idtype == "sensor_id":
            filter_expressions = [ModelSensor.id.in_(ids)]
        result = CRUD().db_get_fields_using_filter_expression(filter_expressions, fields, ModelSensor, [ModelSensorTypes], first=False)

        # The query returns geometry as a WKB. We must convert to WKT string
        results = []
        flagged_sensors = []
        for row in result:
            row_as_dict = dict(row._mapping)
            # if looking for active only and the sensor has been not been updated in over 90 days then include it in the flagged sensors list
            if active_only and row_as_dict["time_updated"] is not None and (dt.datetime.today() - row_as_dict["time_updated"]).days > 90:
                serial_number = CRUD().db_get_fields_using_filter_expression([ModelSensor.id == row_as_dict["id"]], [ModelSensor.serial_number], first=True)[0]
                # do not include the sensor in the data scraping list if it has been flagged as inactive
                flagged_sensors.append({"id": row_as_dict["id"], "serial_number": serial_number})
                continue

            row_as_dict["stationary_box"] = convertWKBtoWKT(row_as_dict["stationary_box"])
            results.append(row_as_dict)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return (results, flagged_sensors)


# def get_sensor_type_from_sensor_id(sensor_id: int) -> str:
#     """Get the sensor type name from the sensor id
#     :param sensor_id: sensor id
#     :return: sensor type name"""
#     try:
#         sensor_type = CRUD().db_get_fields_using_filter_expression([ModelSensor.id == sensor_id], [ModelSensorTypes.name], ModelSensor, [ModelSensorTypes], first=True)
#         return sensor_type[0]
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# used by background tasks
def get_sensor_id_and_serialnum_from_lookup_id(lookup_id: str):
    """Get the sensor id and serial number from the lookup id
    :param lookup_id: lookup id of the sensor
    :return: tuple (sensor id and serial number)"""
    return CRUD().db_get_fields_using_filter_expression([ModelSensor.lookup_id == lookup_id], [ModelSensor.id.label("id"), ModelSensor.serial_number.label("serial_number")], ModelSensor, first=True)


# used by background tasks
def set_last_updated(sensor_id: int, timestamp: int):
    """Sets all sensors last updated field whose id matches to sensor_id
    :param sensor_id: sensor id
    :param timestamp: timestamp to set last updated to"""
    CRUD().db_update(ModelSensor, [ModelSensor.id == sensor_id], {ModelSensor.time_updated: dt.datetime.fromtimestamp(timestamp)})


# used by background tasks
def deactivate_unsynced_sensor(sensor_id: int):
    """Deactivate a sensor if it has not been updated in over 90 days
    :param sensor_id: sensor id
    """
    CRUD().db_update(ModelSensor, [ModelSensor.id == sensor_id], {ModelSensor.active: False, ModelSensor.active_reason: ActiveReason.NO_DATA.value})


def get_lookupids_of_sensors(active_only: bool, ids: list[int], idtype: str) -> tuple[dict[str, dict[str, dict[str, str]]]]:
    """
    Get all active sensors data scraping information from the database and the flagged sensors that have not been updated in over 90 days

    Args:
        active_only (bool): If True, only return active sensors.
        idtype (str): Type of id. Can be sensor_id or sensor_type_id.
        ids (list[int], optional): List of sensor ids or sensor type ids. Defaults to [].
    Returns:
        tuple: A tuple containing a dictionary of sensors grouped by sensor type, where each sensor type maps to a dictionary of sensor lookup_ids and their data.
        [sensor_type_name][lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}

    """
    sensors, flagged_sensors = get_sensor_dict(active_only, idtype, ids)

    # group sensors by type into a new nested dictionary dict[sensor_type][lookup_id] = {"stationary_box": stationary_box, "time_updated": time_updated}
    sensor_dict = {}
    for data in sensors:
        if data["type_name"] in sensor_dict:
            sensor_dict[data["type_name"]][str(data["lookup_id"])] = {"stationary_box": data["stationary_box"], "time_updated": data["time_updated"]}
        else:
            sensor_dict[data["type_name"]] = {str(data["lookup_id"]): {"stationary_box": data["stationary_box"], "time_updated": data["time_updated"]}}

        # if this is a user data ingestion task then we need to remove the time_updated field
        if idtype == "sensor_id":
            del sensor_dict[data["type_name"]][str(data["lookup_id"])]["time_updated"]

    return sensor_dict, flagged_sensors
