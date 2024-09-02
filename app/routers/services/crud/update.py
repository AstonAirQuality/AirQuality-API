from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation
from routers.services.crud.abstractCRUD import abstractbaseCRUD

# error handling
from sqlalchemy.exc import IntegrityError


class Update(abstractbaseCRUD):
    def __init__(self) -> None:
        super().__init__()

    def db_update(self, model: any, filter_expressions: any, data: dict):
        """Update a row in the database
        :param model: model to update
        :param filter_expressions: filter expressions
        :param data: data to update
        :return: updated row"""

        try:
            self.db.query(model).filter(*filter_expressions).update(data)
            self.db.commit()
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                self.db.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
            else:
                raise Exception(e)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return data
