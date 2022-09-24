def checkRoleAdmin(payload: dict) -> bool:
    """checks if the user is an admin"""
    if payload["role"] == "admin":
        return True
    else:
        raise False


def checkRoleSensorTech(payload: dict) -> bool:
    """checks if the user is an admin"""
    if payload["role"] == "sensortech":
        return True
    else:
        raise False


def checkRoleAboveUser(payload: dict) -> bool:
    """checks if the user is an admin"""
    if payload["role"] == "admin" or payload["role"] == "sensortech":
        return True
    else:
        raise False
