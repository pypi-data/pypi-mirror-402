from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import drop_item_pb2 as _drop_item_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_inventory_pb2 as _get_inventory_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_location_pb2 as _get_location_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_redstone_inputs_pb2 as _get_redstone_inputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_redstone_outputs_pb2 as _get_redstone_outputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import merge_item_pb2 as _merge_item_pb2
from clustercomputers._proto.clustercomputers.world.actions import push_item_pb2 as _push_item_pb2
from clustercomputers._proto.clustercomputers.world.actions import ring_bell_pb2 as _ring_bell_pb2
from clustercomputers._proto.clustercomputers.world.actions import set_all_redstone_outputs_pb2 as _set_all_redstone_outputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import set_redstone_output_pb2 as _set_redstone_output_pb2
from clustercomputers._proto.clustercomputers.world.actions import sleep_pb2 as _sleep_pb2
from clustercomputers._proto.clustercomputers.world.actions import swap_item_pb2 as _swap_item_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldPayload(_message.Message):
    __slots__ = ("get_location", "get_redstone_inputs", "get_redstone_outputs", "ring_bell", "set_all_redstone_outputs", "set_redstone_output", "sleep", "get_inventory", "drop_item", "merge_item", "push_item", "swap_item")
    GET_LOCATION_FIELD_NUMBER: _ClassVar[int]
    GET_REDSTONE_INPUTS_FIELD_NUMBER: _ClassVar[int]
    GET_REDSTONE_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    RING_BELL_FIELD_NUMBER: _ClassVar[int]
    SET_ALL_REDSTONE_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    SET_REDSTONE_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    SLEEP_FIELD_NUMBER: _ClassVar[int]
    GET_INVENTORY_FIELD_NUMBER: _ClassVar[int]
    DROP_ITEM_FIELD_NUMBER: _ClassVar[int]
    MERGE_ITEM_FIELD_NUMBER: _ClassVar[int]
    PUSH_ITEM_FIELD_NUMBER: _ClassVar[int]
    SWAP_ITEM_FIELD_NUMBER: _ClassVar[int]
    get_location: _get_location_pb2.GetLocation
    get_redstone_inputs: _get_redstone_inputs_pb2.GetRedstoneInputs
    get_redstone_outputs: _get_redstone_outputs_pb2.GetRedstoneOutputs
    ring_bell: _ring_bell_pb2.RingBell
    set_all_redstone_outputs: _set_all_redstone_outputs_pb2.SetAllRedstoneOutputs
    set_redstone_output: _set_redstone_output_pb2.SetRedstoneOutput
    sleep: _sleep_pb2.Sleep
    get_inventory: _get_inventory_pb2.GetInventory
    drop_item: _drop_item_pb2.DropItem
    merge_item: _merge_item_pb2.MergeItem
    push_item: _push_item_pb2.PushItem
    swap_item: _swap_item_pb2.SwapItem
    def __init__(self, get_location: _Optional[_Union[_get_location_pb2.GetLocation, _Mapping]] = ..., get_redstone_inputs: _Optional[_Union[_get_redstone_inputs_pb2.GetRedstoneInputs, _Mapping]] = ..., get_redstone_outputs: _Optional[_Union[_get_redstone_outputs_pb2.GetRedstoneOutputs, _Mapping]] = ..., ring_bell: _Optional[_Union[_ring_bell_pb2.RingBell, _Mapping]] = ..., set_all_redstone_outputs: _Optional[_Union[_set_all_redstone_outputs_pb2.SetAllRedstoneOutputs, _Mapping]] = ..., set_redstone_output: _Optional[_Union[_set_redstone_output_pb2.SetRedstoneOutput, _Mapping]] = ..., sleep: _Optional[_Union[_sleep_pb2.Sleep, _Mapping]] = ..., get_inventory: _Optional[_Union[_get_inventory_pb2.GetInventory, _Mapping]] = ..., drop_item: _Optional[_Union[_drop_item_pb2.DropItem, _Mapping]] = ..., merge_item: _Optional[_Union[_merge_item_pb2.MergeItem, _Mapping]] = ..., push_item: _Optional[_Union[_push_item_pb2.PushItem, _Mapping]] = ..., swap_item: _Optional[_Union[_swap_item_pb2.SwapItem, _Mapping]] = ...) -> None: ...
