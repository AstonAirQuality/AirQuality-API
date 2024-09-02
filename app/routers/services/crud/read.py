from core.models import Users as ModelUser
from fastapi import HTTPException, status
from routers.services.crud.abstractCRUD import abstractbaseCRUD
from routers.services.formatting import convertWKBtoWKT


class Read(abstractbaseCRUD):
    def __init__(self) -> None:
        super().__init__()

    def db_get_with_model(self, model: any, order_columns: bool = True, filter_expressions: list = None, first: bool = False, page: int = None, limit: int = None):
        """Get all rows from the database
        :param model: model to query
        :filter_expressions: filter expressions
        :param first: return only the first row or all rows
        :param page: page number (optional)
        :param limit: number of rows per page (optional)
        :return: all rows"""

        try:
            query = self.db.query(model)
            if filter_expressions is not None:
                query = query.filter(*filter_expressions)
            if first:
                result = query.first()
            elif page is not None and limit is not None:
                result = query.offset((page - 1) * limit).limit(limit).all()
            else:
                result = query.all()

            if order_columns:
                result = self.order_columns(model, result)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return result

    def db_get_from_column(self, model: any, column: str, searchvalue: str):
        """Get all rows from the database
        :param model: model to query
        :return: all rows"""
        try:
            result = self.order_columns(model, self.db.query(model).filter(getattr(model, column).like(f"%{searchvalue}%")).all())
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return result

    def db_get_by_id(self, model: any, id: int):
        """Get row from the database by id
        :param id: id of the row
        :return: row"""
        try:
            result = self.db.query(model).filter(model.id == id).first()
        except Exception as e:
            print(e)
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve row")
        return result

    def db_get_fields_using_filter_expression(
        self, filter_expressions: list = None, fields: list = None, model: any = None, join_models: list = None, first: bool = False, page: int = None, limit: int = None
    ):
        """Get rows from the database with joins and custom fields
        :param filter_expressions: filter expressions
        :param fields: fields to return
        :param model: model to query
        :param join_models: models to join
        :param first: return only the first row or all rows
        :param page: page number (optional)
        :param limit: number of rows per page (optional)
        :return: rows"""
        try:
            query = self.db.query(*fields)
            if model is not None and join_models is not None:
                query = query.select_from(model).join(*join_models, isouter=True)
            if filter_expressions is not None:
                query = query.filter(*filter_expressions)
            if first:
                result = query.first()
            elif page is not None and limit is not None:
                result = query.offset((page - 1) * limit).limit(limit).all()
            else:
                result = query.all()
        except Exception as e:
            self.db.rollback()
            print(e)
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
        return self.db_get_fields_using_filter_expression(filter_expressions=[ModelUser.uid == uid], fields=[ModelUser.role, ModelUser.username], first=True)
