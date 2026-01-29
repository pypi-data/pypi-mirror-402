from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RoomFlags(_message.Message):
    __slots__ = ("data_app_enabled",)
    DATA_APP_ENABLED_FIELD_NUMBER: _ClassVar[int]
    data_app_enabled: bool
    def __init__(self, data_app_enabled: bool = ...) -> None: ...
