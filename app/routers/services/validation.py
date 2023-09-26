import numpy as np
import shapely.wkt
from fastapi import HTTPException, status


def validate_goem(geom: str) -> str:
    """validates a geometry string is a valid wkt string
    :param geom: wkt geometry to validate
    :return: wkt geometry if valid else raises an exception"""
    try:
        if geom is not None:
            shapely.wkt.loads(geom)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
    return geom
