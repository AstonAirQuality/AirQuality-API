from core.models import SensorSummaries as ModelSensorSummary
from fastapi import HTTPException, status
from routers.services.formatting import convertWKTtoWKB


############################################################################################################
#                                   Spatial helper functions                                               #
############################################################################################################
# adding search filters
def searchQueryFilters(filter_expressions: list[any], spatial_query_type: str, geom: str, sensor_ids: list[str]) -> list[any]:
    """applies search filter_expressions to the query
    :param filter_expressions: list of filter_expressions to apply
    :param spatial_query_type: type of geometry filter query to use (intersects, contains, within)
    :param geom: geometry to filter by
    :param sensor_ids: list of sensor ids to filter by
    :return: list of filter_expressions to apply to the query"""

    if sensor_ids:
        filter_expressions.append(ModelSensorSummary.sensor_id.in_(sensor_ids))

    if spatial_query_type and geom is not None:
        spatialQueryBuilder(filter_expressions, ModelSensorSummary, "geom", spatial_query_type, geom)

    return filter_expressions


def spatialQueryBuilder(filter_expressions: list[any], model: any, column_name: str, spatial_query_type: str, geom: str) -> list[any]:
    """adds spatial filter_expressions to a query
    :param filter_expressions: list of filter_expressions to apply
    :param model: model to filter by
    :param column_name: geometry column to filter by
    :param spatial_query_type: type of spatial query to perform
    :param geom: geometry to filter by
    :return: list of filter_expressions to apply to the query
    """

    geom = convertWKTtoWKB(geom)
    geom_column = getattr(model, column_name)

    if spatial_query_type == "intersects":
        filter_expressions.append(geom_column.ST_Intersects(geom))
    elif spatial_query_type == "within":
        filter_expressions.append(geom_column.ST_Within(geom))
    elif spatial_query_type == "contains":
        filter_expressions.append(geom_column.ST_Contains(geom))
    elif spatial_query_type == "overlaps":
        filter_expressions.append(geom_column.ST_Overlaps(geom))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid geom_type")

    return filter_expressions


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
        if columns is not None:
            for col in columns:
                fields.append(getattr(model, col))
        else:
            # append all columns from the model to the fields list (model.__table__.columns)
            fields.extend(model.__table__.columns)

        for key, val in join_columns.items():
            # append key and value to fields list
            fields.append(key.label(val))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return fields
