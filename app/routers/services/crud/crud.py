from enum import Enum

from routers.services.crud.create import Create
from routers.services.crud.delete import Delete
from routers.services.crud.read import Read
from routers.services.crud.update import Update


class ActiveReason(str, Enum):
    """Enum for the reason a sensor was activated or deactivated"""

    NO_DATA = "DEACTIVATED_NO_DATA"
    ACTIVE_BY_USER = "ACTIVATED_BY_USER"
    DEACTVATE_BY_USER = "DEACTIVATED_BY_USER"
    REMOVED = "REMOVED_FROM_SENSOR_FLEET"


class CRUD(Create, Read, Update, Delete):
    def __init__(self) -> None:
        super().__init__()
