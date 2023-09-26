from routers.services.crud.create import Create
from routers.services.crud.delete import Delete
from routers.services.crud.read import Read
from routers.services.crud.update import Update


class CRUD(Create, Read, Update, Delete):
    _instance = None

    # Singleton pattern
    def __new__(cls):
        if cls._instance is None:
            print("Creating the object")
            cls._instance = super(CRUD, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    def clear_db_session(self):
        self.db.close()
