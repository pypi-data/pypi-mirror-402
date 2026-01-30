__all__ = (
    "BlockLocation",
    "BlockLocation",
    "BlockPosition",
    "BlockSide",
    "CardinalDirection",
    "DropItemResult",
    "FoodProperties",
    "Item",
    "ItemSlot",
    "ItemStack",
    "MergeItemResult",
    "PushItemResult",
    "RedstoneSides",
    "SideRedstoneSignal",
    "SwapItemResult",
    "WorldActionId",
)

import dataclasses
import enum
from collections.abc import Iterable, Iterator
from typing import Any

from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict

from ._proto.clustercomputers.world.actions import (
    drop_item_result_pb2,
    merge_item_result_pb2,
    push_item_result_pb2,
    swap_item_result_pb2,
    world_action_id_pb2,
)
from ._proto.clustercomputers.world.model import (
    block_location_pb2,
    block_position_pb2,
    block_side_pb2,
    cardinal_direction_pb2,
    food_properties_pb2,
    inventory_pb2,
    item_pb2,
    item_slot_pb2,
    item_stack_pb2,
    redstone_sides_pb2,
    redstone_signal_pb2,
    side_redstone_signal_pb2,
)


def _struct_to_dict(struct: struct_pb2.Struct) -> dict[str, Any]:
    """Converts a protobuf Struct to a JSONable dict"""
    return MessageToDict(struct)


@dataclasses.dataclass(frozen=True)
class BlockPosition:
    """Coordinates of a block in the world"""

    x: int
    y: int
    z: int

    @staticmethod
    def _from_proto(
        proto: block_position_pb2.BlockPosition,
    ) -> "BlockPosition":
        return BlockPosition(x=proto.x, y=proto.y, z=proto.z)


class BlockSide(enum.Enum):
    """Relative sides of a block"""

    FRONT = enum.auto()
    BACK = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    TOP = enum.auto()
    BOTTOM = enum.auto()

    @staticmethod
    def _from_proto(proto: block_side_pb2.BlockSide) -> "BlockSide":
        match proto:
            case block_side_pb2.BLOCK_SIDE_FRONT:
                return BlockSide.FRONT
            case block_side_pb2.BLOCK_SIDE_BACK:
                return BlockSide.BACK
            case block_side_pb2.BLOCK_SIDE_LEFT:
                return BlockSide.LEFT
            case block_side_pb2.BLOCK_SIDE_RIGHT:
                return BlockSide.RIGHT
            case block_side_pb2.BLOCK_SIDE_TOP:
                return BlockSide.TOP
            case block_side_pb2.BLOCK_SIDE_BOTTOM:
                return BlockSide.BOTTOM
            case _:
                raise ValueError(proto)

    def _to_proto(self) -> block_side_pb2.BlockSide:
        match self:
            case BlockSide.FRONT:
                return block_side_pb2.BLOCK_SIDE_FRONT
            case BlockSide.BACK:
                return block_side_pb2.BLOCK_SIDE_BACK
            case BlockSide.LEFT:
                return block_side_pb2.BLOCK_SIDE_LEFT
            case BlockSide.RIGHT:
                return block_side_pb2.BLOCK_SIDE_RIGHT
            case BlockSide.TOP:
                return block_side_pb2.BLOCK_SIDE_TOP
            case BlockSide.BOTTOM:
                return block_side_pb2.BLOCK_SIDE_BOTTOM


class CardinalDirection(enum.Enum):
    """Cardinal directions"""

    NORTH = enum.auto()
    SOUTH = enum.auto()
    EAST = enum.auto()
    WEST = enum.auto()

    @staticmethod
    def _from_proto(
        proto: cardinal_direction_pb2.CardinalDirection,
    ) -> "CardinalDirection":
        match proto:
            case cardinal_direction_pb2.CARDINAL_DIRECTION_NORTH:
                return CardinalDirection.NORTH
            case cardinal_direction_pb2.CARDINAL_DIRECTION_SOUTH:
                return CardinalDirection.SOUTH
            case cardinal_direction_pb2.CARDINAL_DIRECTION_EAST:
                return CardinalDirection.EAST
            case cardinal_direction_pb2.CARDINAL_DIRECTION_WEST:
                return CardinalDirection.WEST
            case _:
                raise ValueError(proto)


