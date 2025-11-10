# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import pytest
import tempfile
import os
from app.board import Board, Card


class TestBoardParsing:
    """
    Tests for Board.parse_from_file() method.

    Testing strategy:
    - Valid board files: existing samples (ab.txt, perfect.txt, zoom.txt)
    - Invalid header: wrong format, non-numeric, negative numbers
    - Wrong number of cards: too few, too many
    - Invalid cards: empty, whitespace, newline
    - File errors: non-existent file
    - Edge cases: 1x1 board, large boards
    """

    # Test valid board files

    @pytest.mark.asyncio
    async def test_parse_perfect_board(self):
        """Test parsing the perfect.txt board (3x3 with emojis)."""
        board = await Board.parse_from_file("boards/perfect.txt")

        assert board.size() == (3, 3)

        # Check some specific cards
        card_00 = board._get_card(0, 0)
        assert card_00.value == "🦄"
        assert card_00.on_board is True
        assert card_00.face_up is False

        card_22 = board._get_card(2, 2)
        assert card_22.value == "🌈"

    @pytest.mark.asyncio
    async def test_parse_ab_board(self):
        """Test parsing the ab.txt board (5x5 with letters)."""
        board = await Board.parse_from_file("boards/ab.txt")

        assert board.size() == (5, 5)

        # Check some cards
        card_00 = board._get_card(0, 0)
        assert card_00.value == "A"

        card_01 = board._get_card(0, 1)
        assert card_01.value == "B"

    @pytest.mark.asyncio
    async def test_parse_zoom_board(self):
        """Test parsing the zoom.txt board if it exists."""
        if os.path.exists("boards/zoom.txt"):
            board = await Board.parse_from_file("boards/zoom.txt")
            rows, cols = board.size()
            assert rows > 0
            assert cols > 0

    # Test board initialization and queries

    @pytest.mark.asyncio
    async def test_parsed_board_size(self):
        """Test that parsed board reports correct size."""
        board = await Board.parse_from_file("boards/perfect.txt")
        rows, cols = board.size()
        assert rows == 3
        assert cols == 3

    @pytest.mark.asyncio
    async def test_parsed_board_cards_face_down(self):
        """Test that all parsed cards start face down."""
        board = await Board.parse_from_file("boards/perfect.txt")

        for r in range(3):
            for c in range(3):
                card = board._get_card(r, c)
                assert card.face_up is False
                assert card.on_board is True
                assert card.controller is None

    # Test invalid header formats

    @pytest.mark.asyncio
    async def test_parse_invalid_header_missing_x(self):
        """Test that header without 'x' raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("3 3\n")
            f.write("A\n" * 9)
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid header format"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_invalid_header_non_numeric(self):
        """Test that header with non-numeric values raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("AxB\n")
            f.write("A\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid header format"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_zero_dimensions(self):
        """Test that 0x0 board raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("0x0\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="positive"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_negative_dimensions(self):
        """Test that negative dimensions raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("-1x2\n")
            f.write("A\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid header format"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    # Test wrong number of cards

    @pytest.mark.asyncio
    async def test_parse_too_few_cards(self):
        """Test that file with too few cards raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("B\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Expected.*lines"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_too_many_cards(self):
        """Test that file with too many cards raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("B\n")
            f.write("C\n")
            f.write("D\n")
            f.write("E\n")  # Extra card
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Expected.*lines"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    # Test invalid card content

    @pytest.mark.asyncio
    async def test_parse_empty_card(self):
        """Test that empty card line raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("\n")  # Empty card
            f.write("B\n")
            f.write("C\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="empty"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_card_with_space(self):
        """Test that card with space raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("B C\n")  # Space in card
            f.write("D\n")
            f.write("E\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="whitespace"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_card_with_tab(self):
        """Test that card with tab raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("B\tC\n")  # Tab in card
            f.write("D\n")
            f.write("E\n")
            f.write("\n")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="whitespace"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    # Test missing empty line at end

    @pytest.mark.asyncio
    async def test_parse_missing_final_newline(self):
        """Test that file without final empty line raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x2\n")
            f.write("A\n")
            f.write("B\n")
            f.write("C\n")
            f.write("D")  # No newline at end
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="empty line"):
                await Board.parse_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    # Test file errors

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self):
        """Test that non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            await Board.parse_from_file("boards/nonexistent.txt")

    # Test edge cases

    @pytest.mark.asyncio
    async def test_parse_1x1_board(self):
        """Test parsing a minimal 1x1 board."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("1x1\n")
            f.write("X\n")
            f.write("\n")
            temp_file = f.name

        try:
            board = await Board.parse_from_file(temp_file)
            assert board.size() == (1, 1)
            card = board._get_card(0, 0)
            assert card.value == "X"
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_1x10_board(self):
        """Test parsing a wide 1x10 board."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("1x10\n")
            for i in range(10):
                f.write(f"{i}\n")
            f.write("\n")
            temp_file = f.name

        try:
            board = await Board.parse_from_file(temp_file)
            assert board.size() == (1, 10)
            for i in range(10):
                card = board._get_card(0, i)
                assert card.value == str(i)
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_board_with_complex_emoji(self):
        """Test parsing cards with complex emojis."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("2x2\n")
            f.write("👨‍👩‍👧‍👦\n")  # Family emoji (composite)
            f.write("🏳️‍🌈\n")  # Rainbow flag
            f.write("👨‍👩‍👧‍👦\n")
            f.write("🏳️‍🌈\n")
            f.write("\n")
            temp_file = f.name

        try:
            board = await Board.parse_from_file(temp_file)
            assert board.size() == (2, 2)
            # Just verify it parses without error
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_parse_board_row_major_order(self):
        """Test that cards are filled in row-major order."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("2x3\n")
            # Row 0: A B C
            # Row 1: D E F
            f.write("A\n")
            f.write("B\n")
            f.write("C\n")
            f.write("D\n")
            f.write("E\n")
            f.write("F\n")
            f.write("\n")
            temp_file = f.name

        try:
            board = await Board.parse_from_file(temp_file)
            assert board.size() == (2, 3)

            # Check row 0
            assert board._get_card(0, 0).value == "A"
            assert board._get_card(0, 1).value == "B"
            assert board._get_card(0, 2).value == "C"

            # Check row 1
            assert board._get_card(1, 0).value == "D"
            assert board._get_card(1, 1).value == "E"
            assert board._get_card(1, 2).value == "F"
        finally:
            os.unlink(temp_file)


class TestBoardConstruction:
    """
    Tests for Board constructor and basic operations.
    """

    def test_create_board_direct(self):
        """Test creating a board directly with cards."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        assert board.size() == (2, 2)
        assert board._get_card(0, 0).value == "A"
        assert board._get_card(1, 1).value == "D"

    def test_create_board_invalid_dimensions(self):
        """Test that invalid dimensions raise error."""
        cards = [[Card("A")]]

        with pytest.raises(ValueError, match="positive"):
            Board(0, 1, cards)

        with pytest.raises(ValueError, match="positive"):
            Board(1, -1, cards)

    def test_create_board_dimension_mismatch_rows(self):
        """Test that wrong number of rows raises error."""
        cards = [[Card("A"), Card("B")]]

        with pytest.raises(ValueError, match="Expected 2 rows"):
            Board(2, 2, cards)

    def test_create_board_dimension_mismatch_cols(self):
        """Test that wrong number of columns raises error."""
        cards = [
            [Card("A"), Card("B")],
            [Card("C")],  # Wrong number of columns
        ]

        with pytest.raises(ValueError, match="expected 2"):
            Board(2, 2, cards)

    def test_board_str(self):
        """Test string representation."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        str_repr = str(board)
        assert "1x2" in str_repr

    def test_board_repr(self):
        """Test detailed representation."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        repr_str = repr(board)
        assert "1x2" in repr_str
        assert "0 players" in repr_str

    def test_validate_position_valid(self):
        """Test that valid positions don't raise errors."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        # Should not raise
        board._validate_position(0, 0)
        board._validate_position(1, 1)
        board._validate_position(0, 1)
        board._validate_position(1, 0)

    def test_validate_position_invalid(self):
        """Test that invalid positions raise errors."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        with pytest.raises(ValueError, match="out of bounds"):
            board._validate_position(-1, 0)

        with pytest.raises(ValueError, match="out of bounds"):
            board._validate_position(0, -1)

        with pytest.raises(ValueError, match="out of bounds"):
            board._validate_position(2, 0)

        with pytest.raises(ValueError, match="out of bounds"):
            board._validate_position(0, 2)

    def test_get_or_create_player_new(self):
        """Test creating a new player."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        player = board._get_or_create_player("alice")
        assert player.player_id == "alice"
        assert not player.has_control()

    def test_get_or_create_player_existing(self):
        """Test getting an existing player."""
        cards = [[Card("A")]]
        board = Board(1, 1, cards)

        player1 = board._get_or_create_player("bob")
        player1.first_card = (0, 0)

        player2 = board._get_or_create_player("bob")

        assert player1 is player2  # Same object
        assert player2.first_card == (0, 0)
