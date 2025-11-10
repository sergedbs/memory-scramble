"""
Tests for Board.map() operation.

Phase 6: Transform all card values atomically while maintaining matching consistency.
"""

import pytest
import asyncio
from app.board import Board, Card


@pytest.mark.asyncio
async def test_map_transforms_all_values():
    """map() should transform all card values using the provided transformer."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 0, 1)
    await board.flip_first("p1", 1, 0)
    await board.flip_first("p1", 1, 1)

    # Transform: add prefix to all values
    async def add_prefix(value: str) -> str:
        return f"X{value}"

    await board.map(add_prefix)

    # Verify cards were transformed
    assert board._get_card(0, 0).value == "XA"
    assert board._get_card(0, 1).value == "XB"
    assert board._get_card(1, 0).value == "XA"
    assert board._get_card(1, 1).value == "XB"


@pytest.mark.asyncio
async def test_map_maintains_matching_consistency():
    """Cards that matched before map() should still match after."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 1, 0)

    # Verify initial matching (both A)
    assert board._get_card(0, 0).value == board._get_card(1, 0).value

    # Transform values
    async def uppercase(value: str) -> str:
        return value.upper()

    await board.map(uppercase)

    # Verify matching pairs still match
    assert board._get_card(0, 0).value == board._get_card(1, 0).value


@pytest.mark.asyncio
async def test_map_does_not_change_face_state():
    """map() should not flip cards or change their face-up/down state."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)  # Face up
    await board.flip_first("p1", 1, 0)  # Face up
    # (0,1) and (1,1) remain face down

    async def transform(value: str) -> str:
        return f"new_{value}"

    await board.map(transform)

    assert board._get_card(0, 0).face_up is True
    assert board._get_card(1, 0).face_up is True
    assert board._get_card(0, 1).face_up is False
    assert board._get_card(1, 1).face_up is False


@pytest.mark.asyncio
async def test_map_does_not_change_control():
    """map() should not change card control or remove matched pairs."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_second("p1", 1, 0)  # Match! p1 controls both

    async def transform(value: str) -> str:
        return "Z"

    await board.map(transform)

    # Cards still controlled by p1
    assert board._get_card(0, 0).controller == "p1"
    assert board._get_card(1, 0).controller == "p1"
    # Cards still on board (not removed)
    assert board._get_card(0, 0).on_board is True
    assert board._get_card(1, 0).on_board is True


@pytest.mark.asyncio
async def test_map_with_removed_cards():
    """map() should only transform cards still on the board."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_second("p1", 1, 0)  # Match A-A, cards removed
    await board.flip_first("p1", 0, 1)

    async def transform(value: str) -> str:
        return f"X{value}"

    await board.map(transform)

    # Removed cards stay removed
    assert board._get_card(0, 0).on_board is False
    assert board._get_card(1, 0).on_board is False
    # Remaining cards transformed
    assert board._get_card(0, 1).value == "XB"
    assert board._get_card(1, 1).value == "XB"


@pytest.mark.asyncio
async def test_map_validates_transformed_values():
    """map() should validate transformed values (non-empty, no whitespace)."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)

    # Empty value
    async def make_empty(value: str) -> str:
        return ""

    with pytest.raises(ValueError, match="non-empty"):
        await board.map(make_empty)

    # Whitespace in value
    async def add_space(value: str) -> str:
        return "has space"

    with pytest.raises(ValueError, match="whitespace"):
        await board.map(add_space)

    # Whitespace-only value
    async def only_space(value: str) -> str:
        return "   "

    with pytest.raises(ValueError, match="non-empty"):
        await board.map(only_space)


