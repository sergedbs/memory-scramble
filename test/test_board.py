# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

import pytest
from app.board import Board


class TestBoard:
    """
    Tests for the Board abstract data type.
    """

    # Testing strategy
    #   TODO

    pass


class TestAsync:
    """
    Example test case that uses async/await to test an asynchronous function.
    Feel free to delete these example tests.
    """

    @pytest.mark.asyncio
    async def test_reads_file_asynchronously(self):
        with open("boards/ab.txt", "r") as f:
            file_contents = f.read()
        assert file_contents.startswith("5x5")
