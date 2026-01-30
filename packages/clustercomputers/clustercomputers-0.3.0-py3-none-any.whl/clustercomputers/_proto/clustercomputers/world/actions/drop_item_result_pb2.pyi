from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_pb2 as _item_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DropItemResult(_message.Message):
    __slots__ = ("item", "remaining", "dropped")
    ITEM_FIELD_NUMBER: _ClassVar[int]
    REMAINING_FIELD_NUMBER: _ClassVar[int]
    DROPPED_FIELD_NUMBER: _ClassVar[int]
    item: _item_pb2.Item
    remaining: int
    dropped: int
    def __init__(self, item: _Optional[_Union[_item_pb2.Item, _Mapping]] = ..., remaining: _Optional[int] = ..., dropped: _Optional[int] = ...) -> None: ...
