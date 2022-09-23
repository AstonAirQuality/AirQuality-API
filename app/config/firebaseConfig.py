# import firebase_admin
# from firebase_admin import credentials

# cred = credentials.Certificate("./config/aston-air-quality-firebase-adminsdk-4jn4i-2c19a6b6a9.json")
# firebaseapp = firebase_admin.initialize_app(cred)

import pyrebase

config = {
    "apiKey": "AIzaSyAGNOikpc7Soo0JyLfCZf3SyWFw0hw5C_s",
    "authDomain": "aston-air-quality.firebaseapp.com",
    "projectId": "aston-air-quality",
    "storageBucket": "aston-air-quality.appspot.com",
    "messagingSenderId": "548225484857",
    "appId": "1:548225484857:web:712f958c834475123065e8",
    "measurementId": "G-KSXV6VRCEG",
    "serviceAccount": "./config/aston-air-quality-firebase-adminsdk-4jn4i-2c19a6b6a9.json",
    "databaseURL": "",  # "https://aston-air-quality-default-rtdb.europe-west1.firebasedatabase.app/"
}


app = pyrebase.initialize_app(config)
PyreBaseAuth = app.auth()

# jwt wihout firebase
# https://www.youtube.com/watch?v=0_seNFCtglk

# links
# https://www.youtube.com/watch?v=HltzFtn9f1c
# https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth
# https://firebase.google.com/docs/auth/admin/custom-claims#node.js_1

# not important
# https://firebase.google.com/docs/admin/setup#windows
