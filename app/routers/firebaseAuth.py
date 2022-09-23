# # dependancies:
import datetime as dt
from os import environ as env

import jwt
from config.firebaseConfig import PyreBaseAuth  # TODO remove this dependancy
from core.auth import AuthHandler

# from api_wrappers.scraperWrapper import ScraperWrapper
# from core.models import Users as ModelUser
# from core.schema import User as SchemaUser
# from db.database import SessionLocal
# from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status

# from psycopg2.errors import UniqueViolation

# # error handling
# from sqlalchemy.exc import IntegrityError


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

# notes
"""
signup and login occurs in the frontend then the jwt token from firebase is passed to the backend
verify the jwt token is signed by google and extract the uid
generate a custom jwt token with the uid and custom claims (role)
send the custom jwt token back to the frontend
the frontend will then store the token in local storage
the frontend will then send the token with every request
the backend will then verify the token and check the custom claims
"""


@authRouter.get("/login")
async def login(email: str, password: str):
    try:
        user = PyreBaseAuth.sign_in_with_email_and_password(email, password)
        return auth_handler.encode_token(user["idToken"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# dev login (skip firebase auth)
if env["PRODUCTION_MODE"] != "TRUE":

    @authRouter.get("/dev-login")
    async def dev_login(uid: str):
        try:
            return auth_handler.dev_encode_token(uid)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@authRouter.get("/protected")
async def protected(payload=Depends(auth_handler.auth_wrapper)):

    if payload["role"] == "admin":
        return {"message": "Hello admin"}
    else:
        return {"message": "Hello user"}
