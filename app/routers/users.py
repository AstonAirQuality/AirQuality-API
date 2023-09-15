# dependancies:
import datetime as dt
from os import environ as env

from core.authentication import AuthHandler
from core.models import Users as ModelUser
from core.schema import User as SchemaUser
from db.database import SessionLocal
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, status
from routers.services.crud.crud import CRUD
from routers.services.enums import userColumns

# error handling
from sqlalchemy.exc import IntegrityError

usersRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()

load_dotenv()

#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@usersRouter.get("")
def get_users(payload=Depends(auth_handler.auth_wrapper)):
    """read all users and return a json of users
    \n:return: users"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_get_all(ModelUser)


@usersRouter.get("/read-from/{column}")
def get_user_from_column(column: userColumns,searchvalue: str, payload=Depends(auth_handler.auth_wrapper)):
    """query/read a user from searchvalue  and column name and return a json of the first user
    \n :param column: column to apply the filter on (uid, email, username)
    \n :param searchvalue : user searchvalue
    \n:return: user"""

    # only allow read if user is admin or the user is reading their own data
    if auth_handler.checkRoleAdmin(payload) == False:
        if column == "uid" and searchvalue != payload["sub"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Not authorized")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Not authorized")

    return CRUD().db_get_from_column(ModelUser, column, searchvalue)


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
@usersRouter.put("/{uid}")
def update_user(uid: str, user: SchemaUser, payload=Depends(auth_handler.auth_wrapper)):
    """update a user using the user schema and uid
    \n :param uid: user uid
    \n :param user: user schema
    \n:return: user"""

    updated_user = user.dict()

    if updated_user["role"] not in auth_handler.valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Valid roles are: {auth_handler.valid_roles}")

    if auth_handler.checkRoleAdmin(payload) == False:
        if uid != payload["sub"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized to update another user")
        else:
            # if user is not admin, then remove the role from the user object. This will prevent the user from updating their own role
            updated_user.pop("role", None)

    return CRUD().db_update(ModelUser, ModelUser.uid == uid, updated_user)


@usersRouter.patch("/{uid}/{role}")
def update_user_role(uid: str, role: str, payload=Depends(auth_handler.auth_wrapper)):
    """update a user using the user schema and uid
    \n :param uid: user uid
    \n :param role: user role
    \n:return: user"""

    # only allow update if user is admin only
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_update(ModelUser, ModelUser.uid == uid, {"role": role})

#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@usersRouter.delete("/{uid}")
def delete_user(uid: str, payload=Depends(auth_handler.auth_wrapper)):
    """delete a user using the uid
    \n :param uid: user uid
    \n:return: user"""

    # only allow delete if user is admin or the user is deleting their own data
    if auth_handler.checkRoleAdmin(payload) == False:
        if uid != payload["sub"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    return CRUD().db_delete(ModelUser, ModelUser.uid == uid)
