# dependancies:
import datetime as dt
from datetime import date

from core.authentication import AuthHandler
from core.models import Logs as ModelLogs
from core.schema import Log as SchemaLog
from fastapi import APIRouter, Depends, HTTPException, status
from routers.services.crud.crud import CRUD

logsRouter = APIRouter()
auth_handler = AuthHandler()


#################################################################################################################################
#                                                  Create                                                                       #
#################################################################################################################################
def add_log(log_timestamp: str, log: SchemaLog):
    """add a log to the database
    \n :param log: log schema
    \n :return: log object"""

    log = {"date": dt.datetime.strptime(log_timestamp, "%Y-%m-%d %H:%M:%S"), "data": log.log_data}
    return CRUD().db_add(ModelLogs, log)


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
    else:
        return CRUD().db_get_with_model(ModelLogs)


@logsRouter.get("/findByDate/{log_date}")
def get_log(log_date: date, payload=Depends(auth_handler.auth_wrapper)):
    """get a log from the database by date
    \n :param log_date: date of the log. Format: YYYY-MM-DD
    \n :param payload: auth payload
    \n :return: log object"""
    if auth_handler.checkRoleAdmin(payload) == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    else:
        end_date = (log_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
        return CRUD().db_get_with_model(ModelLogs, filter_expressions=[ModelLogs.date >= log_date, ModelLogs.date < end_date])


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
    else:
        return CRUD().db_delete(ModelLogs, [ModelLogs.date == log_date])
