# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

"""
Tests for Phase 5: Async concurrency with blocking/waiting support.

Tests the async flip_first(), flip_second(), and flip() methods with:
- Non-blocking waits for controlled cards
- Fair contention via asyncio.Condition
- Proper notification of waiting players
"""

import pytest
import asyncio
from app.board import Board, Card, FlipError


class TestAsyncFlipFirst:
    """Tests for async flip_first() without contention."""

    @pytest.mark.asyncio
    async def test_async_flip_first_face_down(self):
        """Async flip of face-down card works."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        await board.flip_first("alice", 0, 0)

        card = board._get_card(0, 0)
        assert card.face_up
        assert card.controller == "alice"

    @pytest.mark.asyncio
    async def test_async_flip_first_removed_raises_error(self):
        """Async flip of removed card raises FlipError."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.remove()

        with pytest.raises(FlipError, match="Cannot flip a removed card"):
            await board.flip_first("bob", 0, 0)

    @pytest.mark.asyncio
    async def test_async_flip_first_uncontrolled(self):
        """Async flip of uncontrolled face-up card grants control."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Card already face up but uncontrolled
        card = board._get_card(0, 0)
        card.flip_up()

        await board.flip_first("charlie", 0, 0)

        assert card.controller == "charlie"


class TestAsyncFlipSecond:
    """Tests for async flip_second()."""

    @pytest.mark.asyncio
    async def test_async_flip_second_match(self):
        """Async second flip with match keeps both cards."""
        cards = [[Card("A"), Card("A")]]
        board = Board(1, 2, cards)

        await board.flip_first("alice", 0, 0)
        await board.flip_second("alice", 0, 1)

        alice = board._get_or_create_player("alice")
        assert alice.matched_pair == ((0, 0), (0, 1))

    @pytest.mark.asyncio
    async def test_async_flip_second_mismatch(self):
        """Async second flip with mismatch relinquishes both."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        await board.flip_first("bob", 0, 0)
        await board.flip_second("bob", 0, 1)

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)

        assert card1.controller is None
        assert card2.controller is None

    @pytest.mark.asyncio
    async def test_async_flip_second_removed_fails(self):
        """Async second flip on removed card fails and relinquishes first."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        await board.flip_first("charlie", 0, 0)

        # Remove second card
        card2 = board._get_card(0, 1)
        card2.remove()

        with pytest.raises(FlipError):
            await board.flip_second("charlie", 0, 1)

        # First card relinquished
        card1 = board._get_card(0, 0)
        assert card1.controller is None


class TestAsyncUnifiedFlip:
    """Tests for unified async flip() method."""

    @pytest.mark.asyncio
    async def test_unified_flip_routes_to_first(self):
        """flip() calls flip_first when player has no cards."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        await board.flip("alice", 0, 0)

        alice = board._get_or_create_player("alice")
        assert alice.first_card == (0, 0)

    @pytest.mark.asyncio
    async def test_unified_flip_routes_to_second(self):
        """flip() calls flip_second when player has first card."""
        cards = [[Card("X"), Card("X")]]
        board = Board(1, 2, cards)

        await board.flip("bob", 0, 0)
        await board.flip("bob", 0, 1)

        bob = board._get_or_create_player("bob")
        assert bob.matched_pair == ((0, 0), (0, 1))

    @pytest.mark.asyncio
    async def test_unified_flip_complete_turn(self):
        """Complete turn sequence using flip()."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # First turn: match
        await board.flip("alice", 0, 0)
        await board.flip("alice", 0, 1)

        # Second turn: cleanup happens automatically
        await board.flip("alice", 1, 0)

        # Old cards removed
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        assert not card1.on_board
        assert not card2.on_board

        # New card controlled
        alice = board._get_or_create_player("alice")
        assert alice.first_card == (1, 0)


class TestAsyncBlocking:
    """Tests for blocking/waiting on controlled cards (Rule 1-D)."""

    @pytest.mark.asyncio
    async def test_flip_first_waits_for_controlled_card(self):
        """Player blocks when trying to flip card controlled by another."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls the card
        await board.flip_first("alice", 0, 0)

        # Bob tries to flip same card - should block
        bob_task = asyncio.create_task(board.flip_first("bob", 0, 0))

        # Give Bob's task a chance to start and block
        await asyncio.sleep(0.01)

        # Bob's task should still be pending (blocked)
        assert not bob_task.done()

        # Alice relinquishes by trying second flip on removed card
        card2 = board._get_card(0, 1)
        card2.remove()
        try:
            await board.flip_second("alice", 0, 1)
        except FlipError:
            pass

        # Now Bob should be able to take control
        await bob_task

        card = board._get_card(0, 0)
        assert card.controller == "bob"

    @pytest.mark.asyncio
    async def test_multiple_players_wait_for_same_card(self):
        """Multiple players can wait for the same controlled card."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        # Alice controls the card
        await board.flip_first("alice", 0, 0)

        # Bob and Charlie both try to flip it
        bob_task = asyncio.create_task(board.flip_first("bob", 0, 0))
        charlie_task = asyncio.create_task(board.flip_first("charlie", 0, 0))

        await asyncio.sleep(0.01)

        # Both should be blocked
        assert not bob_task.done()
        assert not charlie_task.done()

        # Alice relinquishes (second flip on removed card)
        card2 = board._get_card(0, 1)
        card2.remove()
        try:
            await board.flip_second("alice", 0, 1)
        except FlipError:
            pass

        # One of them should get control (FIFO order)
        await asyncio.sleep(0.01)

        # At least one should have succeeded
        card = board._get_card(0, 0)
        assert card.controller in ["bob", "charlie"]

        # Cancel the other task
        if not bob_task.done():
            bob_task.cancel()
        if not charlie_task.done():
            charlie_task.cancel()

    @pytest.mark.asyncio
    async def test_wait_then_card_removed(self):
        """Player waits, then card is removed before they get control."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Alice controls card at (0,0)
        await board.flip_first("alice", 0, 0)

        # Bob waits for that card
        bob_task = asyncio.create_task(board.flip_first("bob", 0, 0))
        await asyncio.sleep(0.01)

        # Alice matches and removes the cards
        card_a2 = board._get_card(0, 1)
        card_a2.value = "A"  # Make it match
        await board.flip_second("alice", 0, 1)

        # Next first flip triggers cleanup (removes matched pair)
        await board.flip_first("alice", 1, 0)

        # Bob's task should wake up and fail (card removed)
        with pytest.raises(FlipError, match="Cannot flip a removed card"):
            await bob_task

    @pytest.mark.asyncio
    async def test_concurrent_flips_different_cards(self):
        """Multiple players can flip different cards concurrently."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # All should succeed without blocking
        await asyncio.gather(
            board.flip_first("alice", 0, 0),
            board.flip_first("bob", 0, 1),
            board.flip_first("charlie", 1, 0),
            board.flip_first("david", 1, 1),
        )

        # All cards controlled by different players
        assert board._get_card(0, 0).controller == "alice"
        assert board._get_card(0, 1).controller == "bob"
        assert board._get_card(1, 0).controller == "charlie"
        assert board._get_card(1, 1).controller == "david"


class TestAsyncNotification:
    """Tests for spot release notification."""

    @pytest.mark.asyncio
    async def test_mismatch_releases_both_spots(self):
        """Mismatched second flip notifies waiters on both spots."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Alice flips two mismatched cards
        await board.flip_first("alice", 0, 0)
        await board.flip_second("alice", 0, 1)

        # Both cards are uncontrolled now
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        assert card1.controller is None
        assert card2.controller is None

        # Bob and Charlie can now flip them
        await board.flip_first("bob", 0, 0)
        await board.flip_first("charlie", 0, 1)

        assert card1.controller == "bob"
        assert card2.controller == "charlie"

    @pytest.mark.asyncio
    async def test_failed_second_flip_releases_first(self):
        """Failed second flip releases first card for others."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice flips first
        await board.flip_first("alice", 0, 0)

        # Bob waits for it
        bob_task = asyncio.create_task(board.flip_first("bob", 0, 0))
        await asyncio.sleep(0.01)

        # Alice's second flip fails (card controlled by someone else)
        card2 = board._get_card(0, 1)
        card2.flip_up()
        card2.set_controller("charlie")

        try:
            await board.flip_second("alice", 0, 1)
        except FlipError:
            pass

        # Bob should now get control
        await bob_task
        assert board._get_card(0, 0).controller == "bob"


class TestAsyncIntegration:
    """Integration tests for async game logic."""

    @pytest.mark.asyncio
    async def test_two_player_game_sequence(self):
        """Two players playing concurrently."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # Alice finds a match
        await board.flip("alice", 0, 0)
        await board.flip("alice", 0, 1)

        # Alice removes her cards by flipping a new first card
        await board.flip("alice", 1, 0)  # Triggers cleanup

        # Check that Alice's matched pair was removed
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        assert not card1.on_board
        assert not card2.on_board

        # Alice now controls (1,0)
        alice = board._get_or_create_player("alice")
        assert alice.first_card == (1, 0)

        # Bob can play on remaining cards
        await board.flip("bob", 1, 1)
        bob = board._get_or_create_player("bob")
        assert bob.first_card == (1, 1)

    @pytest.mark.asyncio
    async def test_async_preserves_board_invariants(self):
        """Async operations maintain board invariants."""
        cards = [[Card("X"), Card("X")], [Card("Y"), Card("Y")]]
        board = Board(2, 2, cards)

        await board.flip("alice", 0, 0)
        await board.flip("alice", 0, 1)
        await board.flip("alice", 1, 0)

        # Should not raise
        board._check_rep()
