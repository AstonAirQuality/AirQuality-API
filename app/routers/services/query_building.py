from core.models import SensorSummaries as ModelSensorSummary
from fastapi import HTTPException, status
from routers.services.formatting import convertWKTtoWKB


############################################################################################################
#                                   Spatial helper functions                                               #
############################################################################################################
# adding search filters
def searchQueryFilters(query: any, spatial_query_type: str, geom: str, sensor_ids: list[str]) -> any:
    """applies search filters to the query
    :param query: query to apply filters to
    :param spatial_query_type: type of geometry filter query to use (intersects, contains, within)
    :param geom: geometry to filter by
    :param sensor_ids: list of sensor ids to filter by
    :return: query with filters applied"""

    if sensor_ids:
        query = query.filter(ModelSensorSummary.sensor_id.in_(sensor_ids))

    if spatial_query_type and geom is not None:
        query = spatialQueryBuilder(query, ModelSensorSummary, "geom", spatial_query_type, geom)

    return query


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

    if spatial_query_type == "intersects":
        query = query.filter(geom_column.ST_Intersects(geom))
    elif spatial_query_type == "within":
        query = query.filter(geom_column.ST_Within(geom))
    elif spatial_query_type == "contains":
        query = query.filter(geom_column.ST_Contains(geom))
    elif spatial_query_type == "overlaps":
        query = query.filter(geom_column.ST_Overlaps(geom))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid geom_type")

    return query


def joinQueryBuilder(fields: any, model: any, columns: list, join_columns: dict = None):
    """builds a query for a joined table with custom fields
    :param fields: fields to return
    :param model: model to query
    :param columns: columns to return
    :param join_columns: columns to join
    :return: query with joined columns applied
    """
    fields = []
    try:
        for col in columns:
            fields.append(getattr(model, col))
        for key, val in join_columns.items():
            # append key and value to fields list
            fields.append(key.label(val))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return fields
