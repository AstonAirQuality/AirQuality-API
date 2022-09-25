# import firebase_admin
# from firebase_admin import credentials

# cred = credentials.Certificate("./config/aston-air-quality-firebase-adminsdk-4jn4i-2c19a6b6a9.json")
# firebaseapp = firebase_admin.initialize_app(cred)

import json

import pyrebase
import requests

# jwt decode
# import jwt
# import requests
# from cryptography import x509
# from cryptography.hazmat.backends import default_backend
# from fastapi import HTTPException

config = {
    "apiKey": "AIzaSyAGNOikpc7Soo0JyLfCZf3SyWFw0hw5C_s",
    "authDomain": "aston-air-quality.firebaseapp.com",
    "projectId": "aston-air-quality",
    "storageBucket": "aston-air-quality.appspot.com",
    "messagingSenderId": "548225484857",
    "appId": "1:548225484857:web:712f958c834475123065e8",
    "measurementId": "G-KSXV6VRCEG",
    "serviceAccount": ".\\app\\config\\aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",
    "databaseURL": "",  # "https://aston-air-quality-default-rtdb.europe-west1.firebasedatabase.app/"
}


app = pyrebase.initialize_app(config)
PyreBaseAuth = app.auth()


def delete_user(auth, id_token):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/deleteAccount?key={0}".format(
        auth.api_key
    )
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"idToken": id_token})
    request_object = requests.post(request_ref, headers=headers, data=data)
    if request_object.status_code != 200:
        raise requests.HTTPError(request_object.text)
    else:
        return request_object.json()


# # decodes the jwt token from firebase # https://stackoverflow.com/questions/69319437/decode-firebase-jwt-in-python-using-pyjwt
# def verify_firebase_token(token):
#     try:
#         n_decoded = jwt.get_unverified_header(token)
#         kid_claim = n_decoded["kid"]

#         response = requests.get(
#             "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
#         )
#         x509_key = response.json()[kid_claim]
#         key = x509.load_pem_x509_certificate(x509_key.encode("utf-8"), backend=default_backend())
#         public_key = key.public_key()

#         decoded_token = jwt.decode(token, public_key, ["RS256"], options=None, audience="aston-air-quality")

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Signature has expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     except Exception:
#         raise HTTPException(status_code=500, detail="Internal server error")

#     return decoded_token


# json_ = PyreBaseAuth.sign_in_with_email_and_password("test@test.com", "test123")
# token = verify_firebase_token(json_["idToken"])
# print(token)


# jwt wihout firebase
# https://www.youtube.com/watch?v=0_seNFCtglk

# links
# https://www.youtube.com/watch?v=HltzFtn9f1c
# https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth
# https://firebase.google.com/docs/auth/admin/custom-claims#node.js_1

# not important
# https://firebase.google.com/docs/admin/setup#windows
