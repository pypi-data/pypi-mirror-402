import uuid
from typing import Literal, Optional, cast

from qdrant_client import models as qdrant_models
from qdrant_client.conversions.common_types import Filter

from ..schemas import QueryBase

try:
    from qdrant_client.grpc import common_pb2 as grpc_common_pb2
except Exception:  # pragma: no cover - optional dependency
    grpc_common_pb2 = None


def cleanse_query_for_search(
    query: Optional[QueryBase | dict],
    offset_type: Literal["int", "str"] = "int",
    *,
    allow_order_by: bool = False,
) -> Filter | None:
    if query is None:
        return None
    elif isinstance(query, dict):
        query = QueryBase.model_validate(query)
    if offset_type == "int":
        assert query.offset is None or isinstance(query.offset, int), (
            "[Db] Offset must be int in Qdrant searching"
        )
    elif offset_type == "str":
        point_id_types: tuple[type, ...] = (int, str, uuid.UUID)
        if grpc_common_pb2 is not None:
            point_id_types = (*point_id_types, grpc_common_pb2.PointId)
        assert query.offset is None or isinstance(query.offset, point_id_types), (
            "[Db] Offset must be point id (int|str|uuid|grpc PointId) in Qdrant scroll"
        )
    assert query.id is None, (
        "[Db] QueryBase's 'id' key should not being use for similarity search in qdrant"
    )
    assert query.ids is None, (
        "[Db] QueryBase's 'ids' key should not being use for similarity search in qdrant"
    )
    if not allow_order_by:
        assert query.order_by is None, (
            "[Db] QueryBase's 'order_by' key should not being use for similarity search in qdrant"
        )
    if query.filters is None:
        return None

    if isinstance(query.filters, qdrant_models.Filter):
        return cast(Filter, query.filters)

    if not isinstance(query.filters, dict):
        raise AssertionError("[Db] Query.filters only accept dict or qdrant Filter")

    # forbidden id and ids in filters
    if "id" in query.filters:
        raise AssertionError(
            "[Db] You should not include 'id' in your QueryBase.filters when searching Qdrant"
        )
    if "ids" in query.filters:
        raise AssertionError(
            "[Db] You should not include 'ids' in your QueryBase.filters when searching Qdrant"
        )

    return qdrant_models.Filter.model_validate(query.filters)
