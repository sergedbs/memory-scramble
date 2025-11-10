# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

"""
Tests for Board._cleanup_before_first_flip() - Rule 3 implementation.

Rule 3: Before a player's next first-card move (turn boundary):
  3-A: If they previously matched: remove the pair, relinquish control
  3-B: Otherwise (mismatch): flip down eligible cards
       (still on board, face up, currently uncontrolled)
"""

from app.board import Board, Card


class TestCleanupMatched:
    """Tests for cleanup after a matched pair (Rule 3-A)."""

    def test_cleanup_removes_matched_pair(self):
        """After a match, cleanup removes both cards from the board."""
        # 2x2 board: AA BB
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        # Simulate player matched A at (0,0) and (0,1)
        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)
        player.second_card = (0, 1)
        player.mark_match((0, 0), (0, 1))

        # Flip cards up and set controller to simulate match state
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("alice")
        card2.set_controller("alice")

        # Cleanup before next first flip
        board._cleanup_before_first_flip(player)

        # Both cards should be removed
        assert not card1.on_board
        assert not card2.on_board

        # Player state should be cleared
        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None

    def test_cleanup_clears_controller_on_removal(self):
        """Removed cards have no controller."""
        cards = [[Card("X"), Card("X")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("bob")
        player.mark_match((0, 0), (0, 1))

        # Set up matched cards
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("bob")
        card2.set_controller("bob")

        board._cleanup_before_first_flip(player)

        # Controllers should be cleared
        assert card1.controller is None
        assert card2.controller is None

    def test_cleanup_matched_cards_become_face_down(self):
        """Removed cards are face down."""
        cards = [[Card("Y"), Card("Y")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.mark_match((0, 0), (0, 1))

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("charlie")
        card2.set_controller("charlie")

        board._cleanup_before_first_flip(player)

        # Removed cards are face down
        assert not card1.face_up
        assert not card2.face_up


class TestCleanupMismatched:
    """Tests for cleanup after mismatched cards (Rule 3-B)."""

    def test_cleanup_flips_down_single_relinquished_card(self):
        """Single relinquished card that is face up and uncontrolled gets flipped down."""
        # 2x2 board: AB CD
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("alice")
        player.first_card = (0, 0)  # Relinquished after failed second flip

        # Card is face up and uncontrolled
        card = board._get_card(0, 0)
        card.flip_up()

        board._cleanup_before_first_flip(player)

        # Card should be flipped down
        assert not card.face_up
        assert player.first_card is None

    def test_cleanup_flips_down_two_relinquished_cards(self):
        """Both relinquished cards get flipped down if eligible."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("bob")
        player.first_card = (0, 0)
        player.second_card = (0, 1)  # Mismatched pair

        # Both face up and uncontrolled
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()

        board._cleanup_before_first_flip(player)

        # Both should be flipped down
        assert not card1.face_up
        assert not card2.face_up
        assert player.first_card is None
        assert player.second_card is None

    def test_cleanup_skips_controlled_cards(self):
        """Cards now controlled by another player are not flipped down."""
        cards = [[Card("A"), Card("B")], [Card("C"), Card("D")]]
        board = Board(2, 2, cards)

        player1 = board._get_or_create_player("alice")
        player1.first_card = (0, 0)

        # Card is face up but now controlled by another player
        card = board._get_card(0, 0)
        card.flip_up()
        card.set_controller("bob")  # Someone else controls it now

        board._cleanup_before_first_flip(player1)

        # Card should remain face up (not flipped down)
        assert card.face_up
        assert card.controller == "bob"

    def test_cleanup_skips_removed_cards(self):
        """Removed cards are not affected by cleanup."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.first_card = (0, 0)

        # Card was removed by another player
        card = board._get_card(0, 0)
        card.remove()

        # Should not crash
        board._cleanup_before_first_flip(player)

        # Card still removed
        assert not card.on_board

    def test_cleanup_skips_already_face_down_cards(self):
        """Cards already face down remain unchanged."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("david")
        player.first_card = (0, 0)

        # Card is already face down (someone else flipped it down)
        card = board._get_card(0, 0)
        # Card starts face down by default

        board._cleanup_before_first_flip(player)

        # Card still face down
        assert not card.face_up


class TestCleanupNoAction:
    """Tests for cleanup when player has no pending state."""

    def test_cleanup_with_no_pending_state(self):
        """Cleanup with no cards does nothing."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("alice")
        # Player has no first_card, second_card, or matched_pair

        # Should not crash
        board._cleanup_before_first_flip(player)

        # Player state remains empty
        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None

    def test_cleanup_clears_state_after_match(self):
        """Cleanup fully resets player state after match."""
        cards = [[Card("X"), Card("X")], [Card("Y"), Card("Y")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("bob")
        player.mark_match((0, 0), (0, 1))

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("bob")
        card2.set_controller("bob")

        board._cleanup_before_first_flip(player)

        # All state cleared
        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None

    def test_cleanup_clears_state_after_mismatch(self):
        """Cleanup fully resets player state after mismatch."""
        cards = [[Card("A"), Card("B")]]
        board = Board(1, 2, cards)

        player = board._get_or_create_player("charlie")
        player.first_card = (0, 0)
        player.second_card = (0, 1)

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()

        board._cleanup_before_first_flip(player)

        # All state cleared
        assert player.first_card is None
        assert player.second_card is None
        assert player.matched_pair is None


class TestCleanupIntegration:
    """Integration tests for cleanup behavior."""

    def test_cleanup_match_then_new_turn(self):
        """Player matches, cleanup removes cards, then starts fresh."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("alice")

        # Simulate match
        player.mark_match((0, 0), (0, 1))
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("alice")
        card2.set_controller("alice")

        # Cleanup before next first flip
        board._cleanup_before_first_flip(player)

        # Cards removed, player state clear
        assert not card1.on_board
        assert not card2.on_board
        assert player.first_card is None

        # Player can start fresh with remaining cards
        card3 = board._get_card(1, 0)
        assert card3.on_board
        assert not card3.face_up

    def test_cleanup_preserves_board_invariants(self):
        """Cleanup maintains board representation invariants."""
        cards = [[Card("X"), Card("X")], [Card("Y"), Card("Y")]]
        board = Board(2, 2, cards)

        player = board._get_or_create_player("bob")
        player.mark_match((0, 0), (0, 1))

        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("bob")
        card2.set_controller("bob")

        board._cleanup_before_first_flip(player)

        # Should not raise assertion error
        board._check_rep()

    def test_cleanup_multiple_players_independent(self):
        """Each player's cleanup is independent."""
        cards = [[Card("A"), Card("A")], [Card("B"), Card("B")]]
        board = Board(2, 2, cards)

        alice = board._get_or_create_player("alice")
        bob = board._get_or_create_player("bob")

        # Alice has matched pair
        alice.mark_match((0, 0), (0, 1))
        card1 = board._get_card(0, 0)
        card2 = board._get_card(0, 1)
        card1.flip_up()
        card2.flip_up()
        card1.set_controller("alice")
        card2.set_controller("alice")

        # Bob has relinquished cards
        bob.first_card = (1, 0)
        bob.second_card = (1, 1)
        card3 = board._get_card(1, 0)
        card4 = board._get_card(1, 1)
        card3.flip_up()
        card4.flip_up()

        # Alice's cleanup
        board._cleanup_before_first_flip(alice)
        assert not card1.on_board
        assert not card2.on_board
        assert alice.first_card is None

        # Bob's state unchanged
        assert bob.first_card == (1, 0)
        assert bob.second_card == (1, 1)

        # Bob's cleanup
        board._cleanup_before_first_flip(bob)
        assert not card3.face_up
        assert not card4.face_up
        assert bob.first_card is None
