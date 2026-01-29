from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from bson import ObjectId as _ObjectId
from keble_helpers import ObjectId, Uuid
from pydantic import BaseModel, ConfigDict
from qdrant_client.conversions.common_types import PointId


def serialize_object_ids_in_dict(mey_be_dict: Any):
    if not isinstance(mey_be_dict, dict):
        return
    for key, val in mey_be_dict.items():
        if isinstance(val, _ObjectId):
            mey_be_dict[key] = str(val)
        elif isinstance(val, dict):
            serialize_object_ids_in_dict(val)
        elif isinstance(val, list):
            for item in val:
                serialize_object_ids_in_dict(item)


class DbSettingsABC(ABC):
    @property
    @abstractmethod
    def qdrant_host(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def qdrant_port(self) -> Optional[int]: ...

    @property
    @abstractmethod
    def mongo_db_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def redis_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def sql_write_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def sql_read_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def sql_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def neo4j_uri(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def neo4j_user(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def neo4j_password(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def neo4j_database(self) -> Optional[str]: ...


class QueryBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    offset: Optional[int | str | PointId] = None
    limit: Optional[int] = None
    filters: Optional[Union[dict, List[Any]]] = None
    order_by: Optional[Any] = None

    id: Optional[Union[ObjectId, Uuid, str, int]] = None
    ids: Optional[List[Union[ObjectId, Uuid, str, int]]] = None

    def __init__(
        self,
        offset: Optional[Union[int, str, PointId]] = None,
        limit: Optional[int] = None,
        filters: Optional[Union[dict, List[Any]]] = None,
        order_by: Optional[Any] = None,
        id: Optional[Union[ObjectId, Uuid, str, int]] = None,
        ids: Optional[List[Union[ObjectId, Uuid, str, int]]] = None,
    ):
        # Perform custom initialization logic if necessary

        # Call the Pydantic BaseModel initializer to perform the standard model validation and initialization
        super().__init__(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by,
            id=id,
            ids=ids,
        )

    @classmethod
    def loop(cls, func, *args, **kwargs) -> List[Any]:
        page = 0
        page_size = 100
        res = []
        has_more = True
        base_query: QueryBase | None = kwargs.get("query")
        if "query" in kwargs:
            del kwargs["query"]
        base_query_dict: dict = (
            base_query.model_dump() if base_query is not None else {}
        )
        if "offset" in base_query_dict:
            del base_query_dict["offset"]
        if "limit" in base_query_dict:
            del base_query_dict["limit"]
        while page < 10000 and has_more:
            query = QueryBase(
                **base_query_dict, limit=page_size, offset=page * page_size
            )

            output = func(*args, **kwargs, query=query)
            if len(output) == 0:
                break
            has_more = len(output) == page_size
            res += output
            page += 1
        return res

    @classmethod
    async def aloop(cls, afunc, *args, **kwargs) -> List[Any]:
        page = 0
        page_size = 100
        res = []
        has_more = True
        base_query: QueryBase | None = kwargs.get("query")
        if "query" in kwargs:
            del kwargs["query"]
        base_query_dict: dict = (
            base_query.model_dump() if base_query is not None else {}
        )
        if "offset" in base_query_dict:
            del base_query_dict["offset"]
        if "limit" in base_query_dict:
            del base_query_dict["limit"]
        while page < 10000 and has_more:
            query = QueryBase(
                **base_query_dict, limit=page_size, offset=page * page_size
            )

            output = await afunc(*args, **kwargs, query=query)
            if len(output) == 0:
                break
            has_more = len(output) == page_size
            res += output
            page += 1
        return res

    @classmethod
    def qdrant_scroll(cls, func, *args, **kwargs) -> List[Any]:
        page = 0
        page_size = 100
        offset = None  # point id
        res = []
        has_more = True
        base_query: QueryBase | None = kwargs.get("query")
        if "query" in kwargs:
            del kwargs["query"]

        base_query_dict: dict = (
            base_query.model_dump() if base_query is not None else {}
        )
        if "offset" in base_query_dict:
            del base_query_dict["offset"]
        if "limit" in base_query_dict:
            del base_query_dict["limit"]
        while page < 10000 and has_more:
            query = QueryBase(**base_query_dict, limit=page_size, offset=offset)
            output, next_point_id = func(*args, **kwargs, query=query)
            if len(output) == 0:
                break
            has_more = next_point_id is not None
            res += output
            page += 1
            offset = next_point_id
        return res
