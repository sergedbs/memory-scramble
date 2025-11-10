# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import asyncio
import random
from .board import Board


async def simulation_main():
    """
    Example code for simulating a game.

    PS4 instructions: you may use, modify, or remove this file,
      completing it is recommended but not required.

    @throws Error if an error occurs reading or parsing the board
    """
    filename = "boards/ab.txt"
    board = await Board.parse_from_file(filename)
    size = 5
    players = 1
    tries = 10
    max_delay_milliseconds = 100

    async def player(player_number: int):
        """@param player_number player to simulate"""
        # TODO set up this player on the board if necessary

        for jj in range(tries):
            try:
                await asyncio.sleep(random.random() * max_delay_milliseconds / 1000)
                # TODO try to flip over a first card at (random_int(size), random_int(size))
                #      which might wait until this player can control that card

                await asyncio.sleep(random.random() * max_delay_milliseconds / 1000)
                # TODO and if that succeeded,
                #      try to flip over a second card at (random_int(size), random_int(size))
            except Exception as err:
                print(f"attempt to flip a card failed: {err}")

    # start up one or more players as concurrent asynchronous function calls
    player_promises = []
    for ii in range(players):
        player_promises.append(player(ii))
    # wait for all the players to finish (unless one throws an exception)
    await asyncio.gather(*player_promises)


def random_int(max_val: int) -> int:
    """
    Random positive integer generator

    @param max_val a positive integer which is the upper bound of the generated number
    @returns a random integer >= 0 and < max_val
    """
    return int(random.random() * max_val)


if __name__ == "__main__":
    asyncio.run(simulation_main())
