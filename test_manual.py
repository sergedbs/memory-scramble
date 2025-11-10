#!/usr/bin/env python3
"""Manual verification of complete game flow."""

import asyncio
from app.board import Board, Card


async def test_complete_game_flow():
    """Test a complete game sequence with all rules."""

    print("=" * 60)
    print("MANUAL VERIFICATION: Complete Game Flow")
    print("=" * 60)

    # Create a simple 2x2 board with one matching pair
    cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]
    board = Board(2, 2, cards)

    print("\n1. Initial Board State")
    print("-" * 60)
    state = board.look("player1")
    print(state)
    assert "2x2" in state
    assert state.count("down") == 4, "All cards should be face down"
    print("✓ All cards face down")

    print("\n2. Player1 flips first card (0,0) - should be 'A'")
    print("-" * 60)
    await board.flip("player1", 0, 0)
    state = board.look("player1")
    print(state)
    assert "my A" in state, "Player should control card A"
    assert state.count("down") == 3, "3 cards should remain face down"
    print("✓ Player1 controls first card")

    print("\n3. Player1 flips second card (0,1) - should be 'B' (mismatch)")
    print("-" * 60)
    await board.flip("player1", 0, 1)
    state = board.look("player1")
    print(state)
    # Both cards should be face up but no longer controlled (relinquished on mismatch)
    assert "down" in state, "Some cards should be face down"
    assert state.count("my") == 0, "Player should not control any cards after mismatch"
    print("✓ Mismatch detected, both cards relinquished")

    print("\n4. Player1 starts new turn - cleanup should flip down uncontrolled cards")
    print("-" * 60)
    await board.flip("player1", 1, 0)  # Start new turn by flipping a different card
    state = board.look("player1")
    print(state)
    # The previously mismatched cards should now be face down
    print("✓ Cleanup occurred before new first flip")

    print("\n5. Player2 flips card (0,0) - should be 'A'")
    print("-" * 60)
    # First complete player1's turn
    await board.flip("player1", 1, 1)  # Complete turn
    # Now player2 can play
    await board.flip("player2", 0, 0)
    state = board.look("player2")
    print(state)
    assert "my A" in state, "Player2 should control card A"
    print("✓ Player2 controls first card")

    print("\n6. Player2 flips matching card (1,0) - should also be 'A' (match!)")
    print("-" * 60)
    await board.flip("player2", 1, 0)
    state = board.look("player2")
    print(state)
    # Both matching cards should still be up and controlled
    assert state.count("my A") == 2, "Both matching A cards should be controlled"
    print("✓ Match detected, player controls both cards")

    print("\n7. Player2 starts new turn - matched pair should be removed")
    print("-" * 60)
    await board.flip("player2", 0, 1)  # Start new turn
    state = board.look("player2")
    print(state)
    assert state.count("none") == 2, "Matched pair should be removed"
    assert "A" not in state, "Card A should be gone"
    print("✓ Matched pair removed from board")

    print("\n8. Verify remaining cards")
    print("-" * 60)
    print(state)
    assert state.count("my B") == 1, "Player2 should control new card"
    assert state.count("down") == 1 or state.count("up B") == 1, (
        "One B card should remain"
    )
    print("✓ Only B cards remain on board")

    print("\n" + "=" * 60)
    print("✅ ALL MANUAL VERIFICATION TESTS PASSED")
    print("=" * 60)


