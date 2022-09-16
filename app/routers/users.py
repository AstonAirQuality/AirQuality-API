# dependancies:
import datetime as dt
from os import environ as env

from api_wrappers.scraperWrapper import ScraperWrapper
from core.models import Users as ModelUser
from core.schema import User as SchemaUser
from db.database import SessionLocal
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

usersRouter = APIRouter()

db = SessionLocal()

load_dotenv()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
@usersRouter.post("/create", response_model=SchemaUser)  # TODO delete route, keep function
def add_user(user: SchemaUser):
    try:
        user = ModelUser(username=user.username, email=user.email)
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return user


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@usersRouter.get("/read")
def get_user():
    try:
        result = db.query(ModelUser).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve user")
    return result


@usersRouter.get("/read/{user_id}")
def get_user(user_id: str):
    try:
        result = db.query(ModelUser).filter(ModelUser.id == user_id).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve user")

    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################

#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@usersRouter.delete("/delete/{user_id}")
def delete_user(user_id: str):
    try:
        user_deleted = db.query(ModelUser).filter(ModelUser.id == user_id).first()
        db.delete(user_deleted)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User could not be deleted")

    return user_deleted
