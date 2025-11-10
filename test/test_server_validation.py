# Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
# Redistribution of original or derived work requires permission of course staff.

"""
Tests for HTTP server input validation.
"""

import pytest
from aiohttp.test_utils import TestServer, TestClient
from app.board import Board, Card
from app.server import WebServer


@pytest.mark.asyncio
async def test_flip_invalid_location_format():
    """Server should return 400 for invalid location format."""
    cards = [[Card("A"), Card("B")]]
    board = Board(1, 2, cards)
    server = WebServer(board, 0)

    async with TestServer(server.app) as test_server:
        async with TestClient(test_server) as client:
            # Missing comma - our validation catches this
            resp = await client.get("/flip/player1/00")
            text = await resp.text()
            assert resp.status == 400
            assert "invalid location format" in text

            # Too many parts
            resp = await client.get("/flip/player1/0,1,2")
            text = await resp.text()
            assert resp.status == 400
            assert "invalid location format" in text


@pytest.mark.asyncio
async def test_flip_non_integer_location():
    """Server should return 400 for non-integer row/col."""
    cards = [[Card("A"), Card("B")]]
    board = Board(1, 2, cards)
    server = WebServer(board, 0)

    async with TestServer(server.app) as test_server:
        async with TestClient(test_server) as client:
            resp = await client.get("/flip/player1/a,b")
            text = await resp.text()
            assert resp.status == 400
            assert "must be integers" in text


@pytest.mark.asyncio
async def test_flip_out_of_bounds():
    """Server should return 400 for out-of-bounds position."""
    cards = [[Card("A"), Card("B")]]
    board = Board(1, 2, cards)
    server = WebServer(board, 0)

    async with TestServer(server.app) as test_server:
        async with TestClient(test_server) as client:
            resp = await client.get("/flip/player1/5,5")
            text = await resp.text()
            assert resp.status == 400
            assert "invalid input" in text or "out of bounds" in text


@pytest.mark.asyncio
async def test_look_invalid_player_id():
    """Server should return 400 for invalid player ID."""
    cards = [[Card("A"), Card("B")]]
    board = Board(1, 2, cards)
    server = WebServer(board, 0)

    async with TestServer(server.app) as test_server:
        async with TestClient(test_server) as client:
            # Player ID with special characters
            resp = await client.get("/look/player!")
            text = await resp.text()
            assert resp.status == 400
            assert "invalid player ID" in text


@pytest.mark.asyncio
async def test_valid_flip_still_works():
    """Server should still accept valid flip requests."""
    cards = [[Card("A"), Card("B")]]
    board = Board(1, 2, cards)
    server = WebServer(board, 0)

    async with TestServer(server.app) as test_server:
        async with TestClient(test_server) as client:
            resp = await client.get("/flip/player1/0,0")
            text = await resp.text()
            assert resp.status == 200
            assert "my A" in text
