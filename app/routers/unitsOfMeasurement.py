# dependancies:
import datetime as dt
from enum import Enum

from core.authentication import AuthHandler
from core.models import UnitsOfMeasurement as ModelUnitsOfMeasurement
from core.schema import UnitsOfMeasurement as SchemaUnitsOfMeasurement
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

unitsOfMeasurementRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@unitsOfMeasurementRouter.post("", response_model=SchemaUnitsOfMeasurement, status_code=status.HTTP_201_CREATED)
async def add_unit_of_measurement(
    unit_of_measurement: SchemaUnitsOfMeasurement,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Add a new unit of measurement to the database.
    Args:
        unit_of_measurement (SchemaUnitsOfMeasurement): The unit of measurement to add.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        SchemaUnitsOfMeasurement: The added unit of measurement.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_add(ModelUnitsOfMeasurement, unit_of_measurement.dict())


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@unitsOfMeasurementRouter.get("", response_model=list[SchemaUnitsOfMeasurement], status_code=status.HTTP_200_OK)
async def get_units_of_measurement():
    """
    Retrieve a list of all the units of measurement in the database.
    Returns:
        List[SchemaUnitsOfMeasurement]: A list of units of measurement.
    """
    return CRUD().db_get_with_model(ModelUnitsOfMeasurement)


##################################################################################################################################
#                                                  Update                                                                        #
##################################################################################################################################
@unitsOfMeasurementRouter.put("/{unit_of_measurement_name}", response_model=SchemaUnitsOfMeasurement, status_code=status.HTTP_200_OK)
async def update_unit_of_measurement(
    unit_of_measurement_name: str,
    unit_of_measurement: SchemaUnitsOfMeasurement,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Update an existing unit of measurement in the database.
    Args:
        unit_of_measurement_name (str): The name of the unit of measurement to update.
        unit_of_measurement (SchemaUnitsOfMeasurement): The updated unit of measurement data.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        SchemaUnitsOfMeasurement: The updated unit of measurement.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelUnitsOfMeasurement, [ModelUnitsOfMeasurement.name == unit_of_measurement_name], unit_of_measurement.dict())


##################################################################################################################################
#                                                  Delete                                                                        #
##################################################################################################################################
@unitsOfMeasurementRouter.delete("/{unit_of_measurement_name}", status_code=status.HTTP_200_OK)
def delete_unit_of_measurement(unit_of_measurement_name: str, payload=Depends(auth_handler.auth_wrapper)):
    """
    Delete a unit of measurement from the database.
    Args:
        unit_of_measurement_name (str): The name of the unit of measurement to delete.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        None
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelUnitsOfMeasurement, [ModelUnitsOfMeasurement.name == unit_of_measurement_name])
