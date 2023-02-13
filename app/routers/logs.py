# dependancies:
import datetime as dt

from core.authentication import AuthHandler
from core.models import Logs as ModelLogs
from core.schema import Log as SchemaLog
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status

logsRouter = APIRouter()

db = SessionLocal()
auth_handler = AuthHandler()

#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
def add_log(log_timestamp: str, log: SchemaLog):
    """add a log to the database
    \n :param log: log schema
    \n :return: log object"""
    try:
        log = ModelLogs(date=dt.datetime.strptime(log_timestamp, "%Y-%m-%d %H:%M:%S"), data=log.log_data)
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return log


#################################################################################################################################
#                                                  Read                                                                         #
#################################################################################################################################
@logsRouter.get("")
def get_log(payload=Depends(auth_handler.auth_wrapper)):
    """get all logs from the database
    \n :param payload: auth payload
    \n :return: log object"""

    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        result = db.query(ModelLogs).all()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve log")
    return result


# TODO get all logs in that day. (not just the first one)
@logsRouter.get("/findByDate/{log_date}")
def get_log(log_date: str, payload=Depends(auth_handler.auth_wrapper)):
    """get a log from the database by date
    \n :param log_date: date of the log. Format: YYYY-MM-DD
    \n :param payload: auth payload
    \n :return: log object"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    log_date = dt.datetime.strptime(log_date, "%Y-%m-%d")
    end_date = (log_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    log_date = log_date.strftime("%Y-%m-%d")

    try:
        result = db.query(ModelLogs).filter(ModelLogs.date >= log_date, ModelLogs.date < end_date).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve log")

    return result


#################################################################################################################################
#                                                  Update                                                                       #
#################################################################################################################################
#################################################################################################################################
#                                                  Delete                                                                       #
#################################################################################################################################
@logsRouter.delete("/{log_date}")
def delete_log(log_date: str, payload=Depends(auth_handler.auth_wrapper)):
    """delete a log from the database by date
    \n :param log_date: date of the log
    \n :param payload: auth payload
    \n :return: log object"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    try:
        db.query(ModelLogs).filter(ModelLogs.date == log_date).delete()
        db.commit()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete log")
    return {"message": "Log deleted successfully"}
