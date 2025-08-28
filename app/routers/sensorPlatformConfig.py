# dependancies:
import datetime as dt
from enum import Enum

from core.authentication import AuthHandler
from core.models import SensorPlatformTypeConfig as ModelSensorPlatformPlatformConfig
from core.schema import SensorTypeConfig as SchemaSensorPlatformConfig
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

sensorPlatformConfig = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@sensorPlatformConfig.post("", response_model=SchemaSensorPlatformConfig, status_code=status.HTTP_201_CREATED)
async def add_sensor_platform_config(
    sensor_platform_config: SchemaSensorPlatformConfig,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Add a new sensor platform configuration.
    Args:
        sensor_platform_config (SchemaSensorPlatformConfig): The sensor platform configuration to add.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        SchemaSensorPlatformConfig: The added sensor platform configuration.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_add(ModelSensorPlatformPlatformConfig, sensor_platform_config.dict())


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@sensorPlatformConfig.get("", response_model=list[SchemaSensorPlatformConfig], status_code=status.HTTP_200_OK)
async def get_sensor_platform_configs(payload=Depends(auth_handler.auth_wrapper)):
    """
    Retrieve a list of all sensor platform configurations.
    Returns:
        List[SchemaSensorPlatformConfig]: A list of sensor platform configurations.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    return CRUD().db_get_with_model(ModelSensorPlatformPlatformConfig)


##################################################################################################################################
#                                                  Update                                                                        #
##################################################################################################################################
@sensorPlatformConfig.put("/{sensor_platform_type}", response_model=SchemaSensorPlatformConfig, status_code=status.HTTP_200_OK)
async def update_sensor_platform_config(
    sensor_platform_type: int,
    sensor_platform_config: SchemaSensorPlatformConfig,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Update an existing sensor platform configuration.
    Args:
        sensor_platform_type (int): The ID of the sensor platform type to update.
        sensor_platform_config (SchemaSensorPlatformConfig): The updated sensor platform configuration.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        SchemaSensorPlatformConfig: The updated sensor platform configuration.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelSensorPlatformPlatformConfig, [ModelSensorPlatformPlatformConfig.sensor_type_id == sensor_platform_type], sensor_platform_config.dict())


##################################################################################################################################
#                                                  Delete                                                                        #
##################################################################################################################################
@sensorPlatformConfig.delete("/{sensor_platform_type}", status_code=status.HTTP_200_OK)
async def delete_sensor_platform_config(
    sensor_platform_type: int,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Delete a sensor platform configuration.
    Args:
        sensor_platform_type (int): The ID of the sensor platform type to delete.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        None
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelSensorPlatformPlatformConfig, [ModelSensorPlatformPlatformConfig.sensor_type_id == sensor_platform_type])
