from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import drop_item_result_pb2 as _drop_item_result_pb2
from clustercomputers._proto.clustercomputers.world.actions import merge_item_result_pb2 as _merge_item_result_pb2
from clustercomputers._proto.clustercomputers.world.actions import push_item_result_pb2 as _push_item_result_pb2
from clustercomputers._proto.clustercomputers.world.actions import swap_item_result_pb2 as _swap_item_result_pb2
from clustercomputers._proto.clustercomputers.world.model import block_location_pb2 as _block_location_pb2
from clustercomputers._proto.clustercomputers.world.model import inventory_pb2 as _inventory_pb2
from clustercomputers._proto.clustercomputers.world.model import redstone_sides_pb2 as _redstone_sides_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldResult(_message.Message):
    __slots__ = ("value", "failure_message")
    class Value(_message.Message):
        __slots__ = ("block_location", "redstone_sides", "inventory", "drop_item_result", "merge_item_result", "push_item_result", "swap_item_result")
        BLOCK_LOCATION_FIELD_NUMBER: _ClassVar[int]
        REDSTONE_SIDES_FIELD_NUMBER: _ClassVar[int]
        INVENTORY_FIELD_NUMBER: _ClassVar[int]
        DROP_ITEM_RESULT_FIELD_NUMBER: _ClassVar[int]
        MERGE_ITEM_RESULT_FIELD_NUMBER: _ClassVar[int]
        PUSH_ITEM_RESULT_FIELD_NUMBER: _ClassVar[int]
        SWAP_ITEM_RESULT_FIELD_NUMBER: _ClassVar[int]
        block_location: _block_location_pb2.BlockLocation
        redstone_sides: _redstone_sides_pb2.RedstoneSides
        inventory: _inventory_pb2.Inventory
        drop_item_result: _drop_item_result_pb2.DropItemResult
        merge_item_result: _merge_item_result_pb2.MergeItemResult
        push_item_result: _push_item_result_pb2.PushItemResult
        swap_item_result: _swap_item_result_pb2.SwapItemResult
        def __init__(self, block_location: _Optional[_Union[_block_location_pb2.BlockLocation, _Mapping]] = ..., redstone_sides: _Optional[_Union[_redstone_sides_pb2.RedstoneSides, _Mapping]] = ..., inventory: _Optional[_Union[_inventory_pb2.Inventory, _Mapping]] = ..., drop_item_result: _Optional[_Union[_drop_item_result_pb2.DropItemResult, _Mapping]] = ..., merge_item_result: _Optional[_Union[_merge_item_result_pb2.MergeItemResult, _Mapping]] = ..., push_item_result: _Optional[_Union[_push_item_result_pb2.PushItemResult, _Mapping]] = ..., swap_item_result: _Optional[_Union[_swap_item_result_pb2.SwapItemResult, _Mapping]] = ...) -> None: ...
    VALUE_FIELD_NUMBER: _ClassVar[int]
    FAILURE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    value: WorldResult.Value
    failure_message: str
    def __init__(self, value: _Optional[_Union[WorldResult.Value, _Mapping]] = ..., failure_message: _Optional[str] = ...) -> None: ...
