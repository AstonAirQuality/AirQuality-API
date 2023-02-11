from enum import Enum


class Roles(Enum):
    """Enum for the roles"""

    admin = "admin"
    sensortech = "sensortech"
    user = "user"


class Authorisation:
    def __init__(self):
        self.roles = Roles
        self.valid_roles = [member.value for member in Roles]

    def checkRoleAdmin(self, payload: dict) -> bool:
        """checks if the user role is an admin
        :param payload: dict
        :return: bool"""
        if payload["role"] == Roles.admin.value:
            return True
        else:
            return False

    def checkRoleSensorTech(self, payload: dict) -> bool:
        """checks if the user role is a sensortech
        :param payload: dict
        :return: bool"""
        if payload["role"] == Roles.sensortech.value:
            return True
        else:
            return False

    def checkRoleAboveUser(self, payload: dict) -> bool:
        """checks if the user role is above user
        :param payload: dict
        :return: bool"""
        if payload["role"] == Roles.admin.value or payload["role"] == Roles.sensortech.value:
            return True
        else:
            return False
