# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import sys
import asyncio
from aiohttp import web
from .board import Board
from .commands import look, flip, map_board, watch


async def main():
    """
    Start a game server using the given arguments.

    PS4 instructions: you are advised *not* to modify this file.

    Command-line usage:
        python server.py PORT FILENAME
    where:

      - PORT is an integer that specifies the server's listening port number,
        0 specifies that a random unused port will be automatically chosen.
      - FILENAME is the path to a valid board file, which will be loaded as
        the starting game board.

    For example, to start a web server on a randomly-chosen port using the
    board in `boards/hearts.txt`:
        python server.py 0 boards/hearts.txt

    @throws Error if an error occurs parsing a file or starting a server
    """
    args = sys.argv[1:]  # skip the first argument (script name)

    if len(args) < 1:
        raise ValueError("missing PORT")
    port_string = args[0]

    try:
        port = int(port_string)
    except ValueError:
        raise ValueError("invalid PORT")

    if port < 0:
        raise ValueError("invalid PORT")

    if len(args) < 2:
        raise ValueError("missing FILENAME")
    filename = args[1]

    board = await Board.parse_from_file(filename)
    server = WebServer(board, port)
    await server.start()


class WebServer:
    """
    HTTP web game server.
    """

    def __init__(self, board: Board, requested_port: int):
        """
        Make a new web game server using board that listens for connections on port.

        @param board shared game board
        @param requested_port server port number
        """
        self.board = board
        self.requested_port = requested_port
        self.app = web.Application()
        self.runner = None
        self.site = None

        # allow requests from web pages hosted anywhere
        @web.middleware
        async def cors_middleware(request, handler):
            response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        self.app.middlewares.append(cors_middleware)

        # GET /look/<playerId>
        # playerId must be a nonempty string of alphanumeric or underscore characters
        #
        # Response is the board state from playerId's perspective, as described in the ps4 handout.
        async def handle_look(request):
            player_id = request.match_info["playerId"]
            assert player_id

            board_state = await look(self.board, player_id)
            return web.Response(text=board_state, status=200)

        self.app.router.add_get("/look/{playerId}", handle_look)

        # GET /flip/<playerId>/<row>,<column>
        # playerId must be a nonempty string of alphanumeric or underscore characters;
        # row and column must be integers, 0 <= row,column < height,width of board (respectively)
        #
        # Response is the state of the board after the flip from the perspective of playerID,
        # as described in the ps4 handout.
        async def handle_flip(request):
            player_id = request.match_info["playerId"]
            location = request.match_info["location"]
            assert player_id
            assert location

            parts = location.split(",")
            row = int(parts[0])
            column = int(parts[1])
            assert row is not None and not isinstance(row, bool)
            assert column is not None and not isinstance(column, bool)

            try:
                board_state = await flip(self.board, player_id, row, column)
                return web.Response(text=board_state, status=200)
            except Exception as err:
                return web.Response(text=f"cannot flip this card: {err}", status=409)

        self.app.router.add_get("/flip/{playerId}/{location}", handle_flip)

        # GET /replace/<playerId>/<oldcard>/<newcard>
        # playerId must be a nonempty string of alphanumeric or underscore characters;
        # oldcard and newcard must be nonempty strings.
        #
        # Replaces all occurrences of oldcard with newcard (as card labels) on the board.
        #
        # Response is the state of the board after the replacement from the the perspective of playerID,
        # as described in the ps4 handout.
        async def handle_replace(request):
            player_id = request.match_info["playerId"]
            from_card = request.match_info["fromCard"]
            to_card = request.match_info["toCard"]
            assert player_id
            assert from_card
            assert to_card

            async def replace_func(card: str) -> str:
                return to_card if card == from_card else card

            board_state = await map_board(self.board, player_id, replace_func)
            return web.Response(text=board_state, status=200)

        self.app.router.add_get(
            "/replace/{playerId}/{fromCard}/{toCard}", handle_replace
        )

        # GET /watch/<playerId>
        # playerId must be a nonempty string of alphanumeric or underscore characters
        #
        # Waits until the next time the board changes (defined as any cards turning face up or face down,
        # being removed from the board, or changing from one string to a different string).
        #
        # Response is the new state of the board from the perspective of playerID,
        # as described in the ps4 handout.
        async def handle_watch(request):
            player_id = request.match_info["playerId"]
            assert player_id

            board_state = await watch(self.board, player_id)
            return web.Response(text=board_state, status=200)

        self.app.router.add_get("/watch/{playerId}", handle_watch)

        # GET /
        #
        # Response is the game UI as an HTML page.
        self.app.router.add_static("/", "public/")

    async def start(self):
        """
        Start this server.

        @returns (a promise that) resolves when the server is listening
        """
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", self.requested_port)
        await self.site.start()
        print(f"server now listening at http://localhost:{self.port}")

    @property
    def port(self) -> int:
        """
        @returns the actual port that server is listening at. (May be different
                 than the requested_port used in the constructor, since if
                 requested_port = 0 then an arbitrary available port is chosen.)
                 Requires that start() has already been called and completed.
        """
        if self.site is None:
            raise RuntimeError("server is not listening at a port")
        return self.site._server.sockets[0].getsockname()[1]

    def stop(self):
        """
        Stop this server. Once stopped, this server cannot be restarted.
        """
        if self.runner:
            asyncio.create_task(self.runner.cleanup())
        print("server stopped")


if __name__ == "__main__":
    asyncio.run(main())
