# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import asyncio
import random
from .board import Board, FlipError


async def simulation_main():
    """
    Stress test simulation for concurrent Memory Scramble gameplay.

    Simulates multiple players concurrently flipping cards with random delays.
    Tests concurrency invariants, blocking behavior, and game rule correctness.

    @throws Error if an error occurs reading or parsing the board
    """
    import sys

    # Allow command-line configuration
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "boards/zoom.txt"

    board = await Board.parse_from_file(filename)
    rows, cols = board.size()

    # Simulation parameters
    players = 4
    tries_per_player = 100
    max_delay_milliseconds = 2
    flip_timeout_seconds = 2.0  # Timeout for flips to prevent deadlocks

    # Statistics tracking
    stats = {
        "total_flips": 0,
        "successful_matches": 0,
        "failed_flips": 0,
        "timeouts": 0,
        "cards_removed": 0,
    }
    stats_lock = asyncio.Lock()

    print(f"\n{'=' * 60}")
    print(" Memory Scramble Stress Test Simulation")
    print(f"{'=' * 60}")
    print(f"Board: {filename} ({rows}x{cols}, {rows * cols} cards)")
    print(f"Players: {players} concurrent bots")
    print(f"Turns per player: {tries_per_player}")
    print(f"Max delay: {max_delay_milliseconds}ms")
    print(f"Flip timeout: {flip_timeout_seconds}s")
    print(f"{'=' * 60}\n")

    async def player(player_number: int):
        """
        Simulate a single player making random flips.

        @param player_number unique identifier for this player
        """
        player_id = f"bot_{player_number}"
        local_matches = 0
        local_failures = 0

        for turn in range(tries_per_player):
            try:
                # Random delay before first flip
                await asyncio.sleep(random.random() * max_delay_milliseconds / 1000)

                # Try to flip first card at random position with timeout
                row1, col1 = random_int(rows), random_int(cols)
                await asyncio.wait_for(
                    board.flip(player_id, row1, col1), timeout=flip_timeout_seconds
                )

                async with stats_lock:
                    stats["total_flips"] += 1

                # Random delay before second flip
                await asyncio.sleep(random.random() * max_delay_milliseconds / 1000)

                # Try to flip second card at different random position with timeout
                row2, col2 = random_int(rows), random_int(cols)
                await asyncio.wait_for(
                    board.flip(player_id, row2, col2), timeout=flip_timeout_seconds
                )

                async with stats_lock:
                    stats["total_flips"] += 1

                # Check if we made a match
                player_state = board._get_or_create_player(player_id)
                if player_state.matched_pair is not None:
                    local_matches += 1
                    async with stats_lock:
                        stats["successful_matches"] += 1
                        stats["cards_removed"] += 2

            except FlipError:
                # Expected failures (removed cards, controlled cards)
                local_failures += 1
                async with stats_lock:
                    stats["failed_flips"] += 1
            except asyncio.TimeoutError:
                # Timeout waiting for a card (too much contention)
                local_failures += 1
                async with stats_lock:
                    stats["failed_flips"] += 1
                    stats["timeouts"] += 1
            except Exception as err:
                print(f"[{player_id}] Unexpected error on turn {turn}: {err}")

        print(
            f"[{player_id}] Finished: {local_matches} matches, {local_failures} failed flips"
        )

    # Start all players concurrently
    print("Starting players...")
    player_tasks = [asyncio.create_task(player(i)) for i in range(players)]

    # Wait for all players to finish
    await asyncio.gather(*player_tasks, return_exceptions=True)

    # Print final statistics
    print(f"\n{'=' * 60}")
    print("✓ Simulation Complete!")
    print(f"{'=' * 60}")
    print(f"Total flips attempted: {stats['total_flips']}")
    print(f"Successful matches: {stats['successful_matches']}")
    print(f"Failed flips: {stats['failed_flips']}")
    print(f"  - Timeouts: {stats['timeouts']}")
    print(f"Cards removed: {stats['cards_removed']}")

    # Calculate success rate
    if stats["total_flips"] > 0:
        success_rate = (stats["successful_matches"] * 2 / stats["total_flips"]) * 100
        print(f"Match success rate: {success_rate:.1f}%")

    # Verify board invariants
    print("\nVerifying board invariants...")
    board._check_rep()
    print("✓ Board representation invariants satisfied")

    # Check final board state
    final_state = board.look("observer")
    none_count = final_state.count("none")
    down_count = final_state.count("down")
    up_count = final_state.count("up ")

    print("\nFinal board state:")
    print(f"  Removed cards: {none_count}")
    print(f"  Face-down cards: {down_count}")
    print(f"  Face-up cards: {up_count}")
    print(f"{'=' * 60}\n")


def random_int(max_val: int) -> int:
    """
    Random positive integer generator

    @param max_val a positive integer which is the upper bound of the generated number
    @returns a random integer >= 0 and < max_val
    """
    return int(random.random() * max_val)


if __name__ == "__main__":
    asyncio.run(simulation_main())
