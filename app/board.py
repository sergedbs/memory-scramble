# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import asyncio
from typing import Optional, Tuple, Set
from dataclasses import dataclass


class FlipError(Exception):
    """Exception raised when a flip operation fails according to game rules."""

    pass


class Card:
    """
    Represents a single card on the Memory Scramble board.

    A card has a value (text), can be on or off the board, face up or down,
    and can be controlled by a player.

    Mutable.
    """

    def __init__(self, value: str):
        """
        Create a new card with the given value.

        @param value: card text, must be non-empty and contain no whitespace
        @raises ValueError if value is invalid
        """
        if not value or not value.strip():
            raise ValueError("Card value must be non-empty")
        if any(c.isspace() for c in value):
            raise ValueError("Card value must not contain whitespace")

        self.value: str = value
        self.on_board: bool = True
        self.face_up: bool = False
        self.controller: Optional[str] = None
        self.last_controller: Optional[str] = None

        self._check_rep()

    def remove(self) -> None:
        """
        Remove this card from the board (as part of a matched pair).
        Card becomes not on board, face down, and uncontrolled.
        """
        self.on_board = False
        self.face_up = False
        self.controller = None
        self._check_rep()

    def flip_up(self) -> None:
        """Turn this card face up."""
        if not self.on_board:
            raise ValueError("Cannot flip up a removed card")
        self.face_up = True
        self._check_rep()

    def flip_down(self) -> None:
        """Turn this card face down."""
        if not self.on_board:
            raise ValueError("Cannot flip down a removed card")
        self.face_up = False
        self.controller = None  # Face-down cards cannot be controlled
        self._check_rep()

    def set_controller(self, player_id: Optional[str]) -> None:
        """
        Set who controls this card.

        @param player_id: player ID or None for no controller
        @raises ValueError if trying to control a face-down or removed card
        """
        if player_id is not None:
            if not self.on_board:
                raise ValueError("Cannot control a removed card")
            if not self.face_up:
                raise ValueError("Cannot control a face-down card")

        self.last_controller = self.controller
        self.controller = player_id
        self._check_rep()

    def _check_rep(self) -> None:
        """Verify representation invariants."""
        # Value must be non-empty and have no whitespace
        assert self.value, "Card value must be non-empty"
        assert not any(c.isspace() for c in self.value), (
            "Card value must not contain whitespace"
        )

        # Removed cards must be face down and uncontrolled
        if not self.on_board:
            assert not self.face_up, "Removed card must be face down"
            assert self.controller is None, "Removed card must be uncontrolled"

        # Face-down cards must be uncontrolled
        if not self.face_up:
            assert self.controller is None, "Face-down card must be uncontrolled"

    def __repr__(self) -> str:
        """String representation for debugging."""
        status = []
        if not self.on_board:
            status.append("removed")
        else:
            status.append("up" if self.face_up else "down")
            if self.controller:
                status.append(f"controlled by {self.controller}")
        return f"Card({self.value!r}, {', '.join(status)})"


