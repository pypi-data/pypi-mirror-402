from buf.validate import validate_pb2 as _validate_pb2
from corvic_generated.validate.v1 import predefined_string_rules_pb2 as _predefined_string_rules_pb2
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RoomFlags(_message.Message):
    __slots__ = ("data_app_enabled",)
    DATA_APP_ENABLED_FIELD_NUMBER: _ClassVar[int]
    data_app_enabled: bool
    def __init__(self, data_app_enabled: bool = ...) -> None: ...

class RoomEntry(_message.Message):
    __slots__ = ("id", "name", "user_id", "org_id", "flags", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    user_id: str
    org_id: str
    flags: RoomFlags
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., user_id: _Optional[str] = ..., org_id: _Optional[str] = ..., flags: _Optional[_Union[RoomFlags, _Mapping]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateRoomRequest(_message.Message):
    __slots__ = ("name", "user_id", "org_id")
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    name: str
    user_id: str
    org_id: str
    def __init__(self, name: _Optional[str] = ..., user_id: _Optional[str] = ..., org_id: _Optional[str] = ...) -> None: ...

class CreateRoomResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: RoomEntry
    def __init__(self, entry: _Optional[_Union[RoomEntry, _Mapping]] = ...) -> None: ...

class DeleteRoomRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteRoomResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetRoomRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetRoomResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: RoomEntry
    def __init__(self, entry: _Optional[_Union[RoomEntry, _Mapping]] = ...) -> None: ...

class ListRoomsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListRoomsResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: RoomEntry
    def __init__(self, entry: _Optional[_Union[RoomEntry, _Mapping]] = ...) -> None: ...

class ListRoomsPaginatedCursorPayload(_message.Message):
    __slots__ = ("create_time_of_last_entry",)
    CREATE_TIME_OF_LAST_ENTRY_FIELD_NUMBER: _ClassVar[int]
    create_time_of_last_entry: _timestamp_pb2.Timestamp
    def __init__(self, create_time_of_last_entry: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ListRoomsPaginatedRequest(_message.Message):
    __slots__ = ("entries_per_page", "cursor")
    ENTRIES_PER_PAGE_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    entries_per_page: int
    cursor: str
    def __init__(self, entries_per_page: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListRoomsPaginatedResponse(_message.Message):
    __slots__ = ("entry", "cursor")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    entry: _containers.RepeatedCompositeFieldContainer[RoomEntry]
    cursor: str
    def __init__(self, entry: _Optional[_Iterable[_Union[RoomEntry, _Mapping]]] = ..., cursor: _Optional[str] = ...) -> None: ...

class PurgeRoomRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class PurgeRoomResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PatchRoomRequest(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class PatchRoomResponse(_message.Message):
    __slots__ = ("room_entry",)
    ROOM_ENTRY_FIELD_NUMBER: _ClassVar[int]
    room_entry: RoomEntry
    def __init__(self, room_entry: _Optional[_Union[RoomEntry, _Mapping]] = ...) -> None: ...
