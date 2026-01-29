import hashlib
import logging
import re
from typing import (
    Any,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    cast,
)
from uuid import UUID

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client import models as qdrant_models
from qdrant_client.conversions import common_types as qdrant_types
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from ..schemas import QueryBase
from .qdrant_util import cleanse_query_for_search

ModelType = TypeVar("ModelType", bound=BaseModel)
VectorModelType = TypeVar("VectorModelType", bound=BaseModel)

logger = logging.getLogger(__name__)

ShardKeySelector = (
    int | str | list[int | str] | qdrant_models.ShardKeyWithFallback | None
)
WithPayload = (
    bool
    | Sequence[str]
    | qdrant_models.PayloadSelectorInclude
    | qdrant_models.PayloadSelectorExclude
)
WithVectors = bool | Sequence[str]
ReadConsistency = int | qdrant_models.ReadConsistencyType | None
OrderBy = str | qdrant_models.OrderBy | None

try:
    from qdrant_client.grpc import common_pb2 as grpc_common_pb2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    grpc_common_pb2 = None


def _safe_collection_suffix(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_\\-]", "_", value).strip("_")
    if not safe:
        safe = "embedder"
    if len(safe) > 48:
        digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
        safe = f"{safe[:39]}_{digest}"
    return safe


def derive_collection_name(*, base: str, embedder_id: str) -> str:
    """Deterministically derive a collection name from a base name and embedder id."""

    return f"{base}__{_safe_collection_suffix(embedder_id)}"


class Record(qdrant_types.Record, Generic[VectorModelType]):
    payload: Optional[Any] = None
    score: Optional[float] = None
    vector: Optional[VectorModelType] = None


