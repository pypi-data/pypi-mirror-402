from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_pb2 as _item_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ItemStack(_message.Message):
    __slots__ = ("count", "item")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    count: int
    item: _item_pb2.Item
    def __init__(self, count: _Optional[int] = ..., item: _Optional[_Union[_item_pb2.Item, _Mapping]] = ...) -> None: ...
