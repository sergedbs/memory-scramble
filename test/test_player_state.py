# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import pytest
from app.board import PlayerState


class TestPlayerState:
    """
    Tests for the PlayerState class.

    Testing strategy:
    - Creation: valid and invalid player IDs
    - State transitions: none → first → second → matched/relinquished
    - Query methods: has_control, get_controlled_positions
    - Cleanup: clear_state
    """

    # Test player state creation

    def test_create_valid_player_simple(self):
        """Test creating a player with simple alphanumeric ID."""
        player = PlayerState("player1")
        assert player.player_id == "player1"
        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None

    def test_create_valid_player_uppercase(self):
        """Test creating a player with uppercase letters."""
        player = PlayerState("ALICE")
        assert player.player_id == "ALICE"

    def test_create_valid_player_underscore(self):
        """Test creating a player with underscores."""
        player = PlayerState("player_1")
        assert player.player_id == "player_1"

    def test_create_valid_player_numbers(self):
        """Test creating a player with only numbers."""
        player = PlayerState("123")
        assert player.player_id == "123"

    def test_create_invalid_player_empty(self):
        """Test that empty player ID raises error."""
        with pytest.raises(ValueError, match="non-empty"):
            PlayerState("")

    def test_create_invalid_player_special_chars(self):
        """Test that special characters raise error."""
        with pytest.raises(ValueError, match="alphanumeric"):
            PlayerState("player-1")

    def test_create_invalid_player_space(self):
        """Test that spaces raise error."""
        with pytest.raises(ValueError, match="alphanumeric"):
            PlayerState("player 1")

    def test_create_invalid_player_symbols(self):
        """Test that symbols raise error."""
        with pytest.raises(ValueError, match="alphanumeric"):
            PlayerState("player@home")

    # Test has_control method

    def test_has_control_initially_false(self):
        """Test that new player has no control."""
        player = PlayerState("player1")
        assert player.has_control() is False

    def test_has_control_with_first_card(self):
        """Test that player with first card has control."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        assert player.has_control() is True

    def test_has_control_with_second_card(self):
        """Test that player with second card has control."""
        player = PlayerState("player1")
        player.second_card = (1, 1)
        assert player.has_control() is True

    def test_has_control_with_both_cards(self):
        """Test that player with both cards has control."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        player.second_card = (1, 1)
        assert player.has_control() is True

    def test_has_control_after_clear(self):
        """Test that has_control returns False after clear."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        player.clear_state()
        assert player.has_control() is False

    # Test get_controlled_positions method

    def test_get_controlled_positions_empty(self):
        """Test that new player controls no positions."""
        player = PlayerState("player1")
        positions = player.get_controlled_positions()
        assert positions == set()

    def test_get_controlled_positions_first_only(self):
        """Test getting positions with only first card."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        positions = player.get_controlled_positions()
        assert positions == {(0, 0)}

    def test_get_controlled_positions_second_only(self):
        """Test getting positions with only second card."""
        player = PlayerState("player1")
        player.second_card = (1, 1)
        positions = player.get_controlled_positions()
        assert positions == {(1, 1)}

    def test_get_controlled_positions_both(self):
        """Test getting positions with both cards."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        player.second_card = (1, 1)
        positions = player.get_controlled_positions()
        assert positions == {(0, 0), (1, 1)}

    def test_get_controlled_positions_returns_copy(self):
        """Test that returned set is independent (for safety)."""
        player = PlayerState("player1")
        player.first_card = (0, 0)

        positions1 = player.get_controlled_positions()
        positions2 = player.get_controlled_positions()

        # Should be equal but not the same object
        assert positions1 == positions2
        assert positions1 is not positions2

    # Test mark_match method

    def test_mark_match_simple(self):
        """Test marking a matched pair."""
        player = PlayerState("player1")
        player.mark_match((0, 0), (1, 1))

        assert player.matched_pair == ((0, 0), (1, 1))

    def test_mark_match_overwrites_previous(self):
        """Test that new match overwrites old match."""
        player = PlayerState("player1")
        player.mark_match((0, 0), (1, 1))
        player.mark_match((2, 2), (3, 3))

        assert player.matched_pair == ((2, 2), (3, 3))

    # Test clear_state method

    def test_clear_state_clears_first_card(self):
        """Test that clear_state removes first card."""
        player = PlayerState("player1")
        player.first_card = (0, 0)

        player.clear_state()

        assert player.first_card is None

    def test_clear_state_clears_second_card(self):
        """Test that clear_state removes second card."""
        player = PlayerState("player1")
        player.second_card = (1, 1)

        player.clear_state()

        assert player.second_card is None

    def test_clear_state_clears_matched_pair(self):
        """Test that clear_state removes matched pair."""
        player = PlayerState("player1")
        player.mark_match((0, 0), (1, 1))

        player.clear_state()

        assert player.matched_pair is None

    def test_clear_state_clears_all(self):
        """Test that clear_state removes all state."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        player.second_card = (1, 1)
        player.mark_match((0, 0), (1, 1))

        player.clear_state()

        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None
        assert not player.has_control()

    def test_clear_state_idempotent(self):
        """Test that clearing already cleared state is safe."""
        player = PlayerState("player1")
        player.clear_state()
        player.clear_state()  # Should not raise

        assert not player.has_control()

    # Test state transitions (game flow scenarios)

    def test_transition_none_to_first(self):
        """Test transition from no control to first card."""
        player = PlayerState("player1")
        assert not player.has_control()

        player.first_card = (0, 0)

        assert player.has_control()
        assert player.first_card == (0, 0)
        assert player.second_card is None

    def test_transition_first_to_second_match(self):
        """Test transition from first to second card (match)."""
        player = PlayerState("player1")
        player.first_card = (0, 0)

        player.second_card = (1, 1)
        player.mark_match((0, 0), (1, 1))

        assert player.first_card == (0, 0)
        assert player.second_card == (1, 1)
        assert player.matched_pair == ((0, 0), (1, 1))

    def test_transition_first_to_relinquish(self):
        """Test transition from first card to relinquish (fail)."""
        player = PlayerState("player1")
        player.first_card = (0, 0)

        player.clear_state()  # Relinquish

        assert not player.has_control()
        assert player.first_card is None

    def test_transition_matched_to_removed(self):
        """Test transition from matched to removed (cleanup)."""
        player = PlayerState("player1")
        player.first_card = (0, 0)
        player.second_card = (1, 1)
        player.mark_match((0, 0), (1, 1))

        # Simulate removal at turn boundary
        player.clear_state()

        assert not player.has_control()
        assert player.matched_pair is None

    # Test __repr__ for debugging

    def test_repr_no_control(self):
        """Test string representation with no control."""
        player = PlayerState("alice")
        repr_str = repr(player)
        assert "alice" in repr_str

    def test_repr_with_first_card(self):
        """Test string representation with first card."""
        player = PlayerState("bob")
        player.first_card = (2, 3)
        repr_str = repr(player)
        assert "bob" in repr_str
        assert "first" in repr_str
        assert "(2, 3)" in repr_str

    def test_repr_with_matched_pair(self):
        """Test string representation with matched pair."""
        player = PlayerState("carol")
        player.mark_match((0, 0), (1, 1))
        repr_str = repr(player)
        assert "carol" in repr_str
        assert "matched" in repr_str