class QdrantCRUDBase(Generic[ModelType, VectorModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        vector_model: Type[VectorModelType],
        collection: str,
    ):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD) in Qdrant

        **Parameters**
        * `model`: A Qdrant Alchemy model class
        """
        self.model: Type[ModelType] = model
        self.vector_model: Type[VectorModelType] = vector_model
        self.collection = collection

    @staticmethod
    def derive_collection_name(*, base: str, embedder_id: str) -> str:
        return derive_collection_name(base=base, embedder_id=embedder_id)

    @classmethod
    def _infer_vectors_config(
        cls,
        *,
        vector_size: int,
        vector_keys: Sequence[str],
        distance: qdrant_models.Distance,
    ) -> Mapping[str, qdrant_models.VectorParams]:
        if vector_size <= 0:
            raise ValueError(f"[Db] vector_size must be > 0, got {vector_size}")
        if not vector_keys:
            raise ValueError("[Db] vector_keys cannot be empty")
        return {
            key: qdrant_models.VectorParams(size=vector_size, distance=distance)
            for key in vector_keys
        }

    @classmethod
    def _infer_vectors_config_from_sample(
        cls,
        *,
        vector_sample: VectorModelType,
        distance: qdrant_models.Distance,
    ) -> Mapping[str, qdrant_models.VectorParams]:
        vector_dict = vector_sample.model_dump(exclude_none=True, exclude_unset=True)
        if not vector_dict:
            raise ValueError("[Db] vector_sample produced an empty vector dict")

        config: dict[str, qdrant_models.VectorParams] = {}
        for key, value in vector_dict.items():
            if not isinstance(value, list) or not value:
                raise ValueError(
                    f"[Db] Expected vector_sample.{key} to be a non-empty list[float], got {type(value)}"
                )
            config[key] = qdrant_models.VectorParams(size=len(value), distance=distance)
        return config

    @staticmethod
    def _collection_exists(client: QdrantClient, *, collection_name: str) -> bool:
        try:
            collections = client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.debug(
                "[Db] Qdrant get_collections failed, falling back to get_collection: %s",
                e,
            )
            try:
                client.get_collection(collection_name)
                return True
            except UnexpectedResponse as exc:
                if exc.status_code != 404:
                    raise
                return False
            except ResponseHandlingException:
                return True

    @staticmethod
    async def _acollection_exists(
        client: AsyncQdrantClient, *, collection_name: str
    ) -> bool:
        try:
            collections = await client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.debug(
                "[Db] Qdrant get_collections failed, falling back to get_collection: %s",
                e,
            )
            try:
                await client.get_collection(collection_name)
                return True
            except UnexpectedResponse as exc:
                if exc.status_code != 404:
                    raise
                return False
            except ResponseHandlingException:
                return True

    def ensure_collection(
        self,
        client: QdrantClient,
        *,
        vectors_config: qdrant_models.VectorParams
        | Mapping[str, qdrant_models.VectorParams]
        | None = None,
        vector_size: int | None = None,
        vector_keys: Sequence[str] | None = None,
        vector_sample: VectorModelType | None = None,
        distance: qdrant_models.Distance = qdrant_models.Distance.COSINE,
        payload_indexes: Sequence[str]
        | Mapping[str, qdrant_models.PayloadSchemaType]
        | None = None,
    ) -> None:
        """Ensure collection and (optional) payload indexes exist.

        Prefer passing `vectors_config` explicitly. If not provided, you can pass either:
        - `vector_size` (+ optional `vector_keys`)
        - `vector_sample` (a VectorModel instance) to infer vector sizes
        """

        if vectors_config is None:
            if vector_size is not None:
                keys = (
                    list(self.vector_model.model_fields.keys())
                    if vector_keys is None
                    else list(vector_keys)
                )
                vectors_config = self._infer_vectors_config(
                    vector_size=vector_size, vector_keys=keys, distance=distance
                )
            elif vector_sample is not None:
                vectors_config = self._infer_vectors_config_from_sample(
                    vector_sample=vector_sample, distance=distance
                )
            else:
                raise ValueError(
                    "[Db] Must provide vectors_config, vector_size, or vector_sample"
                )

        exists = self._collection_exists(client, collection_name=self.collection)
        if not exists:
            try:
                client.create_collection(
                    collection_name=self.collection,
                    vectors_config=vectors_config,
                )
            except UnexpectedResponse as exc:
                if exc.status_code != 409:
                    raise

        if payload_indexes is not None:
            self.ensure_payload_indexes(client, payload_indexes=payload_indexes)

    async def aensure_collection(
        self,
        client: AsyncQdrantClient,
        *,
        vectors_config: qdrant_models.VectorParams
        | Mapping[str, qdrant_models.VectorParams]
        | None = None,
        vector_size: int | None = None,
        vector_keys: Sequence[str] | None = None,
        vector_sample: VectorModelType | None = None,
        distance: qdrant_models.Distance = qdrant_models.Distance.COSINE,
        payload_indexes: Sequence[str]
        | Mapping[str, qdrant_models.PayloadSchemaType]
        | None = None,
    ) -> None:
        """Async variant of `ensure_collection`."""

        if vectors_config is None:
            if vector_size is not None:
                keys = (
                    list(self.vector_model.model_fields.keys())
                    if vector_keys is None
                    else list(vector_keys)
                )
                vectors_config = self._infer_vectors_config(
                    vector_size=vector_size, vector_keys=keys, distance=distance
                )
            elif vector_sample is not None:
                vectors_config = self._infer_vectors_config_from_sample(
                    vector_sample=vector_sample, distance=distance
                )
            else:
                raise ValueError(
                    "[Db] Must provide vectors_config, vector_size, or vector_sample"
                )

        exists = await self._acollection_exists(client, collection_name=self.collection)
        if not exists:
            try:
                await client.create_collection(
                    collection_name=self.collection,
                    vectors_config=vectors_config,
                )
            except UnexpectedResponse as exc:
                if exc.status_code != 409:
                    raise

        if payload_indexes is not None:
            await self.aensure_payload_indexes(client, payload_indexes=payload_indexes)

    def ensure_payload_indexes(
        self,
        client: QdrantClient,
        *,
        payload_indexes: Sequence[str] | Mapping[str, qdrant_models.PayloadSchemaType],
    ) -> None:
        index_map: Mapping[str, qdrant_models.PayloadSchemaType]
        if isinstance(payload_indexes, Mapping):
            index_map = payload_indexes
        else:
            index_map = {
                field: qdrant_models.PayloadSchemaType.KEYWORD
                for field in payload_indexes
            }

        for field_name, field_schema in index_map.items():
            try:
                client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            except UnexpectedResponse as exc:
                if exc.status_code == 409:
                    continue
                logger.warning(
                    "[Db] Failed to create Qdrant payload index %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )
            except ResponseHandlingException as exc:
                logger.warning(
                    "[Db] Qdrant payload index response handling error for %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )
            except Exception as exc:
                logger.exception(
                    "[Db] Unexpected error creating Qdrant payload index %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )

    async def aensure_payload_indexes(
        self,
        client: AsyncQdrantClient,
        *,
        payload_indexes: Sequence[str] | Mapping[str, qdrant_models.PayloadSchemaType],
    ) -> None:
        index_map: Mapping[str, qdrant_models.PayloadSchemaType]
        if isinstance(payload_indexes, Mapping):
            index_map = payload_indexes
        else:
            index_map = {
                field: qdrant_models.PayloadSchemaType.KEYWORD
                for field in payload_indexes
            }

        for field_name, field_schema in index_map.items():
            try:
                await client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            except UnexpectedResponse as exc:
                if exc.status_code == 409:
                    continue
                logger.warning(
                    "[Db] Failed to create Qdrant payload index %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )
            except ResponseHandlingException as exc:
                logger.warning(
                    "[Db] Qdrant payload index response handling error for %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )
            except Exception as exc:
                logger.exception(
                    "[Db] Unexpected error creating Qdrant payload index %s.%s: %s",
                    self.collection,
                    field_name,
                    exc,
                )

    def __is_result_success(self, result: qdrant_types.UpdateResult):
        return (
            result.status.lower() == qdrant_models.UpdateStatus.COMPLETED.value.lower()
        )

    def __convert_payload(self, payload: Any) -> ModelType:
        return self.model.model_validate(payload)

    def __convert_vector(self, vector: Any) -> VectorModelType:
        if isinstance(vector, dict):
            return self.vector_model.model_validate(vector)
        if isinstance(vector, list):
            if getattr(self.vector_model, "__pydantic_root_model__", False):
                return self.vector_model.model_validate(vector)
            field_names = list(self.vector_model.model_fields.keys())
            if len(field_names) == 1:
                return self.vector_model.model_validate({field_names[0]: vector})
        return self.vector_model.model_validate(vector)

    def __convert_record(self, record: qdrant_types.Record) -> Record[VectorModelType]:
        base = record.model_dump(exclude={"payload", "vector"})
        base["payload"] = (
            self.__convert_payload(record.payload)
            if record.payload is not None
            else None
        )
        base["vector"] = (
            self.__convert_vector(record.vector) if record.vector is not None else None
        )
        return Record.model_validate(base)

    def __convert_scored_point(
        self, point: qdrant_types.ScoredPoint
    ) -> Record[VectorModelType]:
        base = point.model_dump(include={"score", "shard_key", "id"})
        base["payload"] = (
            self.__convert_payload(point.payload) if point.payload is not None else None
        )
        base["vector"] = (
            self.__convert_vector(point.vector) if point.vector is not None else None
        )
        return Record.model_validate(base)

    def __convert_records(self, records: List[qdrant_types.Record]) -> List[Record]:
        return [self.__convert_record(record=record) for record in records]

    def get_multi_records_by_ids(
        self,
        client: QdrantClient,
        *,
        _ids: Sequence[qdrant_types.PointId],
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[Record]:
        return self.__convert_records(
            client.retrieve(
                collection_name=self.collection,
                ids=_ids,
                with_payload=with_payload,
                with_vectors=with_vectors,
                consistency=consistency,
                shard_key_selector=shard_key_selector,
                timeout=timeout,
            )
        )

    async def aget_multi_records_by_ids(
        self,
        client: AsyncQdrantClient,
        *,
        _ids: Sequence[qdrant_types.PointId],
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[Record]:
        return self.__convert_records(
            await client.retrieve(
                collection_name=self.collection,
                ids=_ids,
                with_payload=with_payload,
                with_vectors=with_vectors,
                consistency=consistency,
                shard_key_selector=shard_key_selector,
                timeout=timeout,
            )
        )

    def get_multi_by_ids(
        self,
        client: QdrantClient,
        *,
        _ids: Sequence[qdrant_types.PointId],
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[ModelType]:
        records = self.get_multi_records_by_ids(
            client,
            _ids=_ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [r.payload for r in records if r.payload is not None]

    async def aget_multi_by_ids(
        self,
        client: AsyncQdrantClient,
        *,
        _ids: Sequence[qdrant_types.PointId],
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[ModelType]:
        records = await self.aget_multi_records_by_ids(
            client,
            _ids=_ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [r.payload for r in records if r.payload is not None]

    def first_record_by_id(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Optional[Record]:
        records: List[Record] = self.get_multi_records_by_ids(
            client,
            _ids=[_id],
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        if len(records) < 1:
            return None
        return records[0]

    async def afirst_record_by_id(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Optional[Record]:
        records: List[Record] = await self.aget_multi_records_by_ids(
            client,
            _ids=[_id],
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        if len(records) < 1:
            return None
        return records[0]

    def first_by_id(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Optional[ModelType]:
        record = self.first_record_by_id(
            client,
            _id=_id,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        if record is not None:
            return record.payload

    async def afirst_by_id(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Optional[ModelType]:
        record = await self.afirst_record_by_id(
            client,
            _id=_id,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        if record is not None:
            return record.payload

    @classmethod
    def _build_search_params(
        cls, query: Optional[QueryBase | dict] = None
    ) -> tuple[qdrant_types.Filter | None, int, int | None]:
        if isinstance(query, dict):
            query = QueryBase.model_validate(query)
        filter_ = cleanse_query_for_search(
            query, offset_type="int", allow_order_by=False
        )
        offset: int | None = None
        if query is not None and query.offset is not None:
            assert isinstance(query.offset, int), (
                f"[Db] Expected search in qdrant with int or None type offset, but got {query.offset}"
            )
            offset = query.offset
        limit = query.limit if query is not None and query.limit is not None else 100
        return filter_, limit, offset

    def search(
        self,
        client: QdrantClient,
        *,
        vector: List[float],
        vector_key: str,
        query: Optional[QueryBase | dict] = None,
        score_threshold: float | None = 0.76,
        # 0.76 ~ 0.8 is a decent threshold base on our test, among different languages
        with_payload: WithPayload = True,
        with_vectors: WithVectors = True,
        prefetch: qdrant_models.Prefetch | list[qdrant_models.Prefetch] | None = None,
        search_params: qdrant_models.SearchParams | None = None,
        consistency: ReadConsistency = None,
        lookup_from: qdrant_models.LookupLocation | None = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[Record]:
        query_filter, limit, offset = self._build_search_params(query)
        resp = client.query_points(
            collection_name=self.collection,
            query=vector,
            using=vector_key,
            prefetch=prefetch,
            query_filter=query_filter,
            search_params=search_params,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            score_threshold=score_threshold,
            lookup_from=lookup_from,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [self.__convert_scored_point(point=sp) for sp in resp.points]

    async def asearch(
        self,
        client: AsyncQdrantClient,
        *,
        vector: List[float],
        vector_key: str,
        query: Optional[QueryBase | dict] = None,
        score_threshold: float | None = 0.76,
        # 0.76 ~ 0.8 is a decent threshold base on our test, among different languages
        with_payload: WithPayload = True,
        with_vectors: WithVectors = True,
        prefetch: qdrant_models.Prefetch | list[qdrant_models.Prefetch] | None = None,
        search_params: qdrant_models.SearchParams | None = None,
        consistency: ReadConsistency = None,
        lookup_from: qdrant_models.LookupLocation | None = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> List[Record]:
        query_filter, limit, offset = self._build_search_params(query)
        resp = await client.query_points(
            collection_name=self.collection,
            query=vector,
            using=vector_key,
            prefetch=prefetch,
            query_filter=query_filter,
            search_params=search_params,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            score_threshold=score_threshold,
            lookup_from=lookup_from,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [self.__convert_scored_point(point=sp) for sp in resp.points]

    @classmethod
    def _normalize_order_by(cls, order_by: Any) -> OrderBy:
        if order_by is None:
            return None
        if isinstance(order_by, (str, qdrant_models.OrderBy)):
            return order_by
        if isinstance(order_by, dict):
            return qdrant_models.OrderBy.model_validate(order_by)
        raise TypeError(
            f"[Db] Qdrant order_by must be str|OrderBy|dict|None, got {type(order_by)}"
        )

    @classmethod
    def _build_scroll_params(
        cls, query: Optional[QueryBase | dict] = None, *, order_by: OrderBy = None
    ) -> tuple[qdrant_types.Filter | None, int, qdrant_types.PointId | None, OrderBy]:
        if isinstance(query, dict):
            query = QueryBase.model_validate(query)
        resolved_order_by = order_by
        if (
            resolved_order_by is None
            and query is not None
            and query.order_by is not None
        ):
            resolved_order_by = cls._normalize_order_by(query.order_by)

        filter_ = cleanse_query_for_search(
            query, offset_type="str", allow_order_by=True
        )
        assert query is None or query.limit is not None, (
            "[Db] You need to provide limit to perform a scroll in Qdrant"
        )
        offset: qdrant_types.PointId | None = None
        if query is not None and query.offset is not None:
            point_id_types: tuple[type, ...] = (int, str, UUID)
            if grpc_common_pb2 is not None:
                point_id_types = (*point_id_types, grpc_common_pb2.PointId)
            assert isinstance(query.offset, point_id_types), (
                f"[Db] Expected point id (int|str|uuid|grpc PointId) or None type query offset when scrolling records in qdrant, but got {query.offset}"
            )
            offset = query.offset

        limit = query.limit if query is not None and query.limit is not None else 100
        return filter_, limit, offset, resolved_order_by

    def scroll_records(
        self,
        client: QdrantClient,
        *,
        query: QueryBase | dict | None,
        order_by: OrderBy = None,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Tuple[List[Record], Optional[qdrant_types.PointId]]:
        scroll_filter, limit, offset, resolved_order_by = self._build_scroll_params(
            query, order_by=order_by
        )
        records, next_point_id = client.scroll(
            collection_name=self.collection,
            scroll_filter=scroll_filter,
            limit=limit,
            order_by=resolved_order_by,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return self.__convert_records(records), next_point_id

    async def ascroll_records(
        self,
        client: AsyncQdrantClient,
        *,
        query: QueryBase | dict | None,
        order_by: OrderBy = None,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Tuple[List[Record], Optional[qdrant_types.PointId]]:
        scroll_filter, limit, offset, resolved_order_by = self._build_scroll_params(
            query, order_by=order_by
        )
        records, next_point_id = await client.scroll(
            collection_name=self.collection,
            scroll_filter=scroll_filter,
            limit=limit,
            order_by=resolved_order_by,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return self.__convert_records(records), next_point_id

    def scroll(
        self,
        client: QdrantClient,
        *,
        query: QueryBase | dict | None,
        order_by: OrderBy = None,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Tuple[List[ModelType], Optional[qdrant_types.PointId]]:
        records, next_point_id = self.scroll_records(
            client,
            query=query,
            order_by=order_by,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [
            record.payload for record in records if record.payload is not None
        ], next_point_id

    async def ascroll(
        self,
        client: AsyncQdrantClient,
        *,
        query: QueryBase | dict | None,
        order_by: OrderBy = None,
        with_payload: WithPayload = True,
        with_vectors: WithVectors = False,
        consistency: ReadConsistency = None,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> Tuple[List[ModelType], Optional[qdrant_types.PointId]]:
        records, next_point_id = await self.ascroll_records(
            client,
            query=query,
            order_by=order_by,
            with_payload=with_payload,
            with_vectors=with_vectors,
            consistency=consistency,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return [
            record.payload for record in records if record.payload is not None
        ], next_point_id

    def create(
        self,
        client: QdrantClient,
        vector: VectorModelType,
        payload: ModelType,
        _id: qdrant_types.PointId,
        *,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        vector_dict = vector.model_dump(exclude_none=True, exclude_unset=True)
        res = client.upsert(
            collection_name=self.collection,
            points=[
                qdrant_models.PointStruct(
                    id=cast(qdrant_models.ExtendedPointId, _id),
                    vector=vector_dict,
                    payload=payload.model_dump(),
                )
            ],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    async def acreate(
        self,
        client: AsyncQdrantClient,
        vector: VectorModelType,
        payload: ModelType,
        _id: qdrant_types.PointId,
        *,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        vector_dict = vector.model_dump(exclude_none=True, exclude_unset=True)
        res = await client.upsert(
            collection_name=self.collection,
            points=[
                qdrant_models.PointStruct(
                    id=cast(qdrant_models.ExtendedPointId, _id),
                    vector=vector_dict,
                    payload=payload.model_dump(),
                )
            ],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    def create_multi(
        self,
        client: QdrantClient,
        *,
        payloads_and_vectors: List[Tuple[str, ModelType, VectorModelType]],
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        points: List[qdrant_models.PointStruct] = [
            qdrant_models.PointStruct(
                id=_id,
                vector=vector.model_dump(exclude_none=True, exclude_unset=True),
                payload=payload.model_dump(),
            )
            for _id, payload, vector in payloads_and_vectors
        ]
        res = client.upsert(
            collection_name=self.collection,
            points=points,
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    async def acreate_multi(
        self,
        client: AsyncQdrantClient,
        *,
        payloads_and_vectors: List[Tuple[str, ModelType, VectorModelType]],
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        points: List[qdrant_models.PointStruct] = [
            qdrant_models.PointStruct(
                id=_id,
                vector=vector.model_dump(exclude_none=True, exclude_unset=True),
                payload=payload.model_dump(),
            )
            for _id, payload, vector in payloads_and_vectors
        ]
        res = await client.upsert(
            collection_name=self.collection,
            points=points,
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    def delete(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        update_result: qdrant_types.UpdateResult = client.delete(
            collection_name=self.collection,
            points_selector=[_id],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(update_result)

    async def adelete(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        update_result: qdrant_types.UpdateResult = await client.delete(
            collection_name=self.collection,
            points_selector=[_id],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(update_result)

    def _get_points_selector_by_delete_query(
        self,
        query: QueryBase | dict | None,
    ) -> qdrant_models.PointIdsList | qdrant_models.FilterSelector:
        if query is None:
            query_dict: dict = {}
        else:
            if isinstance(query, dict):
                query = QueryBase.model_validate(query)
            query_dict: dict = query.model_dump(
                exclude_none=True, exclude_unset=True, exclude_defaults=True
            )
        filters_exist = "filters" in query_dict and query_dict["filters"] is not None
        ids_exist = "ids" in query_dict and query_dict["ids"] is not None
        if not (filters_exist or ids_exist):
            raise ValueError(
                "[Db] you must set query.ids or query.filters to delete_multi in qdrant"
            )
        if ids_exist:
            points_selector = qdrant_models.PointIdsList(points=query_dict["ids"])
        elif filters_exist:
            points_selector = qdrant_models.FilterSelector(filter=query_dict["filters"])
        else:
            raise Exception(
                "[Db] you must set query.ids or query.filters to delete_multi in qdrant"
            )
        return points_selector

    def delete_multi(
        self,
        client: QdrantClient,
        *,
        query: QueryBase | dict | None,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        points_selector = self._get_points_selector_by_delete_query(query)
        update_result: qdrant_types.UpdateResult = client.delete(
            collection_name=self.collection,
            points_selector=points_selector,
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(update_result)

    async def adelete_multi(
        self,
        client: AsyncQdrantClient,
        *,
        query: QueryBase | dict | None,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        points_selector = self._get_points_selector_by_delete_query(query)
        update_result: qdrant_types.UpdateResult = await client.delete(
            collection_name=self.collection,
            points_selector=points_selector,
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(update_result)

    def update_payload(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        payload: ModelType,
        key: str | None = None,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        """Set Payload key value, not completely override entire payload object"""
        old_payload = self.first_by_id(client, _id=_id)
        if old_payload is not None:
            obj_dict = old_payload.model_dump()
            obj_dict.update(payload.model_dump())
            res = client.set_payload(
                collection_name=self.collection,
                payload=self.__convert_payload(obj_dict).model_dump(),
                points=[_id],
                key=key,
                wait=wait,
                ordering=ordering,
                shard_key_selector=shard_key_selector,
            )
            return self.__is_result_success(res)
        return False

    async def aupdate_payload(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        payload: ModelType,
        key: str | None = None,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        """Set Payload key value, not completely override entire payload object"""
        old_payload = await self.afirst_by_id(client, _id=_id)
        if old_payload is not None:
            obj_dict = old_payload.model_dump()
            obj_dict.update(payload.model_dump())
            res = await client.set_payload(
                collection_name=self.collection,
                payload=self.__convert_payload(obj_dict).model_dump(),
                points=[_id],
                key=key,
                wait=wait,
                ordering=ordering,
                shard_key_selector=shard_key_selector,
            )
            return self.__is_result_success(res)
        return False

    def overwrite_payload(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        payload: ModelType,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        """Completely override entire payload object, replace entire old payload"""
        res = client.overwrite_payload(
            collection_name=self.collection,
            payload=payload.model_dump(),
            points=[_id],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    async def aoverwrite_payload(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        payload: ModelType,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ):
        """Completely override entire payload object, replace entire old payload"""
        res = await client.overwrite_payload(
            collection_name=self.collection,
            payload=payload.model_dump(),
            points=[_id],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    def update_vector(
        self,
        client: QdrantClient,
        *,
        _id: qdrant_types.PointId,
        vector: VectorModelType,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        res = client.update_vectors(
            collection_name=self.collection,
            points=[
                qdrant_models.PointVectors(
                    id=cast(qdrant_models.ExtendedPointId, _id),
                    vector=vector.model_dump(exclude_none=True, exclude_unset=True),
                )
            ],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    async def aupdate_vector(
        self,
        client: AsyncQdrantClient,
        *,
        _id: qdrant_types.PointId,
        vector: VectorModelType,
        wait: bool = True,
        ordering: qdrant_models.WriteOrdering | None = None,
        shard_key_selector: ShardKeySelector = None,
    ) -> bool:
        res = await client.update_vectors(
            collection_name=self.collection,
            points=[
                qdrant_models.PointVectors(
                    id=cast(qdrant_models.ExtendedPointId, _id),
                    vector=vector.model_dump(exclude_none=True, exclude_unset=True),
                )
            ],
            wait=wait,
            ordering=ordering,
            shard_key_selector=shard_key_selector,
        )
        return self.__is_result_success(res)

    def count(
        self,
        client: QdrantClient,
        *,
        query: Optional[QueryBase | dict] = None,
        exact: bool = True,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> int:
        filter_ = cleanse_query_for_search(query, offset_type="int")
        return client.count(
            collection_name=self.collection,
            count_filter=filter_,
            exact=exact,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        ).count

    async def acount(
        self,
        client: AsyncQdrantClient,
        *,
        query: Optional[QueryBase | dict] = None,
        exact: bool = True,
        shard_key_selector: ShardKeySelector = None,
        timeout: int | None = None,
    ) -> int:
        filter_ = cleanse_query_for_search(query, offset_type="int")
        result = await client.count(
            collection_name=self.collection,
            count_filter=filter_,
            exact=exact,
            shard_key_selector=shard_key_selector,
            timeout=timeout,
        )
        return result.count
