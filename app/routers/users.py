# dependancies:
import datetime as dt
from os import environ as env

from core.auth import AuthHandler
from core.models import Users as ModelUser
from core.schema import User as SchemaUser
from db.database import SessionLocal
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

from routers.helpers.authSharedFunctions import checkRoleAboveUser, checkRoleAdmin

usersRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()

load_dotenv()

#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@usersRouter.get("/read")
def get_user(payload=Depends(auth_handler.auth_wrapper)):

    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        result = db.query(ModelUser).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve user")
    return result


@usersRouter.get("/read/{uid}")
def get_user_from_uid(uid: str, payload=Depends(auth_handler.auth_wrapper)):

    if checkRoleAboveUser(uid) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        result = db.query(ModelUser).filter(ModelUser.uid == uid).first()

        # only allow read if user is admin or the user is reading their own data
        if checkRoleAdmin(payload) == False:
            if result.uid != payload["sub"]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve user")

    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@usersRouter.put("/update/{uid}")
def update_user(uid: str, user: SchemaUser, payload=Depends(auth_handler.auth_wrapper)):

    # only allow update if user is admin or the user is reading their own data
    if checkRoleAdmin(payload) == False:
        if uid != payload["sub"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
        else:
            if user.role == "admin":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized to promote a user to admin"
                )
    try:
        db.query(ModelUser).filter(ModelUser.uid == uid).update(user.dict())
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return user


#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@usersRouter.delete("/delete/{uid}")
def delete_user(uid: str, payload=Depends(auth_handler.auth_wrapper)):

    # only allow delete if user is admin or the user is deleting their own data
    if checkRoleAdmin(payload) == False:
        if uid != payload["sub"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        user_deleted = db.query(ModelUser).filter(ModelUser.uid == uid).first()
        db.delete(user_deleted)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User could not be deleted")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete user")

    return user_deleted
