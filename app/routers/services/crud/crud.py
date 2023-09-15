from routers.services.crud.create import Create
from routers.services.crud.delete import Delete
from routers.services.crud.read import Read
from routers.services.crud.update import Update


class CRUD(Create, Read, Update, Delete):
    def __init__(self) -> None:
        super().__init__()
