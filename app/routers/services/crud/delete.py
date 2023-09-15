from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation
from routers.services.crud.abstractCRUD import abstractbaseCRUD

# error handling
from sqlalchemy.exc import IntegrityError


class Delete(abstractbaseCRUD):
    def __init__(self) -> None:
        super().__init__()

    def db_delete(self, model: any, filter_expression: any):
        """Delete a row in the database
        :param model: model to delete
        :param filter_expression: filter expression
        :return: deleted row"""

        try:
            self.db.query(model).filter(filter_expression).delete()
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not delete row. Integrity error")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return True
