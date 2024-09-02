from config.firebaseConfig import PyreBaseDB


def addFirebaseNotifcationDataIngestionTask(uid: str, timestamp_key: str, status: int, message: str):
    """adds a firebase notification data ingestion task to the realtime db
    :param user_id: user id
    :param timestamp_key: timestamp key
    :param status: status of the task
    :param message: message of the task
    """
    PyreBaseDB.child("data-ingestion-tasks").child(timestamp_key).set({"uid": uid, "status": status, "message": message})


def updateFirebaseNotifcationDataIngestionTask(timestamp_key: str, status: int, message: str):
    """updates a firebase notification data ingestion task in the queue
    :param timestamp_key: timestamp key
    :param status: status of the task
    :param message: message of the task"""

    PyreBaseDB.child("data-ingestion-tasks").child(timestamp_key).update({"status": status, "message": message})


def clearFirebaseNotifcationDataIngestionTask():
    """clears all firebase notification data ingestion task in the queue
    :param timestamp_key: timestamp key"""

    PyreBaseDB.child("data-ingestion-tasks").remove()
