from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import food_properties_pb2 as _food_properties_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Item(_message.Message):
    __slots__ = ("id", "nbt", "tags", "max_stack_size", "max_durability", "use_duration_ticks", "food")
    ID_FIELD_NUMBER: _ClassVar[int]
    NBT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    MAX_STACK_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_DURABILITY_FIELD_NUMBER: _ClassVar[int]
    USE_DURATION_TICKS_FIELD_NUMBER: _ClassVar[int]
    FOOD_FIELD_NUMBER: _ClassVar[int]
    id: str
    nbt: _struct_pb2.Struct
    tags: _containers.RepeatedScalarFieldContainer[str]
    max_stack_size: int
    max_durability: int
    use_duration_ticks: int
    food: _food_properties_pb2.FoodProperties
    def __init__(self, id: _Optional[str] = ..., nbt: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., max_stack_size: _Optional[int] = ..., max_durability: _Optional[int] = ..., use_duration_ticks: _Optional[int] = ..., food: _Optional[_Union[_food_properties_pb2.FoodProperties, _Mapping]] = ...) -> None: ...
