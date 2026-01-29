import datetime

from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Snapshot(_message.Message):
    __slots__ = ("id", "parent_id", "hierarchy", "task_type", "task_name", "task_index", "env_type", "session_id", "step", "tags", "node", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    HIERARCHY_FIELD_NUMBER: _ClassVar[int]
    TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_INDEX_FIELD_NUMBER: _ClassVar[int]
    ENV_TYPE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    parent_id: str
    hierarchy: _containers.RepeatedScalarFieldContainer[str]
    task_type: str
    task_name: str
    task_index: _common_pb2.TaskIndex
    env_type: str
    session_id: int
    step: int
    tags: _containers.RepeatedScalarFieldContainer[str]
    node: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., parent_id: _Optional[str] = ..., hierarchy: _Optional[_Iterable[str]] = ..., task_type: _Optional[str] = ..., task_name: _Optional[str] = ..., task_index: _Optional[_Union[_common_pb2.TaskIndex, _Mapping]] = ..., env_type: _Optional[str] = ..., session_id: _Optional[int] = ..., step: _Optional[int] = ..., tags: _Optional[_Iterable[str]] = ..., node: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetStorePathResponse(_message.Message):
    __slots__ = ("root_path", "total_bytes", "free_bytes")
    ROOT_PATH_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    FREE_BYTES_FIELD_NUMBER: _ClassVar[int]
    root_path: str
    total_bytes: int
    free_bytes: int
    def __init__(self, root_path: _Optional[str] = ..., total_bytes: _Optional[int] = ..., free_bytes: _Optional[int] = ...) -> None: ...

class CreateSnapshotRequest(_message.Message):
    __slots__ = ("task_type", "task_name", "task_index", "env_type", "parent_id", "session_id", "step", "tags", "expected_size")
    TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_INDEX_FIELD_NUMBER: _ClassVar[int]
    ENV_TYPE_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_SIZE_FIELD_NUMBER: _ClassVar[int]
    task_type: str
    task_name: str
    task_index: _common_pb2.TaskIndex
    env_type: str
    parent_id: str
    session_id: int
    step: int
    tags: _containers.RepeatedScalarFieldContainer[str]
    expected_size: int
    def __init__(self, task_type: _Optional[str] = ..., task_name: _Optional[str] = ..., task_index: _Optional[_Union[_common_pb2.TaskIndex, _Mapping]] = ..., env_type: _Optional[str] = ..., parent_id: _Optional[str] = ..., session_id: _Optional[int] = ..., step: _Optional[int] = ..., tags: _Optional[_Iterable[str]] = ..., expected_size: _Optional[int] = ...) -> None: ...

class CreateSnapshotResponse(_message.Message):
    __slots__ = ("id", "path")
    ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    id: str
    path: str
    def __init__(self, id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class MarkReadyRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListSnapshotsRequest(_message.Message):
    __slots__ = ("task_type", "task_name", "task_index", "env_type", "parent_id", "session_id", "step", "tags", "page_size", "page_token")
    TASK_TYPE_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_INDEX_FIELD_NUMBER: _ClassVar[int]
    ENV_TYPE_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    task_type: str
    task_name: str
    task_index: _common_pb2.TaskIndex
    env_type: str
    parent_id: str
    session_id: int
    step: int
    tags: _containers.RepeatedScalarFieldContainer[str]
    page_size: int
    page_token: str
    def __init__(self, task_type: _Optional[str] = ..., task_name: _Optional[str] = ..., task_index: _Optional[_Union[_common_pb2.TaskIndex, _Mapping]] = ..., env_type: _Optional[str] = ..., parent_id: _Optional[str] = ..., session_id: _Optional[int] = ..., step: _Optional[int] = ..., tags: _Optional[_Iterable[str]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListSnapshotsResponse(_message.Message):
    __slots__ = ("snapshots", "previous_page_token", "next_page_token")
    SNAPSHOTS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    snapshots: _containers.RepeatedCompositeFieldContainer[Snapshot]
    previous_page_token: str
    next_page_token: str
    def __init__(self, snapshots: _Optional[_Iterable[_Union[Snapshot, _Mapping]]] = ..., previous_page_token: _Optional[str] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetSnapshotRequest(_message.Message):
    __slots__ = ("id", "require_path")
    ID_FIELD_NUMBER: _ClassVar[int]
    REQUIRE_PATH_FIELD_NUMBER: _ClassVar[int]
    id: str
    require_path: bool
    def __init__(self, id: _Optional[str] = ..., require_path: bool = ...) -> None: ...

class GetSnapshotResponse(_message.Message):
    __slots__ = ("snapshot", "path")
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    snapshot: Snapshot
    path: str
    def __init__(self, snapshot: _Optional[_Union[Snapshot, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DeleteSnapshotRequest(_message.Message):
    __slots__ = ("id", "propagate")
    ID_FIELD_NUMBER: _ClassVar[int]
    PROPAGATE_FIELD_NUMBER: _ClassVar[int]
    id: str
    propagate: bool
    def __init__(self, id: _Optional[str] = ..., propagate: bool = ...) -> None: ...

class AddSnapshotTagsRequest(_message.Message):
    __slots__ = ("id", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveSnapshotTagsRequest(_message.Message):
    __slots__ = ("id", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class SetSnapshotTagsRequest(_message.Message):
    __slots__ = ("id", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class StreamArchiveRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ArchiveChunk(_message.Message):
    __slots__ = ("data", "eof")
    class EOF(_message.Message):
        __slots__ = ("total_size", "sha256_tar")
        TOTAL_SIZE_FIELD_NUMBER: _ClassVar[int]
        SHA256_TAR_FIELD_NUMBER: _ClassVar[int]
        total_size: int
        sha256_tar: str
        def __init__(self, total_size: _Optional[int] = ..., sha256_tar: _Optional[str] = ...) -> None: ...
    DATA_FIELD_NUMBER: _ClassVar[int]
    EOF_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    eof: ArchiveChunk.EOF
    def __init__(self, data: _Optional[bytes] = ..., eof: _Optional[_Union[ArchiveChunk.EOF, _Mapping]] = ...) -> None: ...