@dataclasses.dataclass(frozen=True)
class BlockLocation:
    """Location info of a block in the world"""

    dimension: str
    """Dimension, e.g. *minecraft:overworld*"""
    position: BlockPosition
    """Coordinates"""
    facing: CardinalDirection
    """Direction the block is facing"""

    @staticmethod
    def _from_proto(
        proto: block_location_pb2.BlockLocation,
    ) -> "BlockLocation":
        return BlockLocation(
            dimension=proto.dimension,
            position=BlockPosition._from_proto(proto.position),
            facing=CardinalDirection._from_proto(proto.facing),
        )


@dataclasses.dataclass(frozen=True)
class SideRedstoneSignal:
    """Redstone signal on the side of a block

    This can be used for both the *input* (signal received by the block)
    and the *output* (signal emitted by the block)
    """

    side: BlockSide
    strength: int

    @staticmethod
    def _from_proto(
        proto: side_redstone_signal_pb2.SideRedstoneSignal,
    ) -> "SideRedstoneSignal":
        return SideRedstoneSignal(
            side=BlockSide._from_proto(proto.side),
            strength=proto.signal.strength,
        )

    def _to_proto(self) -> side_redstone_signal_pb2.SideRedstoneSignal:
        return side_redstone_signal_pb2.SideRedstoneSignal(
            side=self.side._to_proto(),
            signal=redstone_signal_pb2.RedstoneSignal(strength=self.strength),
        )


@dataclasses.dataclass(frozen=True)
class RedstoneSides(Iterable[SideRedstoneSignal]):
    """Redstone signal on all sides of a block

    This can be used for both the *inputs* (signals received by the
    block) and the *outputs* (signals emitted by the block)
    """

    front: int = 0
    back: int = 0
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0

    @staticmethod
    def with_all(strength: int) -> "RedstoneSides":
        """Returns RedstoneSides with the same ``strength`` set on all
        sides"""
        return RedstoneSides(
            strength, strength, strength, strength, strength, strength
        )

    def side(self, side: BlockSide) -> int:
        """Returns the signal strength of the ``side``"""
        match side:
            case BlockSide.FRONT:
                return self.front
            case BlockSide.BACK:
                return self.back
            case BlockSide.LEFT:
                return self.left
            case BlockSide.RIGHT:
                return self.right
            case BlockSide.TOP:
                return self.top
            case BlockSide.BOTTOM:
                return self.bottom

    def __iter__(self) -> Iterator[SideRedstoneSignal]:
        """Iterates over all sides"""
        return iter(
            (
                SideRedstoneSignal(BlockSide.FRONT, self.front),
                SideRedstoneSignal(BlockSide.BACK, self.back),
                SideRedstoneSignal(BlockSide.LEFT, self.left),
                SideRedstoneSignal(BlockSide.RIGHT, self.right),
                SideRedstoneSignal(BlockSide.TOP, self.top),
                SideRedstoneSignal(BlockSide.BOTTOM, self.bottom),
            )
        )

    @staticmethod
    def _from_proto(
        proto: redstone_sides_pb2.RedstoneSides,
    ) -> "RedstoneSides":
        return RedstoneSides(
            front=proto.front.strength,
            back=proto.back.strength,
            left=proto.left.strength,
            right=proto.right.strength,
            top=proto.top.strength,
            bottom=proto.bottom.strength,
        )

    def _to_proto(self) -> redstone_sides_pb2.RedstoneSides:
        return redstone_sides_pb2.RedstoneSides(
            front=redstone_signal_pb2.RedstoneSignal(strength=self.front),
            back=redstone_signal_pb2.RedstoneSignal(strength=self.back),
            left=redstone_signal_pb2.RedstoneSignal(strength=self.left),
            right=redstone_signal_pb2.RedstoneSignal(strength=self.right),
            top=redstone_signal_pb2.RedstoneSignal(strength=self.top),
            bottom=redstone_signal_pb2.RedstoneSignal(strength=self.bottom),
        )


@dataclasses.dataclass(frozen=True)
class FoodProperties:
    hunger: int
    """Number of hunger points that the food restores"""

    saturation: float
    """Amount of saturation that the food restores"""

    can_always_eat: bool
    """Whether the item can be eaten even when the player is at full
    hunger"""

    meat: bool
    """Whether the item is meat

    Meat can be fed to wolves.
    """

    @staticmethod
    def _from_proto(
        proto: food_properties_pb2.FoodProperties,
    ) -> "FoodProperties":
        return FoodProperties(
            hunger=proto.hunger,
            saturation=proto.saturation,
            can_always_eat=proto.can_always_eat,
            meat=proto.meat,
        )


