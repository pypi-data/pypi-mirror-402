__all__ = (
    "AsyncBatchItemService",
    "AsyncItemService",
    "SyncBatchItemService",
    "SyncItemService",
)

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING

from ._proto.clustercomputers.world.actions.drop_item_pb2 import (
    DropItem as pb_DropItem,
)
from ._proto.clustercomputers.world.actions.get_inventory_pb2 import (
    GetInventory as pb_GetInventory,
)
from ._proto.clustercomputers.world.actions.merge_item_pb2 import (
    MergeItem as pb_MergeItem,
)
from ._proto.clustercomputers.world.actions.push_item_pb2 import (
    PushItem as pb_PushItem,
)
from ._proto.clustercomputers.world.actions.swap_item_pb2 import (
    SwapItem as pb_SwapItem,
)
from ._proto.clustercomputers.world.actions.world_payload_pb2 import (
    WorldPayload as pb_WorldPayload,
)
from ._proto.clustercomputers.world.model.item_slot_index_pb2 import (
    ItemSlotIndex as pb_ItemSlotIndex,
)
from ._proto.clustercomputers.world.subscriptions.world_subscription_pb2 import (
    WorldSubscription as pb_WorldSubscription,
)
from ._util import check_world_sub_type
from .world import (
    BlockSide,
    DropItemResult,
    ItemSlot,
    MergeItemResult,
    PushItemResult,
    SwapItemResult,
    _Inventory,
    _WorldResultValueType,
)

if TYPE_CHECKING:
    from .aclient import AsyncBatch, AsyncBatchFuture, AsyncClient
    from .sclient import SyncBatch, SyncBatchFuture, SyncClient


def _transform_inventory_result(result: _Inventory) -> tuple[ItemSlot, ...]:
    return result.slots