@pytest.mark.asyncio
async def test_map_with_async_transformer():
    """map() should work with async transformers that have delays."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 0, 1)

    async def slow_transform(value: str) -> str:
        await asyncio.sleep(0.01)  # Simulate async work
        return value.lower()

    await board.map(slow_transform)

    assert board._get_card(0, 0).value == "a"
    assert board._get_card(0, 1).value == "b"


@pytest.mark.asyncio
async def test_map_concurrent_transforms():
    """map() should transform different values concurrently."""
    cards = [[Card("A"), Card("B")], [Card("C"), Card("A")], [Card("B"), Card("C")]]
    board = Board(3, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 0, 1)
    await board.flip_first("p1", 1, 0)

    transform_order = []

    async def track_transform(value: str) -> str:
        transform_order.append(f"start_{value}")
        await asyncio.sleep(0.01)
        transform_order.append(f"end_{value}")
        return value.lower()

    await board.map(track_transform)

    # All transforms should start before any ends (concurrent execution)
    assert "start_A" in transform_order
    assert "start_B" in transform_order
    assert "start_C" in transform_order

    # Verify all transformed
    assert board._get_card(0, 0).value == "a"
    assert board._get_card(0, 1).value == "b"
    assert board._get_card(1, 0).value == "c"


@pytest.mark.asyncio
async def test_map_groups_by_value():
    """map() should transform matching cards together (same group)."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 0, 1)
    await board.flip_first("p1", 1, 0)
    await board.flip_first("p1", 1, 1)

    call_count = {}

    async def count_calls(value: str) -> str:
        call_count[value] = call_count.get(value, 0) + 1
        return f"new_{value}"

    await board.map(count_calls)

    # Each unique value transformed exactly once
    assert call_count["A"] == 1
    assert call_count["B"] == 1

    # Both A cards got the same new value
    assert board._get_card(0, 0).value == board._get_card(1, 0).value
    assert board._get_card(0, 1).value == board._get_card(1, 1).value


@pytest.mark.asyncio
async def test_map_on_empty_board():
    """map() on a board with all cards removed should do nothing."""
    cards = [[Card("A"), Card("A")]]
    board = Board(1, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_second("p1", 0, 1)  # Match, marked for removal

    # Trigger cleanup to actually remove the cards
    player = board._get_or_create_player("p1")
    board._cleanup_before_first_flip(player)

    async def transform(value: str) -> str:
        pytest.fail("Should not be called on empty board")
        return "X"

    await board.map(transform)  # Should not call transformer (early return)

    # Cards now removed
    assert board._get_card(0, 0).on_board is False
    assert board._get_card(0, 1).on_board is False


@pytest.mark.asyncio
async def test_map_notifies_watchers():
    """map() should notify watchers when board changes."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)

    async def transform(value: str) -> str:
        return "Z"

    # Start a watcher
    watch_task = asyncio.create_task(board.watch())

    # Give watcher time to start waiting
    await asyncio.sleep(0.01)

    # map() should wake up the watcher
    await board.map(transform)

    # Watcher should complete quickly
    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_map_multiple_groups_atomic():
    """Each value group should be committed atomically."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)
    await board.flip_first("p1", 0, 0)
    await board.flip_first("p1", 0, 1)
    await board.flip_first("p1", 1, 0)
    await board.flip_first("p1", 1, 1)

    async def transform(value: str) -> str:
        await asyncio.sleep(0.01)
        return f"group_{value}"

    await board.map(transform)

    # All A cards should have the same transformed value
    assert board._get_card(0, 0).value == "group_A"
    assert board._get_card(1, 0).value == "group_A"
    # All B cards should have the same transformed value
    assert board._get_card(0, 1).value == "group_B"
    assert board._get_card(1, 1).value == "group_B"


@pytest.mark.asyncio
async def test_map_with_single_card():
    """map() should work with a single-card board."""
    cards = [[Card("A")]]
    board = Board(1, 1, cards)
    await board.flip_first("p1", 0, 0)

    async def transform(value: str) -> str:
        return "SOLO"

    await board.map(transform)

    assert board._get_card(0, 0).value == "SOLO"
