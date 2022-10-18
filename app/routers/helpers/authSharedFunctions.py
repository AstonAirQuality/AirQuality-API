from enum import Enum


class Roles(Enum):
    """Enum for the roles"""

    admin = "admin"
    sensortech = "sensortech"
    user = "user"


def checkRoleAdmin(payload: dict) -> bool:
    """checks if the user is an admin
    :param payload: dict
    :return: bool"""
    if payload["role"] == Roles.admin.value:
        return True
    else:
        return False


def checkRoleSensorTech(payload: dict) -> bool:
    """checks if the user is an admin
    :param payload: dict
    :return: bool"""
    if payload["role"] == Roles.sensortech.value:
        return True
    else:
        return False


def checkRoleAboveUser(payload: dict) -> bool:
    """checks if the user is an admin
    :param payload: dict
    :return: bool"""
    if payload["role"] == Roles.admin.value or payload["role"] == Roles.sensortech.value:
        return True
    else:
        return False
