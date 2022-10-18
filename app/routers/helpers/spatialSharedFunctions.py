import numpy as np
import shapely.wkt
from fastapi import HTTPException, status
from geoalchemy2.shape import WKBElement, from_shape, to_shape


############################################################################################################
#                                   Spatial helper functions                                               #
############################################################################################################
def spatialQueryBuilder(query: any, model: any, column_name: str, spatial_query_type: str, geom: str) -> any:
    """adds spatial filters to a query
    :param query: query to add filters to
    :param model: model to filter by
    :param column_name: geometry column to filter by
    :param spatial_query_type: type of spatial query to perform
    :param geom: geometry to filter by
    :return: query with filters applied
    """

    geom = convertWKTtoWKB(geom)
    geom_column = getattr(model, column_name)

    if spatial_query_type == "intersect":
        query = query.filter(geom_column.ST_Intersects(geom))
    elif spatial_query_type == "within":
        query = query.filter(geom_column.ST_Within(geom))
    elif spatial_query_type == "contains":
        query = query.filter(geom_column.ST_Contains(geom))
    elif spatial_query_type == "overlaps":
        query = query.filter(geom_column.ST_Overlaps(geom))
    elif spatial_query_type == "equals":
        query = query.filter(geom_column.ST_Equals(geom))
    elif spatial_query_type == "disjoint":
        query = query.filter(geom_column.ST_Disjoint(geom))
    elif spatial_query_type == "touches":
        query = query.filter(geom_column.ST_Touches(geom))
    elif spatial_query_type == "crosses":
        query = query.filter(geom_column.ST_Crosses(geom))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid geom_type")

    return query


def convertWKTtoWKB(wkt: str) -> WKBElement:
    """converts wkt string to wkb element
    :param wkt: wkt string
    :return: wkb element"""
    try:
        wkb = from_shape(shapely.wkt.loads(wkt), srid=4326)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"geometry must be a valid WKTE geometry: {e}")
    return wkb


def convertWKBtoWKT(element: any) -> str:
    """converts wkb element to human-readable (wkt string)
    :param element: wkb element
    :return: wkt string"""
    try:
        # if the element is already a string, then it is already in wkt format
        if isinstance(element, str):
            return element
        if element is not None:
            return to_shape(element).wkt
    except AssertionError:
        pass
    return None


#################################################################################################################################
#                                              Validator functions                                                              #
#################################################################################################################################
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
