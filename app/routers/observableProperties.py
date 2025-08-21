# dependancies:
from core.authentication import AuthHandler
from core.models import ObservableProperties as ModelObservableProperties
from core.schema import ObservableProperties as SchemaObservableProperties
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

observablePropertiesRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@observablePropertiesRouter.post("", response_model=SchemaObservableProperties, status_code=status.HTTP_201_CREATED)
async def add_observable_property(
    observable_property: SchemaObservableProperties,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Add a new observable property to the database.
    Args:
        observable_property (SchemaObservableProperties): The observable property to add.
        payload (Depends): Dependency to check user authentication and role.

    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_add(observable_property, observable_property.dict())


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@observablePropertiesRouter.get("", response_model=list[SchemaObservableProperties], status_code=status.HTTP_200_OK)
async def get_observable_properties():
    """
    Retrieve a list of all the observable properties in the database.
    Args:
        name (str | None): Optional filter by observable property name.
        payload (Depends): Dependency to check user authentication and role.

    Returns:
        List[SchemaObservableProperties]: A list of observable properties.
    """

    return CRUD().db_get_with_model(ModelObservableProperties)


##################################################################################################################################
#                                                  Update                                                                        #
##################################################################################################################################
@observablePropertiesRouter.put("/{observable_property_name}", response_model=SchemaObservableProperties, status_code=status.HTTP_200_OK)
async def update_observable_property(
    observable_property_name: str,
    observable_property: SchemaObservableProperties,
    payload=Depends(auth_handler.auth_wrapper),
):
    """
    Update an existing observable property in the database.
    Args:
        observable_property_name (str): The name of the observable property to update.
        observable_property (SchemaObservableProperties): The updated observable property data.
        payload (Depends): Dependency to check user authentication and role.
    Returns:
        SchemaObservableProperties: The updated observable property.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelObservableProperties, [observable_property["name"] == observable_property_name], observable_property.dict())


##################################################################################################################################
#                                                  Delete                                                                        #
##################################################################################################################################
@observablePropertiesRouter.delete("/{observable_property_name}", status_code=status.HTTP_200_OK)
def delete_observable_property(observable_property_name: str, payload=Depends(auth_handler.auth_wrapper)):
    """
    Delete an observable property from the database.
    Args:
        observable_property_name (str): The name of the observable property to delete.
        payload (Depends): Dependency to check user authentication and role.
    Returns:
        Response: HTTP response indicating success or failure.
    """
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelObservableProperties, [ModelObservableProperties.name == observable_property_name])
