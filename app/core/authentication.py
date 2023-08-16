import datetime as dt
from os import environ as env
from typing import Tuple

import jwt
import requests
from core.authorisation import Authorisation
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from routers.services.usersSharedFunctions import get_user_token_info


class AuthHandler(Authorisation):
    """
    Handles the encoding and decoding of JWT tokens
    """

    def __init__(self):
        super().__init__()
        self.secret = env["JWT_SECRET"]

    def verify_firebase_token(self, token):
        """Verifies and decodes Firebase ID token.
        :reference: https://stackoverflow.com/questions/69319437/decode-firebase-jwt-in-python-using-pyjwt
        :param token: Firebase ID token to verify and decode.
        :return: Decoded Firebase ID token.
        """
        try:
            n_decoded = jwt.get_unverified_header(token)
            kid_claim = n_decoded["kid"]

            response = requests.get("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com")
            x509_key = response.json()[kid_claim]
            key = x509.load_pem_x509_certificate(x509_key.encode("utf-8"), backend=default_backend())
            public_key = key.public_key()

            decoded_token = jwt.decode(token, public_key, ["RS256"], options=None, audience="aston-air-quality")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Signature has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")

        return decoded_token

    def encode_token(self, token: str) -> Tuple[str, str]:
        """Encodes a Firebase ID token into a custom JWT token with user role claims
        :param token: Firebase ID token
        :return: Tuple of custom JWT token, user role and username
        """
        decoded_jwt = self.verify_firebase_token(token)

        user_info = get_user_token_info(decoded_jwt["sub"])

        if user_info == None:
            raise HTTPException(status_code=401, detail="User does not exist. Please register an account")

        payload = {
            "sub": decoded_jwt["sub"],
            "role": user_info[0],
            "iat": dt.datetime.utcnow(),
            "exp": dt.datetime.utcnow() + dt.timedelta(hours=1),
        }

        token = jwt.encode(payload, self.secret, algorithm="HS256")
        return (token, user_info[0], user_info[1])

    def dev_encode_token(self, uid: str, role: str):
        """Encodes a custom JWT token with user role claims for development purposes
        :param uid: user id
        :param role: user role
        :return: custom JWT token"""
        payload = {
            "sub": uid,
            "role": role,
            "iat": dt.datetime.utcnow(),
            "exp": dt.datetime.utcnow() + dt.timedelta(hours=1),
        }

        # generate a custom jwt token
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        return token

    def decode_token(self, token: str):
        """Decodes a custom JWT token
        :param token: custom JWT token
        :return: decoded token
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Signature has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        return self.decode_token(auth.credentials)
