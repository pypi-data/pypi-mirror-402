from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import item_stack_pb2 as _item_stack_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Inventory(_message.Message):
    __slots__ = ("item_stacks",)
    ITEM_STACKS_FIELD_NUMBER: _ClassVar[int]
    item_stacks: _containers.RepeatedCompositeFieldContainer[_item_stack_pb2.ItemStack]
    def __init__(self, item_stacks: _Optional[_Iterable[_Union[_item_stack_pb2.ItemStack, _Mapping]]] = ...) -> None: ...