class SyncItemService:
    """Sync service that can be used to interact with the computer's
    inventory

    This class should not be created directly. Use
    :attr:`SyncClient.item`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "SyncClient") -> None:
        self._client = _client

    def get(self) -> tuple[ItemSlot, ...]:
        """Gets all item slots in the computer's inventory

        The slots will be returned in order. Slots may be empty.

        To monitor changes to the inventory in real time, use
        :meth:`subscribe_updates`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(get_inventory=pb_GetInventory())
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.INVENTORY, payload
        )
        assert isinstance(result, _Inventory)
        return _transform_inventory_result(result)

    def drop(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> DropItemResult:
        """Drops an item stack from the computer's inventory onto the
        ground

        To push an item into an adjacent container instead of dropping
        it, use :meth:`push`.

        :param slot: index of the slot, between 0 to 8
        :param side: side to drop the item from
        :param count: number of items to drop. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be dropped. Must be at least 1

        :raises WorldActionFailedError: if ``slot`` is greater than 8
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(
            drop_item=pb_DropItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.DROP_ITEM_RESULT, payload
        )
        assert isinstance(result, DropItemResult)
        return result

    def push(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> PushItemResult:
        """Pushes an item stack from the computer's inventory into an
        adjacent container

        The adjacent container can be either a block (e.g. a chest), or
        an entity (e.g. a minecart with chest). Blocks have priority. If
        multiple entities are adjacent, a random entity will be picked.

        If the stack doesn't fit in the container, any remaining items
        will stay in the computer's inventory.

        To drop an item onto the ground instead of pushing it into a
        container, use :meth:`drop`.

        :param slot: index of the slot, between 0 to 8
        :param side: side to push the item from
        :param count: number of items to push. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be pushed. Must be at least 1

        :raises WorldActionFailedError: if ``slot`` is greater than 8
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(
            push_item=pb_PushItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.PUSH_ITEM_RESULT, payload
        )
        assert isinstance(result, PushItemResult)
        return result

    def swap(self, source: int, dest: int) -> SwapItemResult:
        """Swaps two item stacks within the computer's inventory

        To merge two stacks together instead of swapping them, use
        :meth:`merge`.

        :param source: index of the first slot, between 0 - 8
        :param dest: index of the second slot, between 0 - 8

        :raises WorldActionFailedError: if ``source`` or ``dest`` is
            greater than 8, or if ``source`` and ``dest`` are equal
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(
            swap_item=pb_SwapItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
            )
        )
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.SWAP_ITEM_RESULT, payload
        )
        assert isinstance(result, SwapItemResult)
        return result

    def merge(
        self, source: int, dest: int, count: int | None = None
    ) -> MergeItemResult:
        """Merges an item stack within the computer's inventory into
        another slot

        If the destination slot is empty or contains the same item as
        the source slot, items from the source slot will be merged into
        the destination slot. Otherwise, nothing will happen.

        If the destination slot doesn't have enough space to merge all
        the items, any remaining items will stay in the source slot.

        To swap two stacks completely instead of merging them, use
        :meth:`swap`.

        :param source: index of the slot to merge items from, between
            0 - 8
        :param dest: index of the slot to merge items into, between
            0 - 8
        :param count: number of items to merge. If this is ``None`` or
            is greater than the number of items in the source stack, the
            entire stack will be merged. Must be at least 1

        :raises WorldActionFailedError: if ``source`` or ``dest`` is
            greater than 8, or if ``source`` and ``dest`` are equal
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(
            merge_item=pb_MergeItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
                count=count,
            )
        )
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.MERGE_ITEM_RESULT, payload
        )
        assert isinstance(result, MergeItemResult)
        return result

    def subscribe_updates(self) -> Generator[ItemSlot]:
        """Yields real-time updates whenever the computer's inventory
        changes

        This method will run forever until the generator or client is
        closed.

        To just get the current inventory without real-time updates, use
        :meth:`get`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        subs = (pb_WorldSubscription.WORLD_SUBSCRIPTION_INVENTORY_UPDATE,)
        for update in self._client._subscribe_world_subs(subs):
            check_world_sub_type("inventory_update", update)
            for slot in update.inventory_update.slots:
                yield ItemSlot._from_proto(slot)


class SyncBatchItemService:
    """Sync batch service that can be used to interact with the
    computer's inventory

    This class should not be created directly. Use
    :attr:`SyncBatch.item`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "SyncBatch") -> None:
        self._batch = _batch

    def get(self) -> "SyncBatchFuture[tuple[ItemSlot, ...]]":
        """Gets all item slots in the computer's inventory

        The slots will be returned in order. Slots may be empty.

        To monitor changes to the inventory in real time, use
        :meth:`SyncItemService.subscribe_updates`.
        """
        payload = pb_WorldPayload(get_inventory=pb_GetInventory())
        return self._batch._create_future(
            _WorldResultValueType.INVENTORY,
            payload,
            _transform_inventory_result,
        )

    def drop(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> "SyncBatchFuture[DropItemResult]":
        """Drops an item stack from the computer's inventory onto the
        ground

        To push an item into an adjacent container instead of dropping
        it, use :meth:`push`.

        The action will fail if ``slot`` is greater than 8.

        :param slot: index of the slot, between 0 to 8
        :param side: side to drop the item from
        :param count: number of items to drop. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be dropped. Must be at least 1
        """
        payload = pb_WorldPayload(
            drop_item=pb_DropItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.DROP_ITEM_RESULT, payload
        )

    def push(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> "SyncBatchFuture[PushItemResult]":
        """Pushes an item stack from the computer's inventory into an
        adjacent container

        The adjacent container can be either a block (e.g. a chest), or
        an entity (e.g. a minecart with chest). Blocks have priority. If
        multiple entities are adjacent, a random entity will be picked.

        If the stack doesn't fit in the container, any remaining items
        will stay in the computer's inventory.

        To drop an item onto the ground instead of pushing it into a
        container, use :meth:`drop`.

        The action will fail if ``slot`` is greater than 8.

        :param slot: index of the slot, between 0 to 8
        :param side: side to push the item from
        :param count: number of items to push. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be pushed. Must be at least 1
        """
        payload = pb_WorldPayload(
            push_item=pb_PushItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.PUSH_ITEM_RESULT, payload
        )

    def swap(
        self, source: int, dest: int
    ) -> "SyncBatchFuture[SwapItemResult]":
        """Swaps two item stacks within the computer's inventory

        To merge two stacks together instead of swapping them, use
        :meth:`merge`.

        The action will fail if ``source`` or ``dest`` is greater than
        8, or if ``source`` and ``dest`` are equal.

        :param source: index of the first slot, between 0 - 8
        :param dest: index of the second slot, between 0 - 8
        """
        payload = pb_WorldPayload(
            swap_item=pb_SwapItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.SWAP_ITEM_RESULT, payload
        )

    def merge(
        self, source: int, dest: int, count: int | None = None
    ) -> "SyncBatchFuture[MergeItemResult]":
        """Merges an item stack within the computer's inventory into
        another slot

        If the destination slot is empty or contains the same item as
        the source slot, items from the source slot will be merged into
        the destination slot. Otherwise, nothing will happen.

        If the destination slot doesn't have enough space to merge all
        the items, any remaining items will stay in the source slot.

        To swap two stacks completely instead of merging them, use
        :meth:`swap`.

        The action will fail if ``source`` or ``dest`` is greater than
        8, or if ``source`` and ``dest`` are equal.

        :param source: index of the slot to merge items from, between
            0 - 8
        :param dest: index of the slot to merge items into, between
            0 - 8
        :param count: number of items to merge. If this is ``None`` or
            is greater than the number of items in the source stack, the
            entire stack will be merged. Must be at least 1
        """
        payload = pb_WorldPayload(
            merge_item=pb_MergeItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.MERGE_ITEM_RESULT, payload
        )


class AsyncItemService:
    """Async service that can be used to interact with the computer's
    inventory

    This class should not be created directly. Use
    :attr:`AsyncClient.item`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "AsyncClient") -> None:
        self._client = _client

    async def get(self) -> tuple[ItemSlot, ...]:
        """Gets all item slots in the computer's inventory

        The slots will be returned in order. Slots may be empty.

        To monitor changes to the inventory in real time, use
        :meth:`subscribe_updates`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(get_inventory=pb_GetInventory())
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.INVENTORY, payload
        )
        assert isinstance(result, _Inventory)
        return _transform_inventory_result(result)

    async def drop(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> DropItemResult:
        """Drops an item stack from the computer's inventory onto the
        ground

        To push an item into an adjacent container instead of dropping
        it, use :meth:`push`.

        :param slot: index of the slot, between 0 to 8
        :param side: side to drop the item from
        :param count: number of items to drop. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be dropped. Must be at least 1

        :raises WorldActionFailedError: if ``slot`` is greater than 8
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(
            drop_item=pb_DropItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.DROP_ITEM_RESULT, payload
        )
        assert isinstance(result, DropItemResult)
        return result

    async def push(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> PushItemResult:
        """Pushes an item stack from the computer's inventory into an
        adjacent container

        The adjacent container can be either a block (e.g. a chest), or
        an entity (e.g. a minecart with chest). Blocks have priority. If
        multiple entities are adjacent, a random entity will be picked.

        If the stack doesn't fit in the container, any remaining items
        will stay in the computer's inventory.

        To drop an item onto the ground instead of pushing it into a
        container, use :meth:`drop`.

        :param slot: index of the slot, between 0 to 8
        :param side: side to push the item from
        :param count: number of items to push. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be pushed. Must be at least 1

        :raises WorldActionFailedError: if ``slot`` is greater than 8
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(
            push_item=pb_PushItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.PUSH_ITEM_RESULT, payload
        )
        assert isinstance(result, PushItemResult)
        return result

    async def swap(self, source: int, dest: int) -> SwapItemResult:
        """Swaps two item stacks within the computer's inventory

        To merge two stacks together instead of swapping them, use
        :meth:`merge`.

        :param source: index of the first slot, between 0 - 8
        :param dest: index of the second slot, between 0 - 8

        :raises WorldActionFailedError: if ``source`` or ``dest`` is
            greater than 8, or if ``source`` and ``dest`` are equal
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(
            swap_item=pb_SwapItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
            )
        )
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.SWAP_ITEM_RESULT, payload
        )
        assert isinstance(result, SwapItemResult)
        return result

    async def merge(
        self, source: int, dest: int, count: int | None = None
    ) -> MergeItemResult:
        """Merges an item stack within the computer's inventory into
        another slot

        If the destination slot is empty or contains the same item as
        the source slot, items from the source slot will be merged into
        the destination slot. Otherwise, nothing will happen.

        If the destination slot doesn't have enough space to merge all
        the items, any remaining items will stay in the source slot.

        To swap two stacks completely instead of merging them, use
        :meth:`swap`.

        :param source: index of the slot to merge items from, between
            0 - 8
        :param dest: index of the slot to merge items into, between
            0 - 8
        :param count: number of items to merge. If this is ``None`` or
            is greater than the number of items in the source stack, the
            entire stack will be merged. Must be at least 1

        :raises WorldActionFailedError: if ``source`` or ``dest`` is
            greater than 8, or if ``source`` and ``dest`` are equal
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(
            merge_item=pb_MergeItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
                count=count,
            )
        )
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.MERGE_ITEM_RESULT, payload
        )
        assert isinstance(result, MergeItemResult)
        return result

    async def subscribe_updates(self) -> AsyncGenerator[ItemSlot]:
        """Yields real-time updates whenever the computer's inventory
        changes

        This method will run forever until the generator is closed or
        the coroutine is cancelled.

        To just get the current inventory without real-time updates, use
        :meth:`get`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        subs = (pb_WorldSubscription.WORLD_SUBSCRIPTION_INVENTORY_UPDATE,)
        async for update in self._client._subscribe_world_subs(subs):
            check_world_sub_type("inventory_update", update)
            for slot in update.inventory_update.slots:
                yield ItemSlot._from_proto(slot)


class AsyncBatchItemService:
    """Async batch service that can be used to interact with the
    computer's inventory

    This class should not be created directly. Use
    :attr:`AsyncBatch.item`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "AsyncBatch") -> None:
        self._batch = _batch

    def get(self) -> "AsyncBatchFuture[tuple[ItemSlot, ...]]":
        """Gets all item slots in the computer's inventory

        The slots will be returned in order. Slots may be empty.

        To monitor changes to the inventory in real time, use
        :meth:`AsyncItemService.subscribe_updates`.
        """
        payload = pb_WorldPayload(get_inventory=pb_GetInventory())
        return self._batch._create_future(
            _WorldResultValueType.INVENTORY,
            payload,
            _transform_inventory_result,
        )

    def drop(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> "AsyncBatchFuture[DropItemResult]":
        """Drops an item stack from the computer's inventory onto the
        ground

        To push an item into an adjacent container instead of dropping
        it, use :meth:`push`.

        The action will fail if ``slot`` is greater than 8.

        :param slot: index of the slot, between 0 to 8
        :param side: side to drop the item from
        :param count: number of items to drop. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be dropped. Must be at least 1
        """
        payload = pb_WorldPayload(
            drop_item=pb_DropItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.DROP_ITEM_RESULT, payload
        )

    def push(
        self, slot: int, side: BlockSide, count: int | None = None
    ) -> "AsyncBatchFuture[PushItemResult]":
        """Pushes an item stack from the computer's inventory into an
        adjacent container

        The adjacent container can be either a block (e.g. a chest), or
        an entity (e.g. a minecart with chest). Blocks have priority. If
        multiple entities are adjacent, a random entity will be picked.

        If the stack doesn't fit in the container, any remaining items
        will stay in the computer's inventory.

        To drop an item onto the ground instead of pushing it into a
        container, use :meth:`drop`.

        The action will fail if ``slot`` is greater than 8.

        :param slot: index of the slot, between 0 to 8
        :param side: side to push the item from
        :param count: number of items to push. If this is ``None`` or is
            greater than the number of items in the stack, the entire
            stack will be pushed. Must be at least 1
        """
        payload = pb_WorldPayload(
            push_item=pb_PushItem(
                index=pb_ItemSlotIndex(index=slot),
                side=side._to_proto(),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.PUSH_ITEM_RESULT, payload
        )

    def swap(
        self, source: int, dest: int
    ) -> "AsyncBatchFuture[SwapItemResult]":
        """Swaps two item stacks within the computer's inventory

        To merge two stacks together instead of swapping them, use
        :meth:`merge`.

        The action will fail if ``source`` or ``dest`` is greater than
        8, or if ``source`` and ``dest`` are equal.

        :param source: index of the first slot, between 0 - 8
        :param dest: index of the second slot, between 0 - 8
        """
        payload = pb_WorldPayload(
            swap_item=pb_SwapItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.SWAP_ITEM_RESULT, payload
        )

    def merge(
        self, source: int, dest: int, count: int | None = None
    ) -> "AsyncBatchFuture[MergeItemResult]":
        """Merges an item stack within the computer's inventory into
        another slot

        If the destination slot is empty or contains the same item as
        the source slot, items from the source slot will be merged into
        the destination slot. Otherwise, nothing will happen.

        If the destination slot doesn't have enough space to merge all
        the items, any remaining items will stay in the source slot.

        To swap two stacks completely instead of merging them, use
        :meth:`swap`.

        The action will fail if ``source`` or ``dest`` is greater than
        8, or if ``source`` and ``dest`` are equal.

        :param source: index of the slot to merge items from, between
            0 - 8
        :param dest: index of the slot to merge items into, between
            0 - 8
        :param count: number of items to merge. If this is ``None`` or
            is greater than the number of items in the source stack, the
            entire stack will be merged. Must be at least 1
        """
        payload = pb_WorldPayload(
            merge_item=pb_MergeItem(
                source=pb_ItemSlotIndex(index=source),
                dest=pb_ItemSlotIndex(index=dest),
                count=count,
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.MERGE_ITEM_RESULT, payload
        )
