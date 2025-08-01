from os import environ as env

import numpy as np
import shapely.wkt
from fastapi import HTTPException, status


def validate_geom(geom: str) -> str:
    """validates a geometry string is a valid wkt string
    Args:
        geom (str): The geometry string to validate.
    Raises:
        HTTPException: if the geometry string is not a valid wkt string
    Returns:
        str: The validated geometry string.
    """
    try:
        if geom is not None:
            shapely.wkt.loads(geom)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
    return geom


def validate_json_file_size(file_size: int) -> None:
    """validates the file size is within the limit set in the .env file
    Args:
        file_size (int): The size of the file in bytes.
    Raises:
        HTTPException: if the file size exceeds the limit
    Returns:
        bool: True if the file size is greater than or equal to 500MB, False otherwise.
    """
    try:
        file_size = file_size / 1024 / 1024  # convert to MB
        filesize_limit_str = env.get("FILESIZE_LIMIT", "1024")
        filesize_limit = int(filesize_limit_str) * 1.5  # default to 1024 MB. Multiply by 1.5 because this is before gzip compression
        if file_size > filesize_limit:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the limit")
        elif file_size >= 1024:  # 1GB
            return True
        else:
            return False
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invalid FILESIZE_LIMIT in .env: {e}")
