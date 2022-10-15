import numpy as np
import shapely.wkt
from fastapi import HTTPException, status
from geoalchemy2.shape import (  # used to convert WKBE geometry to string
    from_shape,
    to_shape,
)


############################################################################################################
#                                   Spatial helper functions                                               #
############################################################################################################
def spatialQueryBuilder(query: any, model: any, column_name: str, geom_query_type: str, geom: str) -> any:
    """adds spatial filters to a query"""

    geom = convertWKTtoWKB(geom)
    geom_column = getattr(model, column_name)

    if geom_query_type == "intersect":
        query = query.filter(geom_column.ST_Intersects(geom))
    elif geom_query_type == "within":
        query = query.filter(geom_column.ST_Within(geom))
    elif geom_query_type == "contains":
        query = query.filter(geom_column.ST_Contains(geom))
    elif geom_query_type == "overlaps":
        query = query.filter(geom_column.ST_Overlaps(geom))
    elif geom_query_type == "equals":
        query = query.filter(geom_column.ST_Equals(geom))
    elif geom_query_type == "disjoint":
        query = query.filter(geom_column.ST_Disjoint(geom))
    elif geom_query_type == "touches":
        query = query.filter(geom_column.ST_Touches(geom))
    elif geom_query_type == "crosses":
        query = query.filter(geom_column.ST_Crosses(geom))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid geom_type")

    return query


def convertWKTtoWKB(wkt: str) -> any:
    try:
        wkb = from_shape(shapely.wkt.loads(wkt), srid=4326)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geometry must be a valid WKTE geometry: {e}")
    return wkb


def convertWKBtoWKT(element: any) -> str:
    """converts wkb element to human-readable (wkt string)"""
    try:
        # if the element is already a string, then it is already in wkt format
        if isinstance(element, str):
            return element
        if element is not None:
            return to_shape(element).wkt
    except AssertionError:
        pass
    return None


def get_centre_of_polygon(geometryString):
    """gets the centre point of a polygon

    :param geometryString: string of the geometry of the polygon (e.g POLYGON ((long,lat)) )
    """
    latitude = np.array([])
    longitude = np.array([])

    for coordsPair in geometryString.split("POLYGON ((")[1].split("))")[0].split(", "):
        long, lat = coordsPair.split(" ")
        latitude = np.append(latitude, float(lat))
        longitude = np.append(longitude, float(long))

    return longitude.mean(), latitude.mean()

#################################################################################################################################
#                                              Validator functions                                                              #
#################################################################################################################################
def validate_goem(geom):
    try:
        if geom is not None:
            shapely.wkt.loads(geom)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geom must be a valid WKTE geometry: {e}")
    return geom
