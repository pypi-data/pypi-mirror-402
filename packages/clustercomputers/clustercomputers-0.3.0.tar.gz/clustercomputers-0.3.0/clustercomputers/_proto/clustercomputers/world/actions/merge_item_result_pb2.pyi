from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_pb2 as _item_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MergeItemResult(_message.Message):
    __slots__ = ("source_item", "dest_item", "source_count", "dest_count", "merged")
    SOURCE_ITEM_FIELD_NUMBER: _ClassVar[int]
    DEST_ITEM_FIELD_NUMBER: _ClassVar[int]
    SOURCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    DEST_COUNT_FIELD_NUMBER: _ClassVar[int]
    MERGED_FIELD_NUMBER: _ClassVar[int]
    source_item: _item_pb2.Item
    dest_item: _item_pb2.Item
    source_count: int
    dest_count: int
    merged: int
    def __init__(self, source_item: _Optional[_Union[_item_pb2.Item, _Mapping]] = ..., dest_item: _Optional[_Union[_item_pb2.Item, _Mapping]] = ..., source_count: _Optional[int] = ..., dest_count: _Optional[int] = ..., merged: _Optional[int] = ...) -> None: ...
