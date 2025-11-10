# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import pytest
from app.board import Board, Card


class TestBoardLook:
    """
    Tests for Board.look() method.

    Testing strategy:
    - Empty board (all cards face down)
    - Board with face-up cards
    - Board with removed cards
    - Multiple players with different perspectives
    - Player's own cards show "my"
    - Invalid player IDs
    """

    # Test basic look operation

    def test_look_empty_board_all_down(self):
        """Test looking at a board where all cards are face down."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        result = board.look("player1")
        lines = result.strip().split("\n")

        assert lines[0] == "2x2"
        assert lines[1] == "down"
        assert lines[2] == "down"
        assert lines[3] == "down"
        assert lines[4] == "down"

    def test_look_format_ends_with_newline(self):
        """Test that look() output ends with a newline."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        result = board.look("player1")
        assert result.endswith("\n")

    def test_look_header_format(self):
        """Test that header is in ROWxCOL format."""
        cards = [[Card("A"), Card("B"), Card("C")], [Card("D"), Card("E"), Card("F")]]
        board = Board(2, 3, cards)

        result = board.look("alice")
        lines = result.strip().split("\n")

        assert lines[0] == "2x3"

    # Test with face-up cards

    def test_look_with_face_up_uncontrolled(self):
        """Test looking at board with face-up uncontrolled cards."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Flip some cards face up but don't control them
        cards[0][0].flip_up()
        cards[1][1].flip_up()

        result = board.look("player1")
        lines = result.strip().split("\n")

        assert lines[0] == "2x2"
        assert lines[1] == "up A"  # Face up, uncontrolled
        assert lines[2] == "down"
        assert lines[3] == "down"
        assert lines[4] == "up D"  # Face up, uncontrolled

    def test_look_with_own_controlled_cards(self):
        """Test that player's own controlled cards show 'my'."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Player controls some cards
        cards[0][0].flip_up()
        cards[0][0].set_controller("alice")
        cards[1][1].flip_up()
        cards[1][1].set_controller("alice")

        result = board.look("alice")
        lines = result.strip().split("\n")

        assert lines[1] == "my A"  # Controlled by alice
        assert lines[2] == "down"
        assert lines[3] == "down"
        assert lines[4] == "my D"  # Controlled by alice

    def test_look_with_other_player_controlled_cards(self):
        """Test that other player's cards show 'up'."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Bob controls some cards
        cards[0][0].flip_up()
        cards[0][0].set_controller("bob")
        cards[1][1].flip_up()
        cards[1][1].set_controller("bob")

        # Alice looks at the board
        result = board.look("alice")
        lines = result.strip().split("\n")

        assert lines[1] == "up A"  # Controlled by bob, not alice
        assert lines[4] == "up D"  # Controlled by bob, not alice

    # Test with removed cards

    def test_look_with_removed_cards(self):
        """Test that removed cards show 'none'."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Remove some cards
        cards[0][0].remove()
        cards[1][1].remove()

        result = board.look("player1")
        lines = result.strip().split("\n")

        assert lines[1] == "none"
        assert lines[2] == "down"
        assert lines[3] == "down"
        assert lines[4] == "none"

    def test_look_mixed_states(self):
        """Test board with all different card states."""
        cards = [[Card("A"), Card("B"), Card("C")], [Card("D"), Card("E"), Card("F")]]
        board = Board(2, 3, cards)

        # Setup different states:
        # (0,0): removed
        # (0,1): face down
        # (0,2): face up, controlled by alice
        # (1,0): face up, controlled by bob
        # (1,1): face up, uncontrolled
        # (1,2): face down

        cards[0][0].remove()

        cards[0][2].flip_up()
        cards[0][2].set_controller("alice")

        cards[1][0].flip_up()
        cards[1][0].set_controller("bob")

        cards[1][1].flip_up()

        result = board.look("alice")
        lines = result.strip().split("\n")

        assert lines[0] == "2x3"
        assert lines[1] == "none"  # (0,0) removed
        assert lines[2] == "down"  # (0,1) face down
        assert lines[3] == "my C"  # (0,2) alice's card
        assert lines[4] == "up D"  # (1,0) bob's card
        assert lines[5] == "up E"  # (1,1) uncontrolled
        assert lines[6] == "down"  # (1,2) face down

    # Test multiple player perspectives

    def test_look_different_players_see_different_perspectives(self):
        """Test that different players see different 'my' vs 'up' for same card."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls first card, Bob controls second
        cards[0][0].flip_up()
        cards[0][0].set_controller("alice")
        cards[0][1].flip_up()
        cards[0][1].set_controller("bob")

        # Alice's perspective
        alice_view = board.look("alice")
        alice_lines = alice_view.strip().split("\n")
        assert alice_lines[1] == "my A"
        assert alice_lines[2] == "up B"

        # Bob's perspective
        bob_view = board.look("bob")
        bob_lines = bob_view.strip().split("\n")
        assert bob_lines[1] == "up A"
        assert bob_lines[2] == "my B"

    def test_look_neutral_observer(self):
        """Test that a player with no control sees all as 'up' or 'down'."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        # Alice controls first card
        cards[0][0].flip_up()
        cards[0][0].set_controller("alice")
        cards[0][1].flip_up()

        # Carol (neutral observer) looks
        carol_view = board.look("carol")
        carol_lines = carol_view.strip().split("\n")

        assert carol_lines[1] == "up A"  # Controlled by alice
        assert carol_lines[2] == "up B"  # Uncontrolled

    # Test row-major order

    def test_look_row_major_order(self):
        """Test that cards are listed in row-major order."""
        cards = [
            [Card("A"), Card("B"), Card("C")],
            [Card("D"), Card("E"), Card("F")],
            [Card("G"), Card("H"), Card("I")],
        ]
        board = Board(3, 3, cards)

        # Flip all cards face up to see their values
        for row in cards:
            for card in row:
                card.flip_up()

        result = board.look("viewer")
        lines = result.strip().split("\n")

        # Header + 9 cards
        assert len(lines) == 10
        assert lines[0] == "3x3"

        # Row 0: A B C
        assert "A" in lines[1]
        assert "B" in lines[2]
        assert "C" in lines[3]

        # Row 1: D E F
        assert "D" in lines[4]
        assert "E" in lines[5]
        assert "F" in lines[6]

        # Row 2: G H I
        assert "G" in lines[7]
        assert "H" in lines[8]
        assert "I" in lines[9]

    # Test with emoji cards

    def test_look_with_emoji_cards(self):
        """Test that emoji card values are displayed correctly."""
        cards = [[Card("🦄"), Card("🌈")], [Card("🦄"), Card("🌈")]]
        board = Board(2, 2, cards)

        # Flip some cards
        cards[0][0].flip_up()
        cards[0][1].flip_up()
        cards[0][1].set_controller("alice")

        result = board.look("alice")
        lines = result.strip().split("\n")

        assert lines[1] == "up 🦄"
        assert lines[2] == "my 🌈"
        assert lines[3] == "down"
        assert lines[4] == "down"

    # Test invalid player IDs

    def test_look_invalid_player_id_empty(self):
        """Test that empty player ID raises error."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        with pytest.raises(ValueError, match="non-empty"):
            board.look("")

    def test_look_invalid_player_id_special_chars(self):
        """Test that player ID with special characters raises error."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        with pytest.raises(ValueError, match="alphanumeric"):
            board.look("player-1")

    def test_look_invalid_player_id_space(self):
        """Test that player ID with space raises error."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        with pytest.raises(ValueError, match="alphanumeric"):
            board.look("player 1")

    # Test edge cases

    def test_look_1x1_board(self):
        """Test look on minimal 1x1 board."""
        cards = [[Card("X")]]
        board = Board(1, 1, cards)

        result = board.look("solo")
        lines = result.strip().split("\n")

        assert lines[0] == "1x1"
        assert lines[1] == "down"

    def test_look_large_board(self):
        """Test look on a larger board."""
        cards = [[Card(f"{i}{j}") for j in range(10)] for i in range(10)]
        board = Board(10, 10, cards)

        result = board.look("player1")
        lines = result.strip().split("\n")

        # Header + 100 cards
        assert len(lines) == 101
        assert lines[0] == "10x10"
        # All cards should be face down
        for i in range(1, 101):
            assert lines[i] == "down"

    def test_look_multiple_times_same_result(self):
        """Test that calling look multiple times gives same result."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        cards[0][0].flip_up()
        cards[0][0].set_controller("alice")

        result1 = board.look("alice")
        result2 = board.look("alice")
        result3 = board.look("alice")

        assert result1 == result2 == result3

    def test_look_is_read_only(self):
        """Test that look() doesn't modify board state."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        # look() should not create player state (read-only operation)
        board.look("observer")

        # Player state should not exist since look() is read-only
        assert "observer" not in board._players


class TestBoardLookIntegration:
    """
    Integration tests combining parsing and look operations.
    """

    @pytest.mark.asyncio
    async def test_look_after_parsing_perfect_board(self):
        """Test looking at a freshly parsed board."""
        board = await Board.parse_from_file("boards/perfect.txt")

        result = board.look("player1")
        lines = result.strip().split("\n")

        assert lines[0] == "3x3"
        # All 9 cards should be face down initially
        for i in range(1, 10):
            assert lines[i] == "down"

    @pytest.mark.asyncio
    async def test_look_after_parsing_ab_board(self):
        """Test looking at the ab.txt board."""
        board = await Board.parse_from_file("boards/ab.txt")

        result = board.look("viewer")
        lines = result.strip().split("\n")

        assert lines[0] == "5x5"
        # All 25 cards should be face down
        for i in range(1, 26):
            assert lines[i] == "down"