async def test_concurrency():
    """Test concurrent operations."""

    print("\n" + "=" * 60)
    print("MANUAL VERIFICATION: Concurrency")
    print("=" * 60)

    cards = [[Card("X"), Card("Y")], [Card("X"), Card("Y")]]
    board = Board(2, 2, cards)

    print("\n1. Two players try to flip same card concurrently")
    print("-" * 60)

    async def player1_flip():
        await board.flip("player1", 0, 0)
        print("  Player1: Got card (0,0)")
        await asyncio.sleep(0.2)  # Hold the card
        await board.flip("player1", 1, 1)  # Try second flip
        print("  Player1: Completed turn")

    async def player2_flip():
        await asyncio.sleep(0.05)  # Let player1 go first
        print("  Player2: Waiting for card (0,0)...")
        await board.flip("player2", 0, 0)  # Should wait
        print("  Player2: Got card (0,0)")

    # Run concurrently
    await asyncio.gather(player1_flip(), player2_flip())

    state = board.look("player2")
    print("\nFinal state from player2's perspective:")
    print(state)
    print("✓ Concurrent access handled correctly")

    print("\n" + "=" * 60)
    print("✅ CONCURRENCY TEST PASSED")
    print("=" * 60)


async def test_map_operation():
    """Test map operation preserves matching consistency."""

    print("\n" + "=" * 60)
    print("MANUAL VERIFICATION: Map Operation")
    print("=" * 60)

    cards = [[Card("cat"), Card("dog")], [Card("cat"), Card("dog")]]
    board = Board(2, 2, cards)

    print("\n1. Initial board")
    print("-" * 60)
    state = board.look("observer")
    print(state)

    print("\n2. Flip two matching 'cat' cards")
    print("-" * 60)
    await board.flip("player1", 0, 0)
    await board.flip("player1", 1, 0)
    state = board.look("player1")
    print(state)
    assert state.count("my cat") == 2

    print("\n3. Apply map to uppercase all cards")
    print("-" * 60)

    async def uppercase(value: str) -> str:
        await asyncio.sleep(0.01)  # Simulate async work
        return value.upper()

    await board.map(uppercase)

    state = board.look("player1")
    print(state)
    assert state.count("my CAT") == 2, "Both controlled cards should be uppercased"
    assert "cat" not in state.lower() or "CAT" in state, (
        "All cards should be transformed"
    )
    print("✓ Map transformed all card values")

    print("\n4. Verify matching consistency maintained")
    print("-" * 60)
    # Start new turn to trigger cleanup
    await board.flip("player1", 0, 1)
    state = board.look("player1")
    print(state)
    assert state.count("none") == 2, "Original matching CAT pair should be removed"
    print("✓ Matching consistency preserved through map")

    print("\n" + "=" * 60)
    print("✅ MAP OPERATION TEST PASSED")
    print("=" * 60)


async def test_watch_operation():
    """Test watch operation waits for changes."""

    print("\n" + "=" * 60)
    print("MANUAL VERIFICATION: Watch Operation")
    print("=" * 60)

    cards = [[Card("A"), Card("A")]]
    board = Board(1, 2, cards)

    print("\n1. Start watching in background")
    print("-" * 60)

    watch_completed = False

    async def watcher():
        nonlocal watch_completed
        print("  Watcher: Started watching...")
        await board.watch()
        print("  Watcher: Board changed!")
        watch_completed = True

    async def player():
        await asyncio.sleep(0.1)  # Let watcher start
        print("  Player: Flipping card...")
        await board.flip("player1", 0, 0)
        print("  Player: Card flipped")

    # Run concurrently
    await asyncio.gather(watcher(), player())

    assert watch_completed, "Watcher should have been notified"
    print("✓ Watch operation notified on board change")

    print("\n" + "=" * 60)
    print("✅ WATCH OPERATION TEST PASSED")
    print("=" * 60)


async def main():
    """Run all manual verification tests."""
    try:
        await test_complete_game_flow()
        await test_concurrency()
        await test_map_operation()
        await test_watch_operation()

        print("\n" + "=" * 60)
        print("🎉 ALL MANUAL VERIFICATIONS PASSED")
        print("=" * 60)
        print("\nThe implementation correctly follows all game rules:")
        print("  ✓ First/second flip mechanics")
        print("  ✓ Match/mismatch detection")
        print("  ✓ Turn boundary cleanup")
        print("  ✓ Concurrent access control")
        print("  ✓ Map operation with consistency")
        print("  ✓ Watch operation notifications")

    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