@dataclasses.dataclass(frozen=True)
class Item:
    """Item that can be stored in an :class:`ItemStack`"""

    id: str
    """Unique identifer, e.g. ``minecraft:oak_log``"""

    nbt: dict[str, Any]
    """NBT tags

    This contains various metadata about the item, such as damage values
    and enchancements.

    This may be empty if the item doesn't have any NBT tags.
    """

    tags: frozenset[str]
    """Set of item tags (groups) that the item is contained in

    This may be empty if the item doesn't have any tags.
    """

    max_stack_size: int
    """Max number of items that can fit in a stack

    This is 64 for most items, but it may be smaller.
    """

    max_durability: int
    """Max damage that the item can take before breaking

    This will be ``0`` if the item doesn't use durability.

    The current damage value can be obtained from the ``Damage`` NBT
    integer tag. Once the damage value reaches the max durability, the
    item will break.

    Items that normally use durability can also have an ``Unbreakable``
    NBT boolean tag. Unbreakable items will not lose durability.
    """

    use_duration_ticks: int
    """Number of game ticks that it takes to use the item when the
    player right-clicks

    For food, this is the amount of time that it takes to eat the item.

    If this is ``0``, the item either can't be used, or it activates
    instantly when right-clicked.
    """

    food: FoodProperties | None
    """Food properties, or ``None`` if the item isn't edible"""

    @staticmethod
    def _from_proto(proto: item_pb2.Item) -> "Item":
        return Item(
            id=proto.id,
            nbt=_struct_to_dict(proto.nbt),
            tags=frozenset(proto.tags),
            max_stack_size=proto.max_stack_size,
            max_durability=proto.max_durability,
            use_duration_ticks=proto.use_duration_ticks,
            food=(
                FoodProperties._from_proto(proto.food)
                if proto.HasField("food")
                else None
            ),
        )


@dataclasses.dataclass(frozen=True)
class ItemStack:
    """Stack of zero or more :class:`items <Item>`"""

    count: int
    """Number of items in the stack

    This may be ``0`` if the stack is empty.

    The max stack size can be obtained via :attr:`Item.max_stack_size`.
    """

    item: Item | None
    """Item in this stack, or ``None`` if the stack is empty"""

    def to_slot(self, index: int) -> "ItemSlot":
        """Converts this ItemStack to an ItemSlot that has an index"""
        return ItemSlot(index, self.count, self.item)

    def __len__(self) -> int:
        """Returns the number of items in this stack"""
        return self.count

    @staticmethod
    def _from_proto(proto: item_stack_pb2.ItemStack) -> "ItemStack":
        return ItemStack(
            count=proto.count,
            item=(
                Item._from_proto(proto.item)
                if proto.HasField("item")
                else None
            ),
        )


@dataclasses.dataclass(frozen=True)
class ItemSlot:
    """:class:`ItemStack` that is contained in a slot in the computer's
    inventory

    This is the same as ItemStack, except it also has an index
    indicating its position in the inventory.
    """

    index: int
    """Position in the computer's inventory

    Computers have 9 slots, so this a value between ``0-8``, inclusive.
    """

    count: int
    """Number of items in the slot

    This may be ``0`` if the slot is empty.

    The max stack size can be obtained via :attr:`Item.max_stack_size`.
    """

    item: Item | None
    """Item in this slot, or ``None`` if the slot is empty"""

    def to_stack(self) -> ItemStack:
        """Converts this ItemSlot to an ItemStack without an index"""
        return ItemStack(self.count, self.item)

    def __len__(self) -> int:
        """Returns the number of items in this slot"""
        return self.count

    @staticmethod
    def _from_proto(proto: item_slot_pb2.ItemSlot) -> "ItemSlot":
        return ItemSlot(
            index=proto.index.index,
            count=proto.stack.count,
            item=(
                Item._from_proto(proto.stack.item)
                if proto.stack.HasField("item")
                else None
            ),
        )


@dataclasses.dataclass(frozen=True)
class _Inventory:
    """WorldResult value returned by a GetInventory payload"""

    slots: tuple[ItemSlot, ...]

    @staticmethod
    def _from_proto(proto: inventory_pb2.Inventory) -> "_Inventory":
        return _Inventory(
            slots=tuple(
                ItemStack._from_proto(stack).to_slot(i)
                for i, stack in enumerate(proto.item_stacks)
            )
        )


