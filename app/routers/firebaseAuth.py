# # dependancies:
import email
from os import environ as env
from types import NoneType

from config.firebaseConfig import PyreBaseAuth  # TODO remove this dependancy
from core.auth import AuthHandler
from core.schema import User as SchemaUser
from fastapi import APIRouter, Depends, Header, HTTPException, status

from routers.helpers.usersSharedFunctions import add_user

authRouter = APIRouter()
auth_handler = AuthHandler()

# # notes
# """
# signup and login occurs in the frontend then the uid is passed to the backend
# with the uid the backend will set the custom claims and send the token back to the frontend
# the frontend will then store the token in local storage
# the frontend will then send the token with every request
# the backend will then verify the token and check the custom claims
# """

"""
signup and login occurs in the frontend then the jwt token from firebase is passed to the backend
verify the jwt token is signed by google and extract the uid
generate a custom jwt token with the uid and custom claims (role)
send the custom jwt token back to the frontend
the frontend will then store the token in local storage
the frontend will then send the token with every request
the backend will then verify the token and check the custom claims
"""


@authRouter.get("/signup")
async def signup(token=Header(default=None)):
    try:
        decoded_jwt = auth_handler.verify_firebase_token(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # TODO add username extraction from firebase token
    username = None
    try:
        user = SchemaUser(uid=decoded_jwt["sub"], email=decoded_jwt["email"], username=username, role="user")
        add_user(user)
    except HTTPException as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")

    # login the user
    return login(token)


@authRouter.get("/login")
async def login(token=Header(default=None)):
    try:
        access_token = auth_handler.encode_token(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # login the user
    return {"access_token": access_token}


@authRouter.get("/protected-route-test")
async def protected_route_test(payload=Depends(auth_handler.auth_wrapper)):
    # from enum import Enum
    # Numbers = Enum(ONE=1, TWO=2, THREE='three')
    if payload["role"] == "admin":
        return {"message": "Hello admin"}
    elif payload["role"] == "user":
        return {"message": "Hello user"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role")


#################################################################################################################################
#                                                  Dev only                                                                     #
#################################################################################################################################

# dev routes only
if env["PRODUCTION_MODE"] != "TRUE":

    @authRouter.post("/custom-token/{idToken}")
    async def custom_token(idToken: str):

        decoded_jwt = auth_handler.verify_firebase_token(idToken)

        payload = {"role": "admin"}

        token = PyreBaseAuth.create_custom_token(decoded_jwt["sub"], payload)
        return {"token": token}

    # @authRouter.delete("/delete-user-from-firebase/{uid}")
    # async def delete_firebase_user(idToken: str):
    #     user = PyreBaseAuth.delete_user(idToken)
    #     return user

    @authRouter.post("/create-user-in-firebase")
    async def create_firebase_user(email: str, password: str):
        user = PyreBaseAuth.create_user_with_email_and_password(email, password)
        return user

    @authRouter.get("/firebase-token")
    async def login_firebase_token(email: str, password: str):
        try:
            user = PyreBaseAuth.sign_in_with_email_and_password(email, password)
            return user["idToken"]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    @authRouter.get("/dev-login")
    async def dev_login(uid: str, role: str):
        try:
            return auth_handler.dev_encode_token(uid, role)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    @authRouter.get("/login-firebase")
    async def login_firebase(email: str, password: str):
        try:
            user = PyreBaseAuth.sign_in_with_email_and_password(email, password)
            return auth_handler.encode_token(user["idToken"])
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
