# Keble-DB

Lightweight database toolkit for MongoDB (PyMongo/Motor), SQL (SQLModel/SQLAlchemy), Qdrant, and Neo4j.
Includes sync + async CRUD base classes, a shared `QueryBase`, a `Db` session manager, FastAPI deps (`ApiDbDeps`), and Redis namespace wrappers.

## Installation

```bash
pip install keble-db
```

## Core API (import from `keble_db`)

- Queries/types: `DbSettingsABC`, `QueryBase`, `ObjectId`, `Uuid`
- CRUD:
  - `MongoCRUDBase[Model]`
  - `SqlCRUDBase[Model]`
  - `QdrantCRUDBase[Payload, Vector]` (+ `Record`)
  - `Neo4jCRUDBase[Model]`
- Connections/DI: `Db(settings: DbSettingsABC)`, `ApiDbDeps(db)`
- Redis: `ExtendedRedis`, `ExtendedAsyncRedis`
- Mongo helpers: `build_mongo_find_query`, `merge_mongo_and_queries`, `merge_mongo_or_queries`

Async methods are prefixed with `a` (e.g. `afirst`, `aget_multi`, `adelete`).

## `QueryBase` expectations

`QueryBase` fields: `filters`, `order_by`, `offset`, `limit`, `id`, `ids`.

- Mongo: `filters` is a Mongo query `dict`; `order_by` is `[(field, ASCENDING|DESCENDING)]`; `offset/limit` are `int`.
- SQL: `filters` is a `list` of SQLAlchemy expressions; `order_by` is an expression or list; `offset/limit` are `int`.
- Qdrant:
  - `search()`: `filters` is a Qdrant filter `dict`, `offset` is `int|None`, `limit` defaults to 100.
  - `scroll()`: `offset` is `PointId|None` (point id) and `limit` is required; ordering uses `order_by` (str or Qdrant `OrderBy`) or falls back to `QueryBase.order_by`. Qdrant requires a payload range index for the ordered key.
    Example: `from qdrant_client.models import PayloadSchemaType`; `crud.ensure_payload_indexes(client, payload_indexes={"id": PayloadSchemaType.INTEGER})`.
- Neo4j: `filters` is a `dict` of property predicates (operators: `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$contains`, `$startswith`, `$endswith`);
  `order_by` is `[(field, "asc"|"desc")]`; `offset/limit` are `int`.

## Examples

### MongoDB

```py
from pydantic import BaseModel
from pymongo import MongoClient, DESCENDING

from keble_db import MongoCRUDBase, QueryBase


class User(BaseModel):
    name: str
    age: int


crud = MongoCRUDBase(User, collection="users", database="app")
m = MongoClient("mongodb://localhost:27017")

crud.create(m, obj_in=User(name="Alice", age=30))
users = crud.get_multi(
    m,
    query=QueryBase(filters={"age": {"$gte": 18}}, order_by=[("age", DESCENDING)]),
)
```

### SQL (SQLModel)

```py
import uuid
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine

from keble_db import QueryBase, SqlCRUDBase


class User(SQLModel, table=True):
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True
    )
    name: str
    age: int


engine = create_engine("sqlite:///db.sqlite")
SQLModel.metadata.create_all(engine)
crud = SqlCRUDBase(User, table_name="users")

with Session(engine) as s:
    created = crud.create(s, obj_in=User(name="Alice", age=30))
    found = crud.first(s, query=QueryBase(id=created.id))
```

### Qdrant

Requires `qdrant-client>=1.16.0` (uses `query_points`).

```py
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from keble_db import QdrantCRUDBase, QueryBase


class Payload(BaseModel):
    id: int
    name: str


class Vector(BaseModel):
    vector: list[float]


client = QdrantClient(host="localhost", port=6333)
client.recreate_collection(
    collection_name="items",
    vectors_config={"vector": VectorParams(size=3, distance=Distance.COSINE)},
)

crud = QdrantCRUDBase(Payload, Vector, collection="items")
crud.ensure_payload_indexes(
    client,
    payload_indexes={"id": PayloadSchemaType.INTEGER},
)
crud.create(client, Vector(vector=[0.1, 0.2, 0.3]), Payload(id=1, name="a"), "p1")
hits = crud.search(
    client,
    vector=[0.1, 0.2, 0.3],
    vector_key="vector",
    query=QueryBase(filters={"must": [{"key": "id", "match": {"value": 1}}]}, limit=5),
)
```

If you have per-embedder collections (common in RAG), use deterministic naming:

```py
collection = QdrantCRUDBase.derive_collection_name(
    base="items",
    embedder_id="text-embedding-3-small",
)
crud = QdrantCRUDBase(Payload, Vector, collection=collection)
```

### Neo4j

```py
from pydantic import BaseModel
from neo4j import GraphDatabase

from keble_db import Neo4jCRUDBase, QueryBase


class Person(BaseModel):
    id: int
    name: str


driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))
crud = Neo4jCRUDBase(Person, label="Person", id_field="id")

with driver.session() as s:
    crud.create(s, obj_in=Person(id=1, name="Alice"))
    people = crud.get_multi(s, query=QueryBase(filters={"id": 1}))
```

## Db + FastAPI

`Db(settings)` builds clients from a `DbSettingsABC` implementation (see `keble_db/schemas.py` or `tests/config.py`).
`ApiDbDeps(db)` exposes FastAPI-friendly generator dependencies such as `get_mongo`, `get_amongo`, `get_read_sql`, `get_write_asql`, `get_qdrant`, `get_neo4j_session`, plus Redis equivalents.

## More runnable examples

See `tests/test_crud/` and `tests/test_api_deps.py`.
