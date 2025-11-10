# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

"""
Tests for Board._flip_first_immediate() - Rule 1 implementation.

Rule 1: First card flip attempt:
  1-A: If no card (removed): fail with FlipError
  1-B: If face down: flip up, grant control
  1-C: If face up and uncontrolled: grant control
  1-D: If face up and controlled by another: block/wait (Phase 5)
       For Phase 4: raise FlipError
"""

from app.board import Board, Card, FlipError
import pytest


class TestFlipFirstRemovedCard:
    """Tests for Rule 1-A: flipping a removed card."""

    def test_flip_removed_card_raises_error(self):
        """Flipping a removed card raises FlipError."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Remove the card
        card = board._get_card(0, 0)
        card.remove()

        # Attempt to flip it should fail
        with pytest.raises(FlipError, match="Cannot flip a removed card"):
            board._flip_first_immediate("alice", 0, 0)

    def test_flip_removed_card_does_not_change_state(self):
        """Failed flip of removed card doesn't change board state."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.remove()

        try:
            board._flip_first_immediate("bob", 0, 0)
        except FlipError:
            pass

        # Card still removed
        assert not card.on_board
        assert not card.face_up
        assert card.controller is None

    def test_flip_removed_card_does_not_create_player_state(self):
        """Failed flip doesn't grant control to player."""
        cards = [[Card("A"), Card("A")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.remove()

        try:
            board._flip_first_immediate("charlie", 0, 0)
        except FlipError:
            pass

        # Player should have been created but has no control
        player = board._get_or_create_player("charlie")
        assert player.first_card is None


class TestFlipFirstFaceDown:
    """Tests for Rule 1-B: flipping a face-down card."""

    def test_flip_face_down_card_flips_up(self):
        """Flipping a face-down card turns it face up."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        assert not card.face_up

        board._flip_first_immediate("alice", 0, 0)

        assert card.face_up

    def test_flip_face_down_grants_control(self):
        """Flipping a face-down card grants control to the player."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        board._flip_first_immediate("bob", 0, 0)

        card = board._get_card(0, 0)
        assert card.controller == "bob"

        player = board._get_or_create_player("bob")
        assert player.first_card == (0, 0)

    def test_flip_face_down_card_remains_on_board(self):
        """Flipped card remains on the board."""
        cards = [[Card("Z"), Card("Z")]]
        board = Board(1, 2, cards)

        board._flip_first_immediate("charlie", 0, 0)

        card = board._get_card(0, 0)
        assert card.on_board

    def test_flip_different_face_down_cards(self):
        """Multiple players can flip different face-down cards."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        board._flip_first_immediate("alice", 0, 0)
        board._flip_first_immediate("bob", 1, 1)

        card1 = board._get_card(0, 0)
        card2 = board._get_card(1, 1)

        assert card1.face_up and card1.controller == "alice"
        assert card2.face_up and card2.controller == "bob"


class TestFlipFirstFaceUpUncontrolled:
    """Tests for Rule 1-C: flipping a face-up uncontrolled card."""

    def test_flip_face_up_uncontrolled_grants_control(self):
        """Flipping face-up uncontrolled card grants control."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Card is face up but uncontrolled
        card = board._get_card(0, 0)
        card.flip_up()

        board._flip_first_immediate("alice", 0, 0)

        assert card.controller == "alice"
        player = board._get_or_create_player("alice")
        assert player.first_card == (0, 0)

    def test_flip_face_up_uncontrolled_stays_up(self):
        """Face-up uncontrolled card remains face up."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.flip_up()

        board._flip_first_immediate("bob", 0, 0)

        assert card.face_up

    def test_flip_relinquished_card(self):
        """Player can take control of a card another player relinquished."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.flip_up()
        card.set_controller("alice")
        # Alice relinquishes control
        card.set_controller(None)

        # Bob can now take control
        board._flip_first_immediate("bob", 0, 0)

        assert card.controller == "bob"


class TestFlipFirstControlled:
    """Tests for Rule 1-D: flipping a controlled card (Phase 4 version)."""

    def test_flip_controlled_card_raises_error(self):
        """Flipping a card controlled by another player raises FlipError in Phase 4."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls the card
        card = board._get_card(0, 0)
        card.flip_up()
        card.set_controller("alice")

        # Bob tries to flip it
        with pytest.raises(FlipError, match="controlled by another player"):
            board._flip_first_immediate("bob", 0, 0)

    def test_flip_own_controlled_card_raises_error(self):
        """Player cannot flip a card they already control."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        card = board._get_card(0, 0)
        card.flip_up()
        card.set_controller("alice")

        # Alice tries to flip it again
        with pytest.raises(FlipError, match="controlled by another player"):
            board._flip_first_immediate("alice", 0, 0)


class TestFlipFirstWithCleanup:
    """Tests that first flip triggers cleanup."""

    def test_first_flip_triggers_cleanup_of_matched_pair(self):
        """First flip removes previously matched cards."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # Alice has matched pair from previous turn
        alice = board._get_or_create_player("alice")
        alice.mark_match((0, 0), (0, 1))

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("alice")
        card2.set_controller("alice")

        # Alice flips a new first card
        board._flip_first_immediate("alice", 1, 0)

        # Old matched pair should be removed
        assert not card1.on_board
        assert not card2.on_board

        # Alice now controls the new card
        card3 = board._get_card(1, 0)
        assert card3.controller == "alice"
        assert alice.first_card == (1, 0)

    def test_first_flip_triggers_cleanup_of_mismatched_cards(self):
        """First flip flips down previously relinquished cards."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Bob has relinquished cards from previous turn
        bob = board._get_or_create_player("bob")
        bob.first_card = (0, 0)
        bob.second_card = (0, 1)

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        # Cards are face up but uncontrolled (relinquished)

        # Bob flips a new first card
        board._flip_first_immediate("bob", 1, 0)

        # Old relinquished cards should be face down
        assert not card1.face_up
        assert not card2.face_up

        # Bob now controls the new card
        card3 = board._get_card(1, 0)
        assert card3.controller == "bob"
        assert bob.first_card == (1, 0)

    def test_first_flip_cleanup_only_affects_own_player(self):
        """Cleanup only affects the player making the flip."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Alice has relinquished cards
        alice = board._get_or_create_player("alice")
        alice.first_card = (0, 0)

        card1 = board._get_card(0, 0)
        card1.flip_up()

        # Bob has different cards
        bob = board._get_or_create_player("bob")
        bob.first_card = (0, 1)

        card2 = board._get_card(0, 1)
        card2.flip_up()

        # Alice flips new card
        board._flip_first_immediate("alice", 1, 0)

        # Alice's old card flipped down
        assert not card1.face_up

        # Bob's card unaffected
        assert card2.face_up


class TestFlipFirstEdgeCases:
    """Edge cases and boundary conditions."""

    def test_flip_first_with_invalid_position(self):
        """Flipping at invalid position raises ValueError."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        with pytest.raises(ValueError, match="out of bounds"):
            board._flip_first_immediate("alice", 5, 5)

    def test_flip_first_negative_position(self):
        """Negative positions are invalid."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        with pytest.raises(ValueError, match="out of bounds"):
            board._flip_first_immediate("bob", -1, 0)

    def test_flip_first_creates_player_if_needed(self):
        """Flipping creates player state if it doesn't exist."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        assert "new_player" not in board._players

        board._flip_first_immediate("new_player", 0, 0)

        assert "new_player" in board._players

    def test_flip_first_preserves_board_invariants(self):
        """First flip maintains board representation invariants."""
        cards = [[Card("X"), Card("X")], [Card("Y"), Card("Y")]]
        board = Board(2, 2, cards)

        board._flip_first_immediate("alice", 0, 0)

        # Should not raise
        board._check_rep()

    def test_multiple_first_flips_in_sequence(self):
        """Multiple first flips by same player with cleanup."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # First turn
        board._flip_first_immediate("alice", 0, 0)
        alice = board._get_or_create_player("alice")
        assert alice.first_card == (0, 0)

        # Simulate relinquish (manually for this test)
        card1 = board._get_card(0, 0)
        card1.set_controller(None)
        # alice.first_card remains set (will be cleaned up)

        # Second turn - should trigger cleanup
        board._flip_first_immediate("alice", 0, 1)

        # Old card flipped down
        assert not card1.face_up

        # New card controlled
        card2 = board._get_card(0, 1)
        assert card2.controller == "alice"
        assert alice.first_card == (0, 1)
