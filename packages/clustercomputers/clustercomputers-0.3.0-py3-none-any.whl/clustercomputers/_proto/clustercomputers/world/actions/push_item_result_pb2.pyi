from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_pb2 as _item_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PushItemResult(_message.Message):
    __slots__ = ("item", "remaining", "pushed")
    ITEM_FIELD_NUMBER: _ClassVar[int]
    REMAINING_FIELD_NUMBER: _ClassVar[int]
    PUSHED_FIELD_NUMBER: _ClassVar[int]
    item: _item_pb2.Item
    remaining: int
    pushed: int
    def __init__(self, item: _Optional[_Union[_item_pb2.Item, _Mapping]] = ..., remaining: _Optional[int] = ..., pushed: _Optional[int] = ...) -> None: ...
