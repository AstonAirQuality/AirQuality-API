from core.models import Users as ModelUser
from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation
from routers.services.crud.abstractCRUD import abstractbaseCRUD
from routers.services.formatting import convertWKBtoWKT

# error handling
from sqlalchemy.exc import IntegrityError


class Read(abstractbaseCRUD):
    def __init__(self) -> None:
        super().__init__()

    def db_get_all(self, model: any):
        """Get all rows from the database
        :param model: model to query
        :return: all rows"""
        try:
            result = self.order_columns(model, self.db.query(model).all())
        except Exception as e:
            self.db.rollback()

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e.orig).split("DETAIL:")[0])
        return result

    def db_get_paginated(self, model: any, page: int, limit: int):
        """Get all rows from the database
        :param page: page number
        :param limit: number of rows per page
        :return: all rows"""
        try:
            result = self.order_columns(model, self.db.query(model).offset((page - 1) * limit).limit(limit).all())
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve all rows")
        return result

    def db_get_by_id(self, model: any, id: int):
        """Get row from the database by id
        :param id: id of the row
        :return: row"""
        try:
            result = self.order_columns(model, self.db.query(model).filter(model.id == id).first())
        except Exception as e:
            print(e)
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve row")
        return result

    def db_get_all_joined(self, model: any, join_models: list, fields: list = None):
        """Get all rows from the database with joins and custom fields
        :param model: model to query
        :param join_models: models to join
        :param fields: fields to return
        :return: all rows"""
        try:
            result = self.db.query(*fields).select_from(model).join(*join_models, isouter=True).all()
        except Exception as e:
            self.db.rollback()
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve all rows")
        return result

    def db_get_all_joined_paginated(self, model: any, join_models: list, fields: list = None, page: int = 1, limit: int = 10):
        """Get all rows from the database with joins and custom fields
        :param model: model to query
        :param join_models: models to join
        :param fields: fields to return
        :return: all rows"""
        try:
            result = self.db.query(*fields).select_from(model).join(*join_models, isouter=True).offset((page - 1) * limit).limit(limit).all()
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve all rows")
        return result

    def order_columns(self, model: any, result: any):
        """Order the columns of the result
        :param model: model to order
        :param result: result to order
        :return: ordered result"""
        column_order = model.__table__.columns.keys()
        row_data = []
        # Process the results
        for row in result:
            if hasattr(row, "stationary_box"):
                setattr(row, "stationary_box", convertWKBtoWKT(getattr(row, "stationary_box")))
            # Access attributes in the order defined by the model's table columns in a dictionary
            row_data.append({column: getattr(row, column) for column in column_order})
        return row_data

    def get_user_token_info(self, uid: str):
        """Get user token info from the database
        :param uid: user id
        :return: tuple of user role and username"""
        try:
            result = self.db.query(ModelUser.role, ModelUser.username).filter(ModelUser.uid == uid).first()
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve user")

        return result
