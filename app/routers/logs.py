# dependancies:
import datetime as dt

from core.auth import AuthHandler
from core.models import Logs as ModelLogs
from core.schema import Log as SchemaLog
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status

from routers.helpers.authSharedFunctions import checkRoleAdmin

logsRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
def add_log(log: SchemaLog):
    """add a log to the database
    :param log: log schema
    :return: log object"""
    try:
        log = ModelLogs(date=dt.datetime.today(), data=log.log_data)
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return log


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@logsRouter.get("/read")
def get_log(payload=Depends(auth_handler.auth_wrapper)):
    """get all logs from the database
    :param payload: auth payload
    :return: log object"""

    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        result = db.query(ModelLogs).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve log")
    return result


@logsRouter.get("/read/{log_date}")
def get_log(log_date: str, payload=Depends(auth_handler.auth_wrapper)):
    """get a log from the database by date
    :param log_date: date of the log
    :param payload: auth payload
    :return: log object"""
    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        result = db.query(ModelLogs).filter(ModelLogs.date == log_date).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve log")

    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@logsRouter.delete("/delete/{log_date}")
def delete_log(log_date: str, payload=Depends(auth_handler.auth_wrapper)):
    """delete a log from the database by date
    :param log_date: date of the log
    :param payload: auth payload
    :return: log object"""
    if checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        db.query(ModelLogs).filter(ModelLogs.date == log_date).delete()
        db.commit()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete log")
    return {"message": "Log deleted successfully"}