@dataclass
class PlayerState:
    """
    Tracks per-player transient state during gameplay.

    A player can control at most two cards at a time (first and second flip).
    After a successful match, the matched pair is stored for removal on the
    next turn boundary.

    Mutable.
    """

    player_id: str
    first_card: Optional[Tuple[int, int]] = None
    second_card: Optional[Tuple[int, int]] = None
    matched_pair: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

    def __post_init__(self):
        """Validate player ID."""
        if not self.player_id:
            raise ValueError("Player ID must be non-empty")
        # Validate alphanumeric or underscore
        if not all(c.isalnum() or c == "_" for c in self.player_id):
            raise ValueError(
                "Player ID must contain only alphanumeric or underscore characters"
            )

    def has_control(self) -> bool:
        """
        @returns True if player currently controls any cards
        """
        return self.first_card is not None or self.second_card is not None

    def get_controlled_positions(self) -> Set[Tuple[int, int]]:
        """
        @returns set of all positions this player currently controls
        """
        positions = set()
        if self.first_card is not None:
            positions.add(self.first_card)
        if self.second_card is not None:
            positions.add(self.second_card)
        return positions

    def mark_match(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> None:
        """
        Record a matched pair for removal at next turn boundary.

        @param pos1: position of first card
        @param pos2: position of second card
        """
        self.matched_pair = (pos1, pos2)

    def clear_state(self) -> None:
        """Reset player state (after relinquishing or removing cards)."""
        self.first_card = None
        self.second_card = None
        self.matched_pair = None

    def __repr__(self) -> str:
        """String representation for debugging."""
        parts = [f"Player({self.player_id!r}"]
        if self.first_card:
            parts.append(f"first={self.first_card}")
        if self.second_card:
            parts.append(f"second={self.second_card}")
        if self.matched_pair:
            parts.append(f"matched={self.matched_pair}")
        return ", ".join(parts) + ")"


class Board:
    """
    Represents a Memory Scramble game board.

    A board is a grid of cards that players can flip to find matching pairs.
    The board tracks card states, player control, and enforces game rules.

    Mutable and concurrency safe (when used with proper locking).
    """

    def __init__(self, rows: int, cols: int, cards: list[list[Card]]):
        """
        Create a new board with the given dimensions and cards.

        @param rows: number of rows (positive integer)
        @param cols: number of columns (positive integer)
        @param cards: 2D list of Card objects (rows x cols)
        @raises ValueError: if dimensions are invalid or cards don't match dimensions
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Board dimensions must be positive")
        if len(cards) != rows:
            raise ValueError(f"Expected {rows} rows, got {len(cards)}")
        for i, row in enumerate(cards):
            if len(row) != cols:
                raise ValueError(f"Row {i} has {len(row)} cards, expected {cols}")

        self._rows = rows
        self._cols = cols
        self._grid: list[list[Card]] = cards
        self._players: dict[str, PlayerState] = {}

        # Concurrency primitives for Phase 5
        self._lock = asyncio.Lock()
        # Per-spot conditions for blocking on controlled cards (Rule 1-D)
        self._spot_conditions: dict[Tuple[int, int], asyncio.Condition] = {}
        # Version counter and condition for watch() support (Phase 6)
        self._version = 0
        self._watch_condition = asyncio.Condition(self._lock)

        self._check_rep()

    def size(self) -> Tuple[int, int]:
        """
        @returns (rows, cols) dimensions of the board
        """
        return (self._rows, self._cols)

    def _get_card(self, row: int, col: int) -> Card:
        """
        Internal: get card at position.

        @param row: row index (0-based)
        @param col: column index (0-based)
        @returns: Card at that position
        @raises IndexError: if position is out of bounds
        """
        return self._grid[row][col]

    def _get_or_create_player(self, player_id: str) -> PlayerState:
        """
        Internal: get or create player state.

        @param player_id: player identifier
        @returns: PlayerState for this player
        """
        if player_id not in self._players:
            self._players[player_id] = PlayerState(player_id)
        return self._players[player_id]

    def _cleanup_before_first_flip(self, player: PlayerState) -> list[Tuple[int, int]]:
        """
        Internal: apply turn boundary cleanup before a player's next first flip.

        Rule 3: Before a player flips their first card again:
        - If they previously matched (3-A): remove the matched pair, relinquish control
        - If they previously mismatched (3-B): flip down any eligible cards
          (still on board, face up, uncontrolled)

        NOTE: This is called from within async locked context, so notifications
        are handled by the calling async method.

        @param player: PlayerState to clean up
        @returns: list of positions that were modified (for notification)
        """
        positions_changed: list[Tuple[int, int]] = []

        # Rule 3-A: Remove matched pair
        if player.matched_pair is not None:
            pos1, pos2 = player.matched_pair
            card1 = self._get_card(*pos1)
            card2 = self._get_card(*pos2)

            # Remove both cards
            card1.remove()
            card2.remove()
            positions_changed.extend([pos1, pos2])

            # Clear player state
            player.clear_state()

        # Rule 3-B: Flip down relinquished cards
        elif player.first_card is not None or player.second_card is not None:
            # Check cards the player previously controlled but relinquished
            positions_to_check = []
            if player.first_card is not None:
                positions_to_check.append(player.first_card)
            if player.second_card is not None:
                positions_to_check.append(player.second_card)

            for pos in positions_to_check:
                card = self._get_card(*pos)
                # Only flip down if: still on board, face up, and uncontrolled
                if card.on_board and card.face_up and card.controller is None:
                    card.flip_down()
                    positions_changed.append(pos)

            # Clear player state
            player.clear_state()

        return positions_changed

    def _flip_first_immediate(
        self, player_id: str, row: int, col: int
    ) -> list[Tuple[int, int]]:
        """
        Internal: execute immediate (non-blocking) first card flip.

        Rule 1 (synchronous version - blocking handled in Phase 5):
        1-A: If no card (removed): raise FlipError
        1-B: If face down: flip up, grant control
        1-C: If face up and uncontrolled: grant control

        @param player_id: player making the flip
        @param row: row position
        @param col: column position
        @returns: list of positions that were modified by cleanup (for notification)
        @raises FlipError: if the flip fails according to game rules
        """
        self._validate_position(row, col)
        player = self._get_or_create_player(player_id)

        # Apply turn boundary cleanup
        positions_changed = self._cleanup_before_first_flip(player)

        card = self._get_card(row, col)

        # Rule 1-A: No card at position (removed)
        if not card.on_board:
            raise FlipError("Cannot flip a removed card")

        # Rule 1-B: Card is face down
        if not card.face_up:
            card.flip_up()
            card.set_controller(player_id)
            player.first_card = (row, col)
            return positions_changed

        # Rule 1-C: Card is face up and uncontrolled
        if card.controller is None:
            card.set_controller(player_id)
            player.first_card = (row, col)
            return positions_changed

        # Rule 1-D: Card is controlled by another player
        # For Phase 4, we raise an error. Phase 5 will add blocking/waiting.
        raise FlipError(
            f"Card at ({row}, {col}) is controlled by another player: {card.controller}"
        )

    def _flip_second_immediate(self, player_id: str, row: int, col: int) -> None:
        """
        Internal: execute immediate second card flip.

        Rule 2 (when player already controls one card):
        2-A: If no card (removed): fail, relinquish first card
        2-B: If face up and controlled: fail, relinquish first card
        2-C/D/E: If face down or (face up and uncontrolled):
            - Flip up if needed
            - If match: keep control of both
            - If no match: relinquish both

        @param player_id: player making the flip
        @param row: row position
        @param col: column position
        @raises FlipError: if the flip fails according to game rules
        """
        self._validate_position(row, col)
        player = self._get_or_create_player(player_id)

        # Player must control exactly one card
        if player.first_card is None:
            raise ValueError("Player must control first card before flipping second")
        if player.second_card is not None:
            raise ValueError("Player already has second card")

        first_pos = player.first_card
        first_card = self._get_card(*first_pos)
        second_card = self._get_card(row, col)

        # Rule 2-A: No card at position (removed)
        if not second_card.on_board:
            # Relinquish first card (remains face up, loses control)
            first_card.set_controller(None)
            player.first_card = None  # Mark for turn boundary cleanup
            raise FlipError("Cannot flip a removed card")

        # Rule 2-B: Card is face up and controlled (by anyone, including self)
        if second_card.face_up and second_card.controller is not None:
            # Relinquish first card
            first_card.set_controller(None)
            player.first_card = None  # Mark for turn boundary cleanup
            raise FlipError(f"Card at ({row}, {col}) is already controlled")

        # Rules 2-C/D/E: Card is available (face down or face up & uncontrolled)

        # Rule 2-C: Flip up if face down
        if not second_card.face_up:
            second_card.flip_up()

        # Grant control of second card
        second_card.set_controller(player_id)
        player.second_card = (row, col)

        # Rule 2-D: Check for match
        if first_card.value == second_card.value:
            # Match! Keep control of both, mark for removal at turn boundary
            player.mark_match(first_pos, (row, col))
        else:
            # Rule 2-E: No match - relinquish both (they remain face up)
            first_card.set_controller(None)
            second_card.set_controller(None)
            # Leave positions in player state for turn boundary cleanup

    async def flip_first(self, player_id: str, row: int, col: int) -> None:
        """
        Async first card flip with blocking/waiting support.

        Rule 1-D: If card is controlled by another player, waits (non-busy) until available.
        Once available, attempts to flip. May fail if card was removed while waiting.

        @param player_id: player making the flip
        @param row: row position
        @param col: column position
        @raises FlipError: if the flip fails according to game rules
        """
        self._validate_position(row, col)

        async with self._lock:
            card = self._get_card(row, col)

            # Check if card is controlled by another player (Rule 1-D)
            while card.on_board and card.face_up and card.controller is not None:
                # Need to wait for card to become available
                # Get or create per-spot condition
                spot_key = (row, col)
                if spot_key not in self._spot_conditions:
                    self._spot_conditions[spot_key] = asyncio.Condition(self._lock)

                condition = self._spot_conditions[spot_key]
                await condition.wait()

                # Re-check card state after waking up
                card = self._get_card(row, col)

            # Now card is available (or removed) - attempt immediate flip
            positions_changed = self._flip_first_immediate(player_id, row, col)

            # Notify waiters on positions affected by cleanup
            for pos in positions_changed:
                self._release_spot(*pos)

            # Notify watchers of board change
            self._notify_watchers()

    async def flip_second(self, player_id: str, row: int, col: int) -> None:
        """
        Async second card flip.

        No blocking for second flip (Rule 2-B: controlled cards fail immediately).
        When control is relinquished, notifies waiting players on those spots.

        @param player_id: player making the flip
        @param row: row position
        @param col: column position
        @raises FlipError: if the flip fails according to game rules
        """
        async with self._lock:
            player = self._get_or_create_player(player_id)
            first_pos = player.first_card

            try:
                self._flip_second_immediate(player_id, row, col)
            except FlipError:
                # If second flip failed, first card was relinquished
                # Notify anyone waiting on the first card's spot
                if first_pos is not None:
                    self._release_spot(*first_pos)
                raise

            # Check if cards were relinquished (mismatch)
            # If neither card is controlled, notify waiters on both spots
            if first_pos is not None:
                first_card = self._get_card(*first_pos)
                if first_card.controller is None:
                    self._release_spot(*first_pos)

            second_card = self._get_card(row, col)
            if second_card.controller is None:
                self._release_spot(row, col)

            # Notify watchers of board change
            self._notify_watchers()

    async def flip(self, player_id: str, row: int, col: int) -> None:
        """
        Unified flip operation - routes to first or second flip based on player state.

        Automatically determines if this is a first or second flip attempt based on
        whether the player currently controls a card. Important: this check happens
        BEFORE cleanup, so a player with matched_pair set will route to flip_first
        (which triggers cleanup and then flips the new card).

        @param player_id: player making the flip
        @param row: row position
        @param col: column position
        @raises FlipError: if the flip fails according to game rules
        """
        # We need to check player state to route, but flip_first will handle cleanup
        # Acquire lock briefly just to check state
        async with self._lock:
            player = self._get_or_create_player(player_id)
            # Check if player has cards that are still active (not cleaned up)
            # A player routes to flip_first if:
            # - They have no cards, OR
            # - They have a matched_pair (cleanup will clear it), OR
            # - They have relinquished cards (cleanup will clear them)
            # A player routes to flip_second only if they have first_card and no second_card
            # and no matched_pair (actively controlling one card)
            has_active_first = (
                player.first_card is not None
                and player.second_card is None
                and player.matched_pair is None
            )

        # Release lock before calling flip methods (they acquire it themselves)
        if has_active_first:
            await self.flip_second(player_id, row, col)
        else:
            await self.flip_first(player_id, row, col)

    def _notify_watchers(self) -> None:
        """
        Internal: notify all watchers that the board has changed.
        Increments version counter and wakes up all waiting watch() calls.
        """
        self._version += 1
        self._watch_condition.notify_all()

    def _release_spot(self, row: int, col: int) -> None:
        """
        Internal: release control of a spot and notify ALL waiting players.

        This wakes up ALL waiters, not just one, because when a card is removed
        all waiters need to wake up and realize the card is gone.

        @param row: row position
        @param col: column position
        """
        spot_key = (row, col)
        if spot_key in self._spot_conditions:
            # Wake up ALL waiters (they will re-check card state)
            self._spot_conditions[spot_key].notify_all()

    def _validate_position(self, row: int, col: int) -> None:
        """
        Internal: raise if position is out of bounds.

        @param row: row index
        @param col: column index
        @raises ValueError: if position is invalid
        """
        if row < 0 or row >= self._rows:
            raise ValueError(f"Row {row} out of bounds [0, {self._rows})")
        if col < 0 or col >= self._cols:
            raise ValueError(f"Column {col} out of bounds [0, {self._cols})")

    def _check_rep(self) -> None:
        """Verify representation invariants."""
        # Dimensions must be positive
        assert self._rows > 0, "Rows must be positive"
        assert self._cols > 0, "Columns must be positive"

        # Grid must match dimensions
        assert len(self._grid) == self._rows, "Grid rows mismatch"
        for i, row in enumerate(self._grid):
            assert len(row) == self._cols, f"Grid row {i} columns mismatch"

        # All removed cards must come in matching pairs
        removed_values: dict[str, int] = {}
        for row in self._grid:
            for card in row:
                if not card.on_board:
                    removed_values[card.value] = removed_values.get(card.value, 0) + 1

        for value, count in removed_values.items():
            assert count % 2 == 0, f"Removed cards for '{value}' not in pairs: {count}"

    def __str__(self) -> str:
        """String representation showing board dimensions."""
        return f"Board({self._rows}x{self._cols})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Board({self._rows}x{self._cols}, {len(self._players)} players)"

    def look(self, player_id: str) -> str:
        """
        Generate board state from a player's perspective.

        Returns a textual representation showing:
        - "none" for removed cards
        - "down" for face-down cards
        - "up CARD" for face-up cards controlled by others or uncontrolled
        - "my CARD" for face-up cards controlled by this player

        Format:
        ROWxCOL
        SPOT
        SPOT
        ...

        Where each SPOT is one of the above representations,
        in row-major order (top-left to bottom-right).

        @param player_id: ID of the player viewing the board
        @returns: textual board state
        """
        # Validate player_id format
        if not player_id:
            raise ValueError("Player ID must be non-empty")
        if not all(c.isalnum() or c == "_" for c in player_id):
            raise ValueError(
                "Player ID must contain only alphanumeric or underscore characters"
            )

        # Build the board state string
        lines = [f"{self._rows}x{self._cols}"]

        for r in range(self._rows):
            for c in range(self._cols):
                card = self._get_card(r, c)

                if not card.on_board:
                    # Card has been removed
                    lines.append("none")
                elif not card.face_up:
                    # Card is face down
                    lines.append("down")
                elif card.controller == player_id:
                    # Card is face up and controlled by this player
                    lines.append(f"my {card.value}")
                else:
                    # Card is face up but controlled by another player or no one
                    lines.append(f"up {card.value}")

        return "\n".join(lines) + "\n"

    async def map(self, transformer) -> None:
        """
        Transform all card values using an async transformer function.

        Applies the transformer to every card's value on the board. The transformation
        maintains matching consistency: cards that matched before map() will still match
        after (they're transformed together). Does not change face-up/down state or control.

        Strategy:
        1. Group cards by current value (matching cards grouped together)
        2. Transform each group's value concurrently
        3. Commit each group atomically under lock
        4. Notify watchers after each group commit

        @param transformer: async function (old_value: str) -> new_value: str
        """
        # Phase 1: Collect all cards and group by value (outside lock)
        async with self._lock:
            # Build groups: value -> list of (row, col) positions
            value_groups: dict[str, list[Tuple[int, int]]] = {}
            for r in range(self._rows):
                for c in range(self._cols):
                    card = self._get_card(r, c)
                    if card.on_board:  # Only transform cards still on the board
                        if card.value not in value_groups:
                            value_groups[card.value] = []
                        value_groups[card.value].append((r, c))

        # Phase 2: Transform each unique value concurrently (outside lock)
        # Only transform if there are cards on the board
        if not value_groups:
            return  # No cards to transform

        transform_tasks = {}
        for old_value in value_groups.keys():
            transform_tasks[old_value] = asyncio.create_task(transformer(old_value))

        # Wait for all transformations to complete
        await asyncio.gather(*transform_tasks.values())

        # Phase 3: Commit each group atomically (under lock)
        for old_value, positions in value_groups.items():
            new_value = await transform_tasks[old_value]

            # Validate new value (same rules as Card constructor)
            if not new_value or not new_value.strip():
                raise ValueError("Transformed card value must be non-empty")
            if any(c.isspace() for c in new_value):
                raise ValueError("Transformed card value must not contain whitespace")

            # Atomically update all cards with this value
            async with self._lock:
                for row, col in positions:
                    card = self._get_card(row, col)
                    if card.on_board:  # Double-check card wasn't removed
                        card.value = new_value

                # Notify watchers after each group commit
                self._notify_watchers()

    async def watch(self) -> str:
        """
        Wait for the next board change, then return current board state.

        Blocks until any change occurs (card flipped, removed, or value changed),
        then returns a textual snapshot of the board from a neutral perspective.

        This is a long-polling operation that allows clients to be notified of
        board changes without repeatedly polling.

        @returns: textual board state (same format as look() but no player context)
        """
        async with self._lock:
            # Capture current version
            version_before = self._version

            # Wait until version changes
            while self._version == version_before:
                await self._watch_condition.wait()

            # Return current state (neutral observer - no "my" cards)
            # We'll use a dummy player ID that doesn't exist
            return self.look("_watcher_")

    @staticmethod
    async def parse_from_file(filename: str) -> "Board":
        """
        Make a new board by parsing a file.

        File format:
        ROWxCOL
        CARD1
        CARD2
        ...
        (empty line at end)

        PS4 instructions: the specification of this method may not be changed.

        @param filename path to game board file
        @returns a new board with the size and cards from the file
        @throws Error if the file cannot be read or is not a valid game board
        """
        import re
        import aiofiles

        try:
            # Read file asynchronously
            async with aiofiles.open(filename, "r", encoding="utf-8") as f:
                content = await f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Board file not found: {filename}")
        except Exception as e:
            raise ValueError(f"Error reading board file: {e}")

        # Split into lines (handle both \n and \r\n)
        lines = content.split("\n")
        # Remove \r if present (for cross-platform compatibility)
        lines = [line.rstrip("\r") for line in lines]

        # Remove any trailing empty lines beyond the first one
        # (file should end with exactly one empty line after the last card)
        while len(lines) > 2 and lines[-1] == "" and lines[-2] == "":
            lines.pop()

        if len(lines) < 2:
            raise ValueError("Board file must have at least header and one card")

        # Parse header: "ROWxCOL"
        header = lines[0]
        match = re.match(r"^(\d+)x(\d+)$", header)
        if not match:
            raise ValueError(f"Invalid header format: '{header}', expected 'ROWxCOL'")

        rows = int(match.group(1))
        cols = int(match.group(2))

        if rows <= 0 or cols <= 0:
            raise ValueError(f"Board dimensions must be positive: {rows}x{cols}")

        expected_cards = rows * cols

        # Lines should be: header + cards + empty line at end
        if len(lines) != expected_cards + 2:
            raise ValueError(
                f"Expected {expected_cards + 2} lines (header + {expected_cards} cards + empty line), "
                f"got {len(lines)}"
            )

        # Last line should be empty
        if lines[-1] != "":
            raise ValueError("Board file must end with an empty line")

        # Parse cards (lines 1 through rows*cols)
        card_lines = lines[1 : expected_cards + 1]

        # Build 2D grid of cards
        cards: list[list[Card]] = []
        for r in range(rows):
            row_cards: list[Card] = []
            for c in range(cols):
                card_text = card_lines[r * cols + c]

                # Validate card text
                if not card_text:
                    raise ValueError(f"Card at position ({r}, {c}) is empty")
                if any(ch.isspace() for ch in card_text):
                    raise ValueError(
                        f"Card at position ({r}, {c}) contains whitespace: '{card_text}'"
                    )

                row_cards.append(Card(card_text))
            cards.append(row_cards)

        return Board(rows, cols, cards)
