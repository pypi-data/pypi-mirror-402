from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import block_side_pb2 as _block_side_pb2
from clustercomputers._proto.clustercomputers.world.model import item_slot_index_pb2 as _item_slot_index_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DropItem(_message.Message):
    __slots__ = ("index", "side", "count")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    index: _item_slot_index_pb2.ItemSlotIndex
    side: _block_side_pb2.BlockSide
    count: int
    def __init__(self, index: _Optional[_Union[_item_slot_index_pb2.ItemSlotIndex, _Mapping]] = ..., side: _Optional[_Union[_block_side_pb2.BlockSide, str]] = ..., count: _Optional[int] = ...) -> None: ...
