# # dependancies:
from os import environ as env

from config.firebaseConfig import PyreBaseAuth
from core.authentication import AuthHandler
from core.schema import User as SchemaUser
from fastapi import APIRouter, Header, HTTPException, Query, status

from routers.helpers.usersSharedFunctions import add_user

authRouter = APIRouter()
auth_handler = AuthHandler()


@authRouter.post("/signup")
async def signup(firebase_token=Header(default=None), username: str = Query(None)):
    """sign up a user with firebase token and username
    :param firebase_token: firebase access token
    :param username: username
    :return: dict of user data and custom jwt token"""
    try:
        decoded_jwt = auth_handler.verify_firebase_token(firebase_token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # assign username if it exists in the firebase user record (displayName)
    if username is None:
        try:
            username = decoded_jwt["name"]
        except KeyError:
            pass

    try:
        user = SchemaUser(uid=decoded_jwt["sub"], email=decoded_jwt["email"], username=username, role="user")
        add_user(user)
    except HTTPException as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")

    # TODO use login function to login the user
    (access_token, role, name) = auth_handler.encode_token(firebase_token)
    return {"access_token": access_token, "role": role, "name": name}


@authRouter.post("/login")
async def login(firebase_token=Header(default=None)):
    """login a user with firebase token
    :param firebase_token: firebase access token
    :return: dict of user data and custom jwt token"""

    (access_token, role, name) = auth_handler.encode_token(firebase_token)

    # login the user
    return {"access_token": access_token, "role": role, "name": name}


#################################################################################################################################
#                                                  Firebase                                                                     #
#################################################################################################################################
@authRouter.delete("/delete")
async def delete_user(firebase_token: str):
    """delete a user from firebase
    :param firebase_token: firebase access token
    return: user record from firebase
    """
    jsonResponse = PyreBaseAuth.delete_user(firebase_token)
    return jsonResponse


@authRouter.post("/firebase-login")
async def sign_in_with_firebase(email: str, password: str):
    """sign in with firebase
    :param email: email
    :param password: password
    :return: user record from firebase
    """
    jsonResponse = PyreBaseAuth.sign_in_with_email_and_password(email, password)
    return jsonResponse


@authRouter.post("/firebase-signup")
async def sign_up_with_firebase(email: str, password: str):
    """sign up with firebase
    :param email: email
    :param password: password
    :return: user record from firebase
    """
    jsonResponse = PyreBaseAuth.create_user_with_email_and_password(email, password)
    return jsonResponse


#################################################################################################################################
#                                                  Dev only                                                                     #
#################################################################################################################################
# dev routes only
if env["PRODUCTION_MODE"] != "TRUE":

    @authRouter.get("/dev-login")
    async def dev_login(uid: str, role: str):  #
        """Use this to login as a user with a specific uid and role bypassing authentication with firebase token (for dev only).
        \n This endpoint is only available in dev mode.
        :param uid: firebase
        :param role: role
        """
        try:
            return auth_handler.dev_encode_token(uid, role)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
