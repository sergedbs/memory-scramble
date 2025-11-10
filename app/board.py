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
    TODO specification
    Mutable and concurrency safe.
    """

    # TODO fields

    # Abstraction function:
    #   TODO
    # Representation invariant:
    #   TODO
    # Safety from rep exposure:
    #   TODO

    # TODO constructor

    # TODO checkRep

    # TODO other methods

    @staticmethod
    async def parse_from_file(filename: str) -> "Board":
        """
        Make a new board by parsing a file.

        PS4 instructions: the specification of this method may not be changed.

        @param filename path to game board file
        @returns a new board with the size and cards from the file
        @throws Error if the file cannot be read or is not a valid game board
        """
        return Board()  # TODO: implement this
