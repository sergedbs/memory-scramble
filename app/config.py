import os
import sys
from typing import Tuple


class Config:
    DEFAULT_PORT = 8080
    DEFAULT_BOARD = "boards/perfect.txt"
    DEFAULT_HOST = "localhost"

    @staticmethod
    def get_config() -> Tuple[int, str, str]:
        """
        Get server configuration.

        @returns (port, board_file, host) tuple
        """
        port = Config.DEFAULT_PORT
        board_file = Config.DEFAULT_BOARD
        host = Config.DEFAULT_HOST

        # Environment variables
        if "PORT" in os.environ:
            try:
                port = int(os.environ["PORT"])
            except ValueError:
                print(f"Warning: Invalid PORT env var, using default {port}")

        if "BOARD_FILE" in os.environ:
            board_file = os.environ["BOARD_FILE"]

        if "HOST" in os.environ:
            host = os.environ["HOST"]

        # Command-line arguments
        args = sys.argv[1:]
        if len(args) >= 1:
            try:
                port = int(args[0])
            except ValueError:
                raise ValueError(f"Invalid PORT argument: {args[0]}")

        if len(args) >= 2:
            board_file = args[1]

        return port, board_file, host


def load_config() -> Tuple[int, str, str]:
    """
    Load configuration for the server.

    @returns (port, board_file, host) tuple
    """
    return Config.get_config()