@dataclasses.dataclass(frozen=True)
class DropItemResult:
    """Result when an item is dropped from the computer's inventory onto
    the ground"""

    item: Item | None
    """Item that was dropped, or ``None`` if the slot was empty"""

    remaining: int
    """Number of items remaining in the slot"""

    dropped: int
    """Number of items that were dropped"""

    @staticmethod
    def _from_proto(
        proto: drop_item_result_pb2.DropItemResult,
    ) -> "DropItemResult":
        return DropItemResult(
            item=(
                Item._from_proto(proto.item)
                if proto.HasField("item")
                else None
            ),
            remaining=proto.remaining,
            dropped=proto.dropped,
        )


@dataclasses.dataclass(frozen=True)
class PushItemResult:
    """Result when an item is pushed from the computer's inventory into
    another container"""

    item: Item | None
    """Item that was pushed, or ``None`` if the slot was empty"""

    remaining: int
    """Number of items remaining in the slot"""

    pushed: int
    """Number of items that were pushed"""

    @staticmethod
    def _from_proto(
        proto: push_item_result_pb2.PushItemResult,
    ) -> "PushItemResult":
        return PushItemResult(
            item=(
                Item._from_proto(proto.item)
                if proto.HasField("item")
                else None
            ),
            remaining=proto.remaining,
            pushed=proto.pushed,
        )


@dataclasses.dataclass(frozen=True)
class SwapItemResult:
    """Result when two items are swapped within the computer's
    inventory"""

    source: ItemStack
    """Item stack in the source slot after the swap. May be empty"""

    dest: ItemStack
    """Item stack in the destination slot after the swap. May be
    empty"""

    @staticmethod
    def _from_proto(
        proto: swap_item_result_pb2.SwapItemResult,
    ) -> "SwapItemResult":
        return SwapItemResult(
            source=ItemStack._from_proto(proto.source),
            dest=ItemStack._from_proto(proto.dest),
        )


@dataclasses.dataclass(frozen=True)
class MergeItemResult:
    """Result when an item is merged into another slot within the
    computer's inventory"""

    source_item: Item | None
    """Item remaining in the source slot after the merge, or ``None`` if
    the slot is empty"""

    dest_item: Item | None
    """Item in the destination slot after the merge, or ``None`` if the
    slot is empty"""

    source_count: int
    """Number of items in the source slot after the merge"""

    dest_count: int
    """Number of items in the destination slot after the merge"""

    merged: int
    """Number of items that were merged from the source slot to the
    destination slot"""

    @staticmethod
    def _from_proto(
        proto: merge_item_result_pb2.MergeItemResult,
    ) -> "MergeItemResult":
        return MergeItemResult(
            source_item=(
                Item._from_proto(proto.source_item)
                if proto.HasField("source_item")
                else None
            ),
            dest_item=(
                Item._from_proto(proto.dest_item)
                if proto.HasField("dest_item")
                else None
            ),
            source_count=proto.source_count,
            dest_count=proto.dest_count,
            merged=proto.merged,
        )


@dataclasses.dataclass(frozen=True)
class WorldActionId:
    """ID of a WorldAction that was submitted to the Minecraft server

    This is normally handled internally by the clients, but it's
    included in logs and exceptions to help with troubleshooting.
    """

    id: int

    @staticmethod
    def _from_proto(
        proto: world_action_id_pb2.WorldActionId,
    ) -> "WorldActionId":
        return WorldActionId(id=proto.id)

    def _to_proto(self) -> world_action_id_pb2.WorldActionId:
        return world_action_id_pb2.WorldActionId(id=self.id)


type _WorldResultValue = (
    BlockLocation
    | RedstoneSides
    | _Inventory
    | DropItemResult
    | MergeItemResult
    | PushItemResult
    | SwapItemResult
    | None
)
"""Union of possible value types in a successful WorldResult"""


class _WorldResultValueType(enum.Enum):
    """Enum of WorldResultValue types with their field name"""

    NO_VALUE = None
    BLOCK_LOCATION = "block_location"
    REDSTONE_SIDES = "redstone_sides"
    INVENTORY = "inventory"
    DROP_ITEM_RESULT = "drop_item_result"
    MERGE_ITEM_RESULT = "merge_item_result"
    PUSH_ITEM_RESULT = "push_item_result"
    SWAP_ITEM_RESULT = "swap_item_result"

    field_name: str | None
    """Name of the protobuf field in ``WorldResult.Value``, or ``None``
    if the result should have no return value"""

    def __init__(self, field_name: str | None) -> None:
        self.field_name = field_name
