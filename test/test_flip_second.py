# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

"""
Tests for Board._flip_second_immediate() - Rule 2 implementation.

Rule 2: Second card flip attempt (when player controls one card):
  2-A: If no card (removed): fail, relinquish first card
  2-B: If face up and controlled: fail, relinquish first card
  2-C/D/E: If face down or (face up and uncontrolled):
    - Flip up if needed
    - If match: keep control of both
    - If no match: relinquish both
"""

from app.board import Board, Card, FlipError
import pytest


class TestFlipSecondPreconditions:
    """Tests for preconditions and validation."""

    def test_flip_second_requires_first_card(self):
        """Cannot flip second card without controlling a first card."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        with pytest.raises(ValueError, match="must control first card"):
            board._flip_second_immediate("alice", 0, 1)

    def test_flip_second_with_existing_second_card_fails(self):
        """Cannot flip second card if already have one."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        player.second_card = (0, 1)

        with pytest.raises(ValueError, match="already has second card"):
            board._flip_second_immediate("alice", 1, 0)

    def test_flip_second_invalid_position(self):
        """Invalid position raises ValueError."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)

        with pytest.raises(ValueError, match="out of bounds"):
            board._flip_second_immediate("alice", 5, 5)


class TestFlipSecondRemovedCard:
    """Tests for Rule 2-A: flipping removed card as second flip."""

    def test_flip_second_removed_card_raises_error(self):
        """Flipping removed card as second flip raises FlipError."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls first card
        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        # Remove the second card
        card2 = board._get_card(0, 1)
        card2.remove()

        # Attempt to flip removed card
        with pytest.raises(FlipError, match="Cannot flip a removed card"):
            board._flip_second_immediate("alice", 0, 1)

    def test_flip_second_removed_relinquishes_first(self):
        """Failed second flip on removed card relinquishes first card."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("bob")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("bob")

        # Remove second card
        card2 = board._get_card(0, 1)
        card2.remove()

        try:
            board._flip_second_immediate("bob", 0, 1)
        except FlipError:
            pass

        # First card should be relinquished (uncontrolled but face up)
        assert card1.on_board
        assert card1.face_up
        assert card1.controller is None

    def test_flip_second_removed_clears_first_in_player_state(self):
        """Failed flip clears first_card from player state."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("charlie")

        card2 = board._get_card(0, 1)
        card2.remove()

        try:
            board._flip_second_immediate("charlie", 0, 1)
        except FlipError:
            pass

        # Player state should mark first card for cleanup
        assert player.first_card is None


