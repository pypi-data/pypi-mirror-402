from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class FoodProperties(_message.Message):
    __slots__ = ("hunger", "saturation", "can_always_eat", "meat")
    HUNGER_FIELD_NUMBER: _ClassVar[int]
    SATURATION_FIELD_NUMBER: _ClassVar[int]
    CAN_ALWAYS_EAT_FIELD_NUMBER: _ClassVar[int]
    MEAT_FIELD_NUMBER: _ClassVar[int]
    hunger: int
    saturation: float
    can_always_eat: bool
    meat: bool
    def __init__(self, hunger: _Optional[int] = ..., saturation: _Optional[float] = ..., can_always_eat: bool = ..., meat: bool = ...) -> None: ...
