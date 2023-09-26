from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation
from routers.services.crud.abstractCRUD import abstractbaseCRUD

# error handling
from sqlalchemy.exc import IntegrityError


class Create(abstractbaseCRUD):
    def __init__(self) -> None:
        super().__init__()

    def db_add(self, model: any, data: dict):
        """Add a new row to the database
        :param model: database model
        :param data: data to add to the database
        :return: newly added row"""
        try:
            self.db.add(model(**data))
            self.db.commit()
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                self.db.rollback()
                print(str(e.orig).split("DETAIL:")[1])
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
            else:
                raise Exception(e)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return data
