import datetime as dt
from os import environ as env

import jwt
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from routers.helpers.usersSharedFunctions import get_user_role


class AuthHandler:
    security = HTTPBearer()
    secret = env["JWT_SECRET"]

    # decodes the jwt token from firebase # https://stackoverflow.com/questions/69319437/decode-firebase-jwt-in-python-using-pyjwt
    def verify_firebase_token(self, token):
        try:
            n_decoded = jwt.get_unverified_header(token)
            kid_claim = n_decoded["kid"]

            response = requests.get(
                "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
            )
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

    def encode_token(self, token: str):
        decoded_jwt = self.verify_firebase_token(token)
        role = get_user_role(decoded_jwt["user_id"])["role"]

        if role == None:
            role = "user"

        payload = {
            "sub": decoded_jwt["user_id"],
            "role": role,
            "iat": dt.datetime.utcnow(),
            "exp": dt.datetime.utcnow() + dt.timedelta(hours=1),
        }

        return jwt.encode(payload, self.secret, algorithm="HS256")

    def dev_encode_token(self, uid: str, role: str):
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
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Signature has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(auth.credentials)
