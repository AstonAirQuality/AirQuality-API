from enum import Enum


class ActiveReason(str, Enum):
    """Enum for the reason a sensor was activated or deactivated"""

    NO_DATA = "DEACTIVATED_NO_DATA"
    ACTIVE_BY_USER = "ACTIVATED_BY_USER"
    DEACTVATE_BY_USER = "DEACTIVATED_BY_USER"
    REMOVED = "REMOVED_FROM_SENSOR_FLEET"


class sensorSummaryColumns(str, Enum):
    sensor_id = "sensor_id"
    measurement_count = "measurement_count"
    measurement_data = "measurement_data"
    stationary = "stationary"
    geom = "geom"
    timestamp = "timestamp"


class spatialQueryType(str, Enum):
    intersects = "intersects"
    contains = "contains"
    within = "within"
    overlaps = "overlaps"


class averagingMethod(str, Enum):
    mean = "mean"
    count = "count"
    median = "median"
    min = "min"
    max = "max"

class userColumns(str,Enum):
    uid = "uid"
    email = "email"
    username = "username"
    role = "role"

