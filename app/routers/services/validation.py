from os import environ as env

import numpy as np
import shapely.wkt
from fastapi import HTTPException, status


def validate_geom(geom: str) -> str:
    """validates a geometry string is a valid wkt string
    :param geom: wkt geometry to validate
    :return: wkt geometry if valid else raises an exception"""
    try:
        if geom is not None:
            shapely.wkt.loads(geom)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
    return geom


def validate_json_file_size(file_size: int) -> None:
    """validates the file size is within the limit set in the .env file
    :param file_size: size of the file in bytes
    :raises HTTPException: if the file size exceeds the limit"""
    try:
        filesize_limit = int(env.get("FILESIZE_LIMIT", 0))
        if file_size > filesize_limit:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the limit")
        elif file_size >= 500 * 1024 * 1024:
            return True
        else:
            return False
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invalid FILESIZE_LIMIT in .env: {e}")
