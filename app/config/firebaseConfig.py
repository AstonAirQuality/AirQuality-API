from config.firebaseWrapper import Firebase

# from firebaseWrapper import Firebase  #NOTE: testing as script

config = {
    "apiKey": "AIzaSyAGNOikpc7Soo0JyLfCZf3SyWFw0hw5C_s",
    "authDomain": "aston-air-quality.firebaseapp.com",
    "projectId": "aston-air-quality",
    "storageBucket": "aston-air-quality.appspot.com",
    "messagingSenderId": "548225484857",
    "appId": "1:548225484857:web:712f958c834475123065e8",
    "measurementId": "G-KSXV6VRCEG",
    # "serviceAccount": ".\\app\\config\\aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",  #NOTE: testing as script
    "serviceAccount": "./config/aston-air-quality-firebase-adminsdk-4jn4i-dc3d87e1bd.json",
    "databaseURL": "",  # "https://aston-air-quality-default-rtdb.europe-west1.firebasedatabase.app/"
}

PyreBaseAuth = Firebase(config).auth()
