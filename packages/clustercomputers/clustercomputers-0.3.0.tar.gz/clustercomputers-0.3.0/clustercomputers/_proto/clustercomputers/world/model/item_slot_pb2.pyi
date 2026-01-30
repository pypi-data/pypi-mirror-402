from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_slot_index_pb2 as _item_slot_index_pb2
from clustercomputers._proto.clustercomputers.world.model import item_stack_pb2 as _item_stack_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ItemSlot(_message.Message):
    __slots__ = ("index", "stack")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    STACK_FIELD_NUMBER: _ClassVar[int]
    index: _item_slot_index_pb2.ItemSlotIndex
    stack: _item_stack_pb2.ItemStack
    def __init__(self, index: _Optional[_Union[_item_slot_index_pb2.ItemSlotIndex, _Mapping]] = ..., stack: _Optional[_Union[_item_stack_pb2.ItemStack, _Mapping]] = ...) -> None: ...
