# # dependancies:
from os import environ as env

from config.firebaseConfig import PyreBaseAuth, delete_user
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


#################################################################################################################################
#                                                  Dev only                                                                     #
#################################################################################################################################
# dev routes only
if env["PRODUCTION_MODE"] != "TRUE":

    @authRouter.get("/dev-login")
    async def dev_login(uid: str, role: str):
        try:
            return auth_handler.dev_encode_token(uid, role)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
