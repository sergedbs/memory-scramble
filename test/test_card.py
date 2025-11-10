# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import pytest
from app.board import Card


class TestCard:
    """
    Tests for the Card class.

    Testing strategy:
    - Card creation: valid values, invalid values (empty, whitespace)
    - State transitions: flip up/down, control assignment, removal
    - Representation invariants: face-down must be uncontrolled,
      removed must be face-down and uncontrolled
    - Edge cases: operations on removed cards
    """

    # Test card creation

    def test_create_valid_card_simple(self):
        """Test creating a card with simple text."""
        card = Card("A")
        assert card.value == "A"
        assert card.on_board is True
        assert card.face_up is False
        assert card.controller is None

    def test_create_valid_card_emoji(self):
        """Test creating a card with emoji."""
        card = Card("🦄")
        assert card.value == "🦄"
        assert card.on_board is True
        assert card.face_up is False

    def test_create_valid_card_multi_char(self):
        """Test creating a card with multiple characters (no spaces)."""
        card = Card("ABC123")
        assert card.value == "ABC123"

    def test_create_invalid_card_empty(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            Card("")

    def test_create_invalid_card_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            Card("   ")

    def test_create_invalid_card_contains_space(self):
        """Test that string with spaces raises ValueError."""
        with pytest.raises(ValueError, match="whitespace"):
            Card("A B")

    def test_create_invalid_card_contains_tab(self):
        """Test that string with tab raises ValueError."""
        with pytest.raises(ValueError, match="whitespace"):
            Card("A\tB")

    def test_create_invalid_card_contains_newline(self):
        """Test that string with newline raises ValueError."""
        with pytest.raises(ValueError, match="whitespace"):
            Card("A\nB")

    # Test flip operations

    def test_flip_up_from_down(self):
        """Test flipping a face-down card up."""
        card = Card("A")
        assert card.face_up is False

        card.flip_up()
        assert card.face_up is True
        assert card.on_board is True

    def test_flip_down_from_up(self):
        """Test flipping a face-up card down."""
        card = Card("A")
        card.flip_up()
        assert card.face_up is True

        card.flip_down()
        assert card.face_up is False

    def test_flip_down_clears_controller(self):
        """Test that flipping down removes controller."""
        card = Card("A")
        card.flip_up()
        card.set_controller("player1")
        assert card.controller == "player1"

        card.flip_down()
        assert card.controller is None

    def test_flip_up_removed_card_fails(self):
        """Test that flipping up a removed card raises error."""
        card = Card("A")
        card.remove()

        with pytest.raises(ValueError, match="removed"):
            card.flip_up()

    def test_flip_down_removed_card_fails(self):
        """Test that flipping down a removed card raises error."""
        card = Card("A")
        card.remove()

        with pytest.raises(ValueError, match="removed"):
            card.flip_down()

    # Test controller operations

    def test_set_controller_on_face_up_card(self):
        """Test setting controller on a face-up card."""
        card = Card("A")
        card.flip_up()

        card.set_controller("player1")
        assert card.controller == "player1"
        assert card.last_controller is None

    def test_set_controller_tracks_last_controller(self):
        """Test that last_controller is updated."""
        card = Card("A")
        card.flip_up()

        card.set_controller("player1")
        card.set_controller("player2")

        assert card.controller == "player2"
        assert card.last_controller == "player1"

    def test_clear_controller(self):
        """Test clearing controller by setting to None."""
        card = Card("A")
        card.flip_up()
        card.set_controller("player1")

        card.set_controller(None)
        assert card.controller is None
        assert card.last_controller == "player1"

    def test_set_controller_on_face_down_fails(self):
        """Test that controlling a face-down card raises error."""
        card = Card("A")
        assert card.face_up is False

        with pytest.raises(ValueError, match="face-down"):
            card.set_controller("player1")

    def test_set_controller_on_removed_fails(self):
        """Test that controlling a removed card raises error."""
        card = Card("A")
        card.remove()

        with pytest.raises(ValueError, match="removed"):
            card.set_controller("player1")

    # Test remove operation

    def test_remove_card(self):
        """Test removing a card from the board."""
        card = Card("A")
        card.flip_up()
        card.set_controller("player1")

        card.remove()

        assert card.on_board is False
        assert card.face_up is False
        assert card.controller is None

    def test_remove_already_removed(self):
        """Test removing an already removed card (should be safe)."""
        card = Card("A")
        card.remove()
        card.remove()  # Should not raise

        assert card.on_board is False

    # Test representation invariants

    def test_rep_invariant_removed_card_properties(self):
        """Test that removed cards maintain correct properties."""
        card = Card("A")
        card.flip_up()
        card.set_controller("player1")
        card.remove()

        # Removed card must be face down and uncontrolled
        assert not card.on_board
        assert not card.face_up
        assert card.controller is None

    def test_rep_invariant_face_down_uncontrolled(self):
        """Test that face-down cards cannot be controlled."""
        card = Card("A")
        card.flip_up()
        card.set_controller("player1")
        card.flip_down()

        # Flipping down should clear controller
        assert not card.face_up
        assert card.controller is None

    # Test __repr__ for debugging

    def test_repr_face_down(self):
        """Test string representation of face-down card."""
        card = Card("A")
        repr_str = repr(card)
        assert "A" in repr_str
        assert "down" in repr_str

    def test_repr_face_up_controlled(self):
        """Test string representation of controlled card."""
        card = Card("🦄")
        card.flip_up()
        card.set_controller("player1")
        repr_str = repr(card)
        assert "🦄" in repr_str
        assert "up" in repr_str
        assert "player1" in repr_str

    def test_repr_removed(self):
        """Test string representation of removed card."""
        card = Card("B")
        card.remove()
        repr_str = repr(card)
        assert "B" in repr_str
        assert "removed" in repr_str
