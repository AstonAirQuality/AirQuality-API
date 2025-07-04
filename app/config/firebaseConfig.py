# load environment variables
from os import environ as env

from config.firebaseWrapper import Firebase
from dotenv import load_dotenv

load_dotenv()

config = {
    "apiKey": env["FIREBASE_API_KEY"],
    "authDomain": env["FIREBASE_AUTH_DOMAIN"],
    "projectId": env["FIREBASE_PROJECT_ID"],
    "storageBucket": env["FIREBASE_STORAGE_BUCKET"],
    "messagingSenderId": env["FIREBASE_MESSAGING_SENDER_ID"],
    "appId": env["FIREBASE_APP_ID"],
    "measurementId": env["FIREBASE_MEASUREMENT_ID"],
    # "serviceAccount": ".\\app\\config\\aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",  #NOTE: testing as script
    "serviceAccount": env["FIREBASE_SERVICE_ACCOUNT"],
    "databaseURL": env["FIREBASE_DATABASE_URL"],
}

PyreBaseAuth = Firebase(config).auth()
PyreBaseDB = Firebase(config).database()

# if __name__ == "__main__":
#     users = PyreBaseDB.child("users").get()
#     print(users.val())
# from firebaseWrapper import Firebase  #NOTE: testing as script