class TestFlipSecondControlledCard:
    """Tests for Rule 2-B: flipping controlled card as second flip."""

    def test_flip_second_controlled_by_other_raises_error(self):
        """Flipping card controlled by another player raises FlipError."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls first card
        alice = board._get_or_create_player("alice")
        alice.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        # Bob controls second card
        card2 = board._get_card(0, 1)
        card2.flip_up()
        card2.set_controller("bob")

        # Alice tries to flip Bob's card
        with pytest.raises(FlipError, match="already controlled"):
            board._flip_second_immediate("alice", 0, 1)

    def test_flip_second_controlled_by_self_raises_error(self):
        """Cannot flip the same card as second flip."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card = board._get_card(0, 0)
        card.flip_up()
        card.set_controller("alice")

        # Try to flip same card again
        with pytest.raises(FlipError, match="already controlled"):
            board._flip_second_immediate("alice", 0, 0)

    def test_flip_second_controlled_relinquishes_first(self):
        """Failed flip on controlled card relinquishes first card."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        alice = board._get_or_create_player("alice")
        alice.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        # Bob controls second card
        card2 = board._get_card(0, 1)
        card2.flip_up()
        card2.set_controller("bob")

        try:
            board._flip_second_immediate("alice", 0, 1)
        except FlipError:
            pass

        # Alice's first card relinquished
        assert card1.controller is None
        assert card1.face_up  # Remains face up


class TestFlipSecondMatch:
    """Tests for Rule 2-D: successful match."""

    def test_flip_second_match_keeps_both_cards(self):
        """Matching cards keeps both under player control."""
        cards = [[Card("A"), Card("A")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        # Flip second matching card
        board._flip_second_immediate("alice", 0, 1)

        card2 = board._get_card(0, 1)

        # Both cards controlled by alice
        assert card1.controller == "alice"
        assert card2.controller == "alice"

        # Player state tracks both
        assert player.first_card == (0, 0)
        assert player.second_card == (0, 1)

    def test_flip_second_match_marks_for_removal(self):
        """Matching cards are marked for removal at turn boundary."""
        cards = [[Card("X"), Card("X")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("bob")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("bob")

        board._flip_second_immediate("bob", 0, 1)

        # Matched pair marked
        assert player.matched_pair == ((0, 0), (0, 1))

    def test_flip_second_match_both_cards_face_up(self):
        """Both matched cards are face up."""
        cards = [[Card("Y"), Card("Y")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("charlie")

        board._flip_second_immediate("charlie", 0, 1)

        card2 = board._get_card(0, 1)
        assert card1.face_up
        assert card2.face_up

    def test_flip_second_match_face_down_card(self):
        """Matching with a face-down card flips it up."""
        cards = [[Card("Z"), Card("Z")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        # Second card is face down
        card2 = board._get_card(0, 1)
        assert not card2.face_up

        board._flip_second_immediate("alice", 0, 1)

        # Second card now face up
        assert card2.face_up

    def test_flip_second_match_face_up_uncontrolled(self):
        """Can match with a face-up uncontrolled card."""
        cards = [[Card("A"), Card("A")]]
        board = Board(1, 2, cards)

        # Second card already face up but uncontrolled
        card2 = board._get_card(0, 1)
        card2.flip_up()

        player = board._get_or_create_player("bob")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("bob")

        board._flip_second_immediate("bob", 0, 1)

        # Match succeeds
        assert card2.controller == "bob"
        assert player.matched_pair == ((0, 0), (0, 1))


class TestFlipSecondMismatch:
    """Tests for Rule 2-E: mismatch."""

    def test_flip_second_mismatch_relinquishes_both(self):
        """Mismatched cards causes both to be relinquished."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        board._flip_second_immediate("alice", 0, 1)

        card2 = board._get_card(0, 1)

        # Both cards relinquished
        assert card1.controller is None
        assert card2.controller is None

    def test_flip_second_mismatch_both_remain_face_up(self):
        """Mismatched cards remain face up."""
        cards = [[Card("X"), Card("Y")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("bob")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("bob")

        board._flip_second_immediate("bob", 0, 1)

        card2 = board._get_card(0, 1)
        assert card1.face_up
        assert card2.face_up

    def test_flip_second_mismatch_tracks_for_cleanup(self):
        """Mismatched cards tracked in player state for cleanup."""
        cards = [[Card("P"), Card("Q")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("charlie")

        board._flip_second_immediate("charlie", 0, 1)

        # Both positions tracked for turn boundary cleanup
        assert player.first_card == (0, 0)
        assert player.second_card == (0, 1)

    def test_flip_second_mismatch_no_match_marker(self):
        """Mismatched cards don't set matched_pair."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        card1 = board._get_card(0, 0)
        card1.flip_up()
        card1.set_controller("alice")

        board._flip_second_immediate("alice", 0, 1)

        # No match marker
        assert player.matched_pair is None


class TestFlipSecondIntegration:
    """Integration tests for second flip."""

    def test_complete_match_sequence(self):
        """Full sequence: first flip, second flip match."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # First flip
        board._flip_first_immediate("alice", 0, 0)

        alice = board._get_or_create_player("alice")
        assert alice.first_card == (0, 0)

        # Second flip (match)
        board._flip_second_immediate("alice", 0, 1)

        assert alice.second_card == (0, 1)
        assert alice.matched_pair == ((0, 0), (0, 1))

    def test_complete_mismatch_sequence(self):
        """Full sequence: first flip, second flip mismatch."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # First flip
        board._flip_first_immediate("bob", 0, 0)

        # Second flip (mismatch)
        board._flip_second_immediate("bob", 0, 1)

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)

        # Both face up, uncontrolled
        assert card1.face_up and card1.controller is None
        assert card2.face_up and card2.controller is None

    def test_match_then_cleanup_then_new_turn(self):
        """Match, cleanup, then new first flip."""
        cards = [[Card("X"), Card("X")], [Card("Y"), Card("Y")]]
        board = Board(2, 2, cards)

        # First turn: match
        board._flip_first_immediate("alice", 0, 0)
        board._flip_second_immediate("alice", 0, 1)

        # Second turn: cleanup happens automatically
        board._flip_first_immediate("alice", 1, 0)

        # Old cards removed
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        assert not card1.on_board
        assert not card2.on_board

        # New card controlled
        card3 = board._get_card(1, 0)
        assert card3.controller == "alice"

    def test_mismatch_then_cleanup_then_new_turn(self):
        """Mismatch, cleanup, then new first flip."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # First turn: mismatch
        board._flip_first_immediate("bob", 0, 0)
        board._flip_second_immediate("bob", 0, 1)

        # Second turn: cleanup happens automatically
        board._flip_first_immediate("bob", 1, 0)

        # Old cards flipped down
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        assert not card1.face_up
        assert not card2.face_up

        # New card controlled
        card3 = board._get_card(1, 0)
        assert card3.controller == "bob"

    def test_multiple_players_independent_flips(self):
        """Multiple players can flip independently."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # Alice's turn
        board._flip_first_immediate("alice", 0, 0)
        board._flip_second_immediate("alice", 0, 1)

        # Bob's turn
        board._flip_first_immediate("bob", 1, 0)
        board._flip_second_immediate("bob", 1, 1)

        # Both have matched pairs
        alice = board._get_or_create_player("alice")
        bob = board._get_or_create_player("bob")

        assert alice.matched_pair == ((0, 0), (0, 1))
        assert bob.matched_pair == ((1, 0), (1, 1))

    def test_flip_second_preserves_invariants(self):
        """Second flip maintains board invariants."""
        cards = [[Card("X"), Card("X")]]
        board = Board(1, 2, cards)

        board._flip_first_immediate("alice", 0, 0)
        board._flip_second_immediate("alice", 0, 1)

        # Should not raise
        board._check_rep()
