# import firebase_admin
# from firebase_admin import credentials

# cred = credentials.Certificate("./config/aston-air-quality-firebase-adminsdk-4jn4i-2c19a6b6a9.json")
# firebaseapp = firebase_admin.initialize_app(cred)

import json

import pyrebase
import requests

config = {
    "apiKey": "AIzaSyAGNOikpc7Soo0JyLfCZf3SyWFw0hw5C_s",
    "authDomain": "aston-air-quality.firebaseapp.com",
    "projectId": "aston-air-quality",
    "storageBucket": "aston-air-quality.appspot.com",
    "messagingSenderId": "548225484857",
    "appId": "1:548225484857:web:712f958c834475123065e8",
    "measurementId": "G-KSXV6VRCEG",
    # "serviceAccount": ".\\app\\config\\aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",  # testing as script
    "serviceAccount": "./config/aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",
    "databaseURL": "",  # "https://aston-air-quality-default-rtdb.europe-west1.firebasedatabase.app/"
}


app = pyrebase.initialize_app(config)


class PyreBaseAuthWrapper(pyrebase.pyrebase.Auth):
    def __init__(self, apiKey, requests, credentials):
        super().__init__(apiKey, requests, credentials)

    def delete_user(self, id_token: str):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/deleteAccount?key={0}".format(
            self.api_key
        )
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"idToken": id_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        if request_object.status_code != 200:
            raise requests.HTTPError(request_object.text)
        else:
            return request_object.json()


PyreBaseAuth = PyreBaseAuthWrapper(app.api_key, app.requests, app.credentials)

# PyreBaseAuth = app.auth() # I use a wrapper to add my custom delete function. If you don't need it, you can just use app.auth()

############# LINKS #############
# jwt wihout firebase
# https://www.youtube.com/watch?v=0_seNFCtglk

# links
# https://www.youtube.com/watch?v=HltzFtn9f1c
# https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth
# https://firebase.google.com/docs/auth/admin/custom-claims#node.js_1

# not important
# https://firebase.google.com/docs/admin/setup#windows
