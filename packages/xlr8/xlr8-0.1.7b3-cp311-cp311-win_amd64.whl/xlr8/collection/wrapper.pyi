"""Type stubs for XLR8 Collection.

Provides IDE autocomplete for all PyMongo methods plus XLR8 extensions.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

import bson
from bson.raw_bson import RawBSONDocument
from bson.timestamp import Timestamp
from pymongo.operations import (
    DeleteMany,
    DeleteOne,
    IndexModel,
    InsertOne,
    ReplaceOne,
    SearchIndexModel,
    UpdateMany,
    UpdateOne,
    _IndexKeyHint,
    _IndexList,
)
from pymongo.read_preferences import _ServerMode
from pymongo.results import (
    BulkWriteResult,
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)
from pymongo.synchronous.change_stream import CollectionChangeStream
from pymongo.synchronous.client_session import ClientSession
from pymongo.synchronous.collection import Collection as PyMongoCollection
from pymongo.synchronous.command_cursor import CommandCursor, RawBatchCommandCursor
from pymongo.synchronous.cursor import RawBatchCursor
from pymongo.synchronous.database import Database
from pymongo.typings import _CollationIn, _DocumentType, _DocumentTypeArg, _Pipeline
from pymongo.write_concern import WriteConcern

from .cursor import XLR8Cursor

_T = TypeVar("_T", bound=Mapping[str, Any])
_WriteOp = Union[
    InsertOne[_T], DeleteOne, DeleteMany, ReplaceOne[_T], UpdateOne, UpdateMany
]

class XLR8Collection(Generic[_DocumentType]):
    """PyMongo-compatible collection with optional acceleration.

    All PyMongo methods work via delegation. find() returns XLR8Cursor.
    """

    def __init__(
        self,
        pymongo_collection: PyMongoCollection[_DocumentType],
        schema: Optional[Any] = None,
        mongo_uri: Optional[Union[str, Callable[[], str]]] = None,
        approx_document_size_bytes: int = 500,
    ) -> None: ...
    def __getattr__(self, name: str) -> XLR8Collection[_DocumentType]: ...
    def __getitem__(self, name: str) -> XLR8Collection[_DocumentType]: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __bool__(self) -> NoReturn: ...
    @property
    def full_name(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def database(self) -> Database[_DocumentType]: ...
    @overload
    def with_options(
        self,
        codec_options: None = None,
        read_preference: _ServerMode | None = ...,
        write_concern: WriteConcern | None = ...,
        read_concern: Any | None = ...,
    ) -> XLR8Collection[_DocumentType]: ...
    @overload
    def with_options(
        self,
        codec_options: bson.CodecOptions[_DocumentTypeArg],
        read_preference: _ServerMode | None = ...,
        write_concern: WriteConcern | None = ...,
        read_concern: Any | None = ...,
    ) -> XLR8Collection[_DocumentTypeArg]: ...
    def __next__(self) -> NoReturn: ...
    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn: ...
    def watch(
        self,
        pipeline: _Pipeline | None = None,
        full_document: str | None = None,
        resume_after: Mapping[str, Any] | None = None,
        max_await_time_ms: int | None = None,
        batch_size: int | None = None,
        collation: _CollationIn | None = None,
        start_at_operation_time: Timestamp | None = None,
        session: ClientSession | None = None,
        start_after: Mapping[str, Any] | None = None,
        comment: Any | None = None,
        full_document_before_change: str | None = None,
        show_expanded_events: bool | None = None,
    ) -> CollectionChangeStream[_DocumentType]: ...
    def bulk_write(
        self,
        requests: Sequence[_WriteOp[_DocumentType]],
        ordered: bool = True,
        bypass_document_validation: bool | None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
        let: Mapping[str, Any] | None = None,
    ) -> BulkWriteResult: ...
    def insert_one(
        self,
        document: _DocumentType | RawBSONDocument,
        bypass_document_validation: bool | None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
    ) -> InsertOneResult: ...
    def insert_many(
        self,
        documents: Iterable[_DocumentType | RawBSONDocument],
        ordered: bool = True,
        bypass_document_validation: bool | None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
    ) -> InsertManyResult: ...
    def replace_one(
        self,
        filter: Mapping[str, Any],
        replacement: Mapping[str, Any],
        upsert: bool = False,
        bypass_document_validation: bool | None = None,
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        sort: Mapping[str, Any] | None = None,
        comment: Any | None = None,
    ) -> UpdateResult: ...
    def update_one(
        self,
        filter: Mapping[str, Any],
        update: Mapping[str, Any] | _Pipeline,
        upsert: bool = False,
        bypass_document_validation: bool | None = None,
        collation: _CollationIn | None = None,
        array_filters: Sequence[Mapping[str, Any]] | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        sort: Mapping[str, Any] | None = None,
        comment: Any | None = None,
    ) -> UpdateResult: ...
    def update_many(
        self,
        filter: Mapping[str, Any],
        update: Mapping[str, Any] | _Pipeline,
        upsert: bool = False,
        array_filters: Sequence[Mapping[str, Any]] | None = None,
        bypass_document_validation: bool | None = None,
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
    ) -> UpdateResult: ...
    def drop(
        self,
        session: ClientSession | None = None,
        comment: Any | None = None,
        encrypted_fields: Mapping[str, Any] | None = None,
    ) -> None: ...
    def delete_one(
        self,
        filter: Mapping[str, Any],
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
    ) -> DeleteResult: ...
    def delete_many(
        self,
        filter: Mapping[str, Any],
        collation: _CollationIn | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
    ) -> DeleteResult: ...
    def find_one(
        self, filter: Any | None = None, *args: Any, **kwargs: Any
    ) -> _DocumentType | None: ...
    def find(
        self,
        filter: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 0,
        sort: Optional[List[Tuple[str, int]]] = None,
        batch_size: int = 1000,
        # PyMongo compatibility parameters (passed through to cursor)
        no_cursor_timeout: bool = False,
        cursor_type: int = ...,
        allow_partial_results: bool = False,
        oplog_replay: bool = False,
        collation: Optional[Dict[str, Any]] = None,
        hint: Optional[Any] = None,
        max_scan: Optional[int] = None,
        max_time_ms: Optional[int] = None,
        max: Optional[List[Tuple[str, Any]]] = None,
        min: Optional[List[Tuple[str, Any]]] = None,
        return_key: Optional[bool] = None,
        show_record_id: Optional[bool] = None,
        snapshot: Optional[bool] = None,
        comment: Optional[Any] = None,
        session: Optional[Any] = None,
        allow_disk_use: Optional[bool] = None,
        let: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> XLR8Cursor[_DocumentType]: ...
    def find_raw_batches(
        self, *args: Any, **kwargs: Any
    ) -> RawBatchCursor[_DocumentType]: ...
    def estimated_document_count(
        self, comment: Any | None = None, **kwargs: Any
    ) -> int: ...
    def count_documents(
        self,
        filter: Mapping[str, Any],
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> int: ...
    def create_indexes(
        self,
        indexes: Sequence[IndexModel],
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> list[str]: ...
    def create_index(
        self,
        keys: _IndexKeyHint,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> str: ...
    def drop_indexes(
        self,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> None: ...
    def drop_index(
        self,
        index_or_name: _IndexKeyHint,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> None: ...
    def list_indexes(
        self, session: ClientSession | None = None, comment: Any | None = None
    ) -> CommandCursor[MutableMapping[str, Any]]: ...
    def index_information(
        self, session: ClientSession | None = None, comment: Any | None = None
    ) -> MutableMapping[str, Any]: ...
    def list_search_indexes(
        self,
        name: str | None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> CommandCursor[Mapping[str, Any]]: ...
    def create_search_index(
        self,
        model: Mapping[str, Any] | SearchIndexModel,
        session: ClientSession | None = None,
        comment: Any = None,
        **kwargs: Any,
    ) -> str: ...
    def create_search_indexes(
        self,
        models: list[SearchIndexModel],
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> list[str]: ...
    def drop_search_index(
        self,
        name: str,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> None: ...
    def update_search_index(
        self,
        name: str,
        definition: Mapping[str, Any],
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> None: ...
    def options(
        self, session: ClientSession | None = None, comment: Any | None = None
    ) -> MutableMapping[str, Any]: ...
    def aggregate(
        self,
        pipeline: _Pipeline,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> CommandCursor[_DocumentType]: ...
    def aggregate_raw_batches(
        self,
        pipeline: _Pipeline,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> RawBatchCommandCursor[_DocumentType]: ...
    def rename(
        self,
        new_name: str,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> MutableMapping[str, Any]: ...
    def distinct(
        self,
        key: str,
        filter: Mapping[str, Any] | None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
        hint: _IndexKeyHint | None = None,
        **kwargs: Any,
    ) -> list[Any]: ...
    def find_one_and_delete(
        self,
        filter: Mapping[str, Any],
        projection: Mapping[str, Any] | Iterable[str] | None = None,
        sort: _IndexList | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> _DocumentType | None: ...
    def find_one_and_replace(
        self,
        filter: Mapping[str, Any],
        replacement: Mapping[str, Any],
        projection: Mapping[str, Any] | Iterable[str] | None = None,
        sort: _IndexList | None = None,
        upsert: bool = False,
        return_document: bool = ...,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> _DocumentType | None: ...
    def find_one_and_update(
        self,
        filter: Mapping[str, Any],
        update: Mapping[str, Any] | _Pipeline,
        projection: Mapping[str, Any] | Iterable[str] | None = None,
        sort: _IndexList | None = None,
        upsert: bool = False,
        return_document: bool = ...,
        array_filters: Sequence[Mapping[str, Any]] | None = None,
        hint: _IndexKeyHint | None = None,
        session: ClientSession | None = None,
        let: Mapping[str, Any] | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> _DocumentType | None: ...

    # XLR8-specific methods
    def raw_collection(self) -> PyMongoCollection[_DocumentType]: ...
    def set_schema(self, schema: Any) -> None: ...
    def get_schema(self) -> Optional[Any]: ...
    def clear_cache(self) -> None: ...

    # XLR8 properties
    @property
    def schema(self) -> Optional[Any]: ...
    @property
    def pymongo_collection(self) -> PyMongoCollection[_DocumentType]: ...
    @property
    def mongo_uri(self) -> Optional[Union[str, Callable[[], str]]]: ...
    @property
    def approx_document_size_bytes(self) -> int: ...

def accelerate(
    pymongo_collection: PyMongoCollection[_DocumentType],
    schema: Any,
    mongo_uri: Union[str, Callable[[], str]],
    approx_document_size_bytes: int = 500,
) -> XLR8Collection[_DocumentType]: ...
