from typing import Any

from geojson_pydantic.geometries import Geometry

from olmoearth_shared.api.common.search_filters import DatetimeFilter, KeywordFilter, NumericFilter, StringFilter


def geo_intersection_filter(geometry: Geometry, field_name: str) -> dict:
    """
    Filters to a geo_shape field that intersect with the provided geometry
    """
    return {"geo_shape": {field_name: {"relation": "intersects", "shape": geometry.model_dump(mode="json")}}}


def datetime_filter(f: DatetimeFilter, field: str) -> dict:
    """
    Computes the elasticsearch filter for a datetime field.
    We support searching both on time ranges, and also looking for existence/absence of a field.
    exists: True and a range filter doesn't make sense; this is a validation error.
    exists: True and no range filter: field exists.
    exists: False and no range filter: field does not exist
    exists: False and a range filter: field does not exist OR range filter
    """
    filters: list[dict[str, Any]] = []
    if f.exists is not None:
        exists_filter: dict[str, Any] = {"exists": {"field": field}}
        if not f.exists:
            exists_filter = {"bool": {"must_not": exists_filter}}
        filters.append(exists_filter)

    if f.gte or f.gt or f.lt or f.lte:
        conditions = {}
        if f.gte:
            conditions["gte"] = f.gte.isoformat()
        if f.gt:
            conditions["gt"] = f.gt.isoformat()
        if f.lte:
            conditions["lte"] = f.lte.isoformat()
        if f.lt:
            conditions["lt"] = f.lt.isoformat()
        filters.append({"range": {field: conditions}})

    if len(filters) == 1:
        return filters[0]  # just return the single filter
    # OR between the two
    return {"bool": {"should": filters}}


def numeric_filter(f: NumericFilter, field: str) -> dict:
    if f.eq is not None:
        return {"term": {field: f.eq}}
    if f.neq is not None:
        return {"bool": {"must_not": {"term": {field: f.neq}}}}
    # It must be one of the range filters, this is validated in the pydantic model
    conditions = {}
    if f.gte is not None:
        conditions["gte"] = f.gte
    if f.gt is not None:
        conditions["gt"] = f.gt
    if f.lte is not None:
        conditions["lte"] = f.lte
    if f.lt is not None:
        conditions["lt"] = f.lt
    return {"range": {field: conditions}}


def keyword_filter(f: KeywordFilter, field: str) -> dict:
    if f.eq:
        return {"term": {field: f.eq}}
    if f.neq:
        return {"bool": {"must_not": {"term": {field: f.neq}}}}
    if f.ninc:
        return {"bool": {"must_not": {"terms": {field: f.ninc}}}}
    if f.inc:
        return {"terms": {field: f.inc}}
    raise ValueError("Keyword filter must have one of eq, neq, in, or nin set")


def string_text_filter(f: StringFilter, field: str) -> dict:
    """
    Applies a String filter on a ES field of type text.
    Text fields generally do fuzzy matching; so this applies those specific query types
    """
    if f.eq:
        # AND requires that every word in the query appear in the document
        # so searching for "fruit eq 'green banana'" means we must have green AND banana in the field.
        return {"match": {field: {"query": f.eq, "operator": "AND"}}}
    if f.neq:
        return {"bool": {"must_not": {"match": {field: {"query": f.neq, "operator": "AND"}}}}}
    if f.inc:
        # OR means that as long as one of the words match, we'll take it.
        # so search "fruit in ["banana", "apple"]" will match when either banana OR apple appear
        return {"match": {field: {"query": " ".join(f.inc), "operator": "OR"}}}
    if f.ninc:
        return {"bool": {"must_not": {"match": {field: {"query": " ".join(f.ninc), "operator": "OR"}}}}}
    if f.like:
        return {"match_phrase": {field: {"query": f.like}}}
    if f.nlike:
        return {"bool": {"must_not": {"match_phrase": {field: {"query": f.nlike}}}}}
    raise ValueError(f"String filter missing condition for {field}")
