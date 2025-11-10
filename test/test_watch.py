"""
Tests for Board.watch() operation.

Phase 6: Long-polling to wait for board changes.
"""

import pytest
import asyncio
from app.board import Board, Card


@pytest.mark.asyncio
async def test_watch_returns_immediately_on_change():
    """watch() should return when the board changes."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # Start watching
    watch_task = asyncio.create_task(board.watch())

    # Give watcher time to start waiting
    await asyncio.sleep(0.01)

    # Make a change
    await board.flip_first("p1", 0, 0)

    # watch() should complete quickly after the change
    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_waits_when_no_changes():
    """watch() should block until a change occurs."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # Start watching
    watch_task = asyncio.create_task(board.watch())

    # Give watcher time to start waiting
    await asyncio.sleep(0.05)

    # watch() should still be waiting (not completed)
    assert not watch_task.done()

    # Cancel the watch task to clean up
    watch_task.cancel()
    try:
        await watch_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_watch_notified_by_flip_first():
    """watch() should be notified when flip_first() is called."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    await board.flip_first("p1", 0, 0)

    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_notified_by_flip_second():
    """watch() should be notified when flip_second() is called."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # Setup: flip first card
    await board.flip_first("p1", 0, 0)

    # Start watching
    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    # Flip second card (will match and remove cards)
    await board.flip_second("p1", 1, 0)

    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_notified_by_map():
    """watch() should be notified when map() transforms values."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    async def transform(value: str) -> str:
        return f"X{value}"

    await board.map(transform)

    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_multiple_watchers():
    """Multiple watchers should all be notified of changes."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # Start multiple watchers
    watch1 = asyncio.create_task(board.watch())
    watch2 = asyncio.create_task(board.watch())
    watch3 = asyncio.create_task(board.watch())

    await asyncio.sleep(0.01)

    # Make a change
    await board.flip_first("p1", 0, 0)

    # All watchers should complete
    await asyncio.wait_for(asyncio.gather(watch1, watch2, watch3), timeout=0.1)


@pytest.mark.asyncio
async def test_watch_sequential_changes():
    """watch() can be called multiple times to wait for successive changes."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # First watch
    watch1 = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)
    await board.flip_first("p1", 0, 0)
    await asyncio.wait_for(watch1, timeout=0.1)

    # Second watch
    watch2 = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)
    await board.flip_first("p2", 0, 1)
    await asyncio.wait_for(watch2, timeout=0.1)

    # Third watch
    watch3 = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)
    await board.flip_first("p3", 1, 0)
    await asyncio.wait_for(watch3, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_not_notified_by_look():
    """watch() should not be triggered by read-only operations like look()."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    # look() should not trigger watch
    board.look("p1")
    board.look("p2")

    await asyncio.sleep(0.05)

    # watch() should still be waiting
    assert not watch_task.done()

    watch_task.cancel()
    try:
        await watch_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_watch_concurrent_with_flip():
    """watch() works correctly when changes happen concurrently."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    async def make_changes():
        await asyncio.sleep(0.01)
        await board.flip_first("p1", 0, 0)
        await asyncio.sleep(0.01)
        await board.flip_first("p2", 0, 1)
        await asyncio.sleep(0.01)
        await board.flip_first("p3", 1, 0)

    # Start watcher and changes concurrently
    watch_task = asyncio.create_task(board.watch())
    change_task = asyncio.create_task(make_changes())

    # Watcher should complete when first change happens
    await asyncio.wait_for(watch_task, timeout=0.5)
    await change_task  # Let changes finish


@pytest.mark.asyncio
async def test_watch_with_card_removal():
    """watch() should be notified when cards are removed (matched)."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    # Setup: flip first card
    await board.flip_first("p1", 0, 0)

    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    # Match cards (removes them)
    await board.flip_second("p1", 1, 0)

    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_empty_board():
    """watch() should work on an empty board (all cards removed)."""
    cards = [[Card("A"), Card("A")]]
    board = Board(1, 2, cards)

    # Remove all cards
    await board.flip_first("p1", 0, 0)
    await board.flip_second("p1", 0, 1)

    # watch() should still wait for changes
    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.05)

    assert not watch_task.done()

    watch_task.cancel()
    try:
        await watch_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_watch_with_unified_flip():
    """watch() should be notified by the unified flip() method."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    watch_task = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)

    # Use unified flip() method
    await board.flip("p1", 0, 0)

    await asyncio.wait_for(watch_task, timeout=0.1)


@pytest.mark.asyncio
async def test_watch_stress_multiple_rapid_changes():
    """watch() handles multiple rapid changes correctly."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    changes_detected = 0

    async def watcher():
        nonlocal changes_detected
        for _ in range(3):
            await board.watch()
            changes_detected += 1

    async def changer():
        await asyncio.sleep(0.01)
        await board.flip_first("p1", 0, 0)
        await asyncio.sleep(0.01)
        await board.flip_first("p2", 0, 1)
        await asyncio.sleep(0.01)
        await board.flip_first("p3", 1, 0)

    await asyncio.gather(watcher(), changer())

    assert changes_detected == 3


@pytest.mark.asyncio
async def test_watch_version_increments():
    """Each change should increment the board's version counter."""
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    initial_version = board._version

    # First change
    watch1 = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)
    await board.flip_first("p1", 0, 0)
    await asyncio.wait_for(watch1, timeout=0.1)

    assert board._version > initial_version
    version_after_first = board._version

    # Second change
    watch2 = asyncio.create_task(board.watch())
    await asyncio.sleep(0.01)
    await board.flip_first("p2", 0, 1)
    await asyncio.wait_for(watch2, timeout=0.1)

    assert board._version > version_after_first
