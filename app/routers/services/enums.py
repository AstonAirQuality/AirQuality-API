from enum import Enum


class SensorMeasurementsColumns(Enum):
    # all columns should be in camelCase
    DATE = "timestamp"  # save date as timestamp UTC
    PM1 = "PM1"
    PM2_5 = "PM2.5"
    PM_4 = "PM4"  # SensorCommunity specific columns
    PM10 = "PM10"
    PM1_A = "PM1_A"
    PM1_B = "PM1_B"
    PM2_5_A = "PM2.5_A"
    PM2_5_B = "PM2.5_B"
    PM4_A = "PM4_A"  # SensorCommunity specific columns
    PM4_B = "PM4_B"  # SensorCommunity specific columns
    PM10_A = "PM10_A"
    PM10_B = "PM10_B"
    PM1_RAW = "PM1Raw"  # air gradient specific columns
    PM2_5_RAW = "PM2.5Raw"  # air gradient specific columns
    PM_4_RAW = "PM4Raw"  # SensorCommunity specific columns
    PM10_RAW = "PM10Raw"  # air gradient specific columns
    PM0_3_COUNT = "PM0.3Count"  # air gradient specific columns
    NO = "NO"
    NO2 = "NO2"
    NOX = "NOx"
    NOX_RAW = "NOxRaw"  # air gradient specific columns
    NOX_INDEX = "NOxIndex"  # air gradient specific columns
    CO = "CO"
    CO2 = "CO2"
    O3 = "O3"
    SO2 = "SO2"
    VOC = "VOC"
    TVOC_RAW = "TVOCRaw"  # air gradient specific columns
    VOC_INDEX = "VOCIndex"  # air gradient specific columns
    TEMPERATURE = "temperature"
    AMBIENT_TEMPERATURE = "ambientTemperature"
    HUMIDITY = "humidity"
    AMBIENT_HUMIDITY = "ambientHumidity"
    PRESSURE = "pressure"
    AMBIENT_PRESSURE = "ambientPressure"
    SCATTERING_COEFFICIENT = "scatteringCoefficient"
    DECIVIEWS = "deciviews"
    VISUAL_RANGE = "visualRange"
    NOISE_LA_MAX = "noiseLAMax"  # SensorCommunity specific columns
    NOISE_LA_MIN = "noiseLAMin"  # SensorCommunity specific columns
    NOISE_LA_EQ = "noiseLAEq"  # SensorCommunity specific columns
    NOISE_LA_EQ_DELOG = "noiseLAEqDelog"  # SensorCommunity specific columns
    LATITUDE = "latitude"
    LONGITUDE = "longitude"


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


class userColumns(str, Enum):
    uid = "uid"
    email = "email"
    username = "username"
    role = "role"
