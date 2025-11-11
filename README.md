# Memory Scramble

A multiplayer, concurrent implementation of the Memory/Concentration card matching game. Built with Python asyncio and aiohttp, this project demonstrates advanced concurrency patterns, shared mutable state management, and real-time event notification systems. Based on [MIT 6.102 -  Problem Set 4: Memory Scramble](https://web.mit.edu/6.102/www/sp25/psets/ps4/)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT%206.102-green.svg)](LICENSE)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Game Rules](#game-rules)
- [HTTP API](#http-api)
- [Examples](#examples)
- [License](#license)

## Features

- **Asynchronous Concurrency**: Non-blocking multiplayer gameplay using Python's `asyncio`
- **Fair Resource Contention**: FIFO queuing for card access with no starvation
- **Real-time Updates**: Push-based notifications via long-polling `watch()` mechanism
- **Atomic State Transitions**: Lock-protected board operations preventing race conditions
- **Per-Player State Tracking**: Individual game contexts with turn boundary cleanup
- **Card Transformation**: Async `map()` operation maintaining matching consistency
- **Web-based Client**: Interactive browser interface with real-time board updates
- **HTTP Protocol**: `GET`/`POST` with JSON payloads, CORS enabled, long-polling support
- **Type-Annotated**: Full type hints with PEP 484 compliance
- **Comprehensive Testing**: 12 test modules covering rules, concurrency, and edge cases
- **Docker Ready**: Containerized deployment with docker-compose
- **Stress Testing**: Configurable simulation framework with bot players

## Architecture

The server follows a **layered architecture** with asyncio-based concurrency:

```txt
                     Asyncio Event Loop
                            |
         +------------------+------------------+
         |                  |                  |
    HTTP Requests       watch() Waiters    Simulation Bots
         |                  |                  |
         v                  v                  v
┌─────────────────────────────────────────────────────┐
│         HTTP Server (server.py)                     │
│         - aiohttp request handlers                  │
│         - CORS middleware                           │
│         - Route mapping                             │
├─────────────────────────────────────────────────────┤
│         Command Layer (commands.py)                 │
│         - look, flip, map_board, watch, reset       │
├─────────────────────────────────────────────────────┤
│         Board ADT (board.py)                        │
│         ┌───────────────────────────────────┐       │
│         │ Concurrency Control:              │       │
│         │ - asyncio.Lock (global)           │       │
│         │ - asyncio.Condition (per spot)    │       │
│         │ - asyncio.Condition (watchers)    │       │
│         │ - asyncio.Future (pending ops)    │       │
│         └───────────────────────────────────┘       │
│         ┌───────────────────────────────────┐       │
│         │ State Management:                 │       │
│         │ - Card grid (2D list)             │       │
│         │ - Player states (dict)            │       │
│         │ - Version counter                 │       │
│         └───────────────────────────────────┘       │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Card         │  │ PlayerState  │  │ Config    │  │
│  │ (board.py)   │  │ (board.py)   │  │ (config)  │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
```

### Concurrency Model

Memory Scramble uses **asyncio** for cooperative concurrency with:

- **Global Lock**: `asyncio.Lock` protects board state modifications
- **Per-Spot Conditions**: `asyncio.Condition` per card enables FIFO waiting queues
- **Version Counter**: Change detection for `watch()` notifications via `asyncio.Condition`
- **No Busy-Waiting**: All blocking uses `await` on condition variables
- **No Deadlocks**: Lock acquisition order enforced, no circular waits

## Project Structure

```txt
memory-scramble/
├── app/                        # Application source code
│   ├── __init__.py            # Package initialization
│   ├── board.py               # Board ADT with Card, PlayerState, Board
│   ├── server.py              # HTTP server with aiohttp
│   ├── commands.py            # Game command implementations
│   ├── config.py              # Configuration management
│   ├── simulation.py          # Stress testing framework
│   └── Dockerfile             # Docker image definition
├── boards/                     # Sample board files
│   ├── perfect.txt            # 3x3 grid (default)
│   ├── ab.txt                 # Simple 2x2 test board
│   └── zoom.txt               # Larger board for stress testing
├── public/                     # Web client
│   └── index.html             # Interactive browser interface
├── test/                       # Test suite
│   ├── test_card.py           # Card representation invariants
│   ├── test_player_state.py   # Player state management
│   ├── test_board_parsing.py  # Board file parsing
│   ├── test_board_look.py     # Look operation correctness
│   ├── test_flip_first.py     # First card flip rules
│   ├── test_flip_second.py    # Second card flip rules
│   ├── test_cleanup.py        # Turn boundary cleanup
│   ├── test_async_flip.py     # Concurrent flip operations
│   ├── test_map.py            # Map transformation correctness
│   ├── test_watch.py          # Watch notification mechanism
│   ├── test_server_validation.py # HTTP validation
│   └── __pycache__/
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── test_manual.py              # Manual testing utilities
├── LICENSE                     # License file
└── README.md                   # This file
```

## Installation

### Prerequisites

- **Python 3.11+** (requires asyncio features from Python 3.10+)
- **Docker** (optional, for containerized deployment)

### Local Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd memory-scramble
   ```

2. **Create virtual environment**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   **Dependencies**:
   - `aiohttp>=3.9.0` - Async HTTP server
   - `aiofiles>=23.0.0` - Async file I/O
   - `pytest>=9.0.0` - Testing framework
   - `pytest-asyncio>=0.21.0` - Async test support

4. **Verify installation**:

   ```bash
   python -m app.server --help
   ```

## Usage

### Basic Usage

**Start the server with default settings** (serves `boards/perfect.txt` on `localhost:8080`):

```bash
python -m app.server
```

**Access the web client**:

- Open your browser to `http://localhost:8080`
- Or use curl: `curl "http://localhost:8080/look?player=alice"`

### Command-Line Options

```bash
python -m app.server [PORT] [BOARD_FILE]
```

#### Positional Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PORT` | Port number (0 for random) | `8080` |
| `BOARD_FILE` | Path to board file | `boards/perfect.txt` |

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8080` |
| `BOARD_FILE` | Board file path | `boards/perfect.txt` |
| `HOST` | Bind address | `localhost` |

### Common Usage Examples

**Serve on a specific port**:

```bash
python -m app.server 3000
```

**Use a custom board**:

```bash
python -m app.server 8080 boards/zoom.txt
```

**Bind to all interfaces** (for remote access):

```bash
HOST=0.0.0.0 python -m app.server
```

**Random port**:

```bash
python -m app.server 0
```

**Environment variable configuration**:

```bash
PORT=9000 BOARD_FILE=boards/ab.txt python -m app.server
```

## Configuration

### Server Configuration

Configuration is managed in `app/config.py`:

```python
class Config:
    DEFAULT_PORT = 8080
    DEFAULT_BOARD = "boards/perfect.txt"
    DEFAULT_HOST = "localhost"
```

### Board File Format

Board files use a simple text format:

```txt
<rows>x<cols>
<card_value_1>
<card_value_2>
...
<card_value_N>
```

**Rules**:

- First line: dimensions as `<rows>x<cols>` (e.g., `3x3`)
- Exactly `rows × cols` card values follow
- Cards listed in row-major order (left-to-right, top-to-bottom)
- Card values: non-empty strings without whitespace
- Unicode characters (including emojis) supported

**Example** (`boards/perfect.txt`):

```txt
3x3
🦄
🦄
🌈
🌈
🌈
🦄
🌈
🦄
🌈
```

## Testing

The server includes a comprehensive test suite with 12 test modules covering rules, concurrency, and edge cases.

### Running Tests

**Run all tests**:

```bash
pytest test/
```

**Run specific test module**:

```bash
pytest test/test_flip_first.py -v
```

**Run with coverage**:

```bash
pytest test/ --cov=app --cov-report=html
```

**Run async tests only**:

```bash
pytest test/test_async_flip.py -v
```

### Test Coverage

The test suite covers:

- **Unit Tests**: Card state, player state, board parsing, board rendering
- **Rule Tests**: First/second flip rules, turn boundary cleanup
- **Concurrency Tests**: Concurrent flips, blocking behavior, FIFO fairness
- **Map Tests**: Transformation consistency, matching invariants during updates
- **Watch Tests**: Change notifications, version tracking
- **Integration Tests**: HTTP protocol, request validation

### Stress Testing

Run concurrent gameplay simulation:

```bash
python -m app.simulation                # Default settings
python -m app.simulation boards/zoom.txt # Custom board
```

The simulation tests concurrent operations, blocking behavior, invariant checking, and deadlock detection with configurable bot players.

## Docker Deployment

### Using Docker

**Build the image**:

```bash
docker build -t memory-scramble -f app/Dockerfile .
```

**Run the container**:

```bash
docker run -p 8080:8080 -e BOARD_FILE=boards/perfect.txt memory-scramble
```

### Using Docker Compose

**Start the server**:

```bash
docker-compose up
```

**Start in detached mode**:

```bash
docker-compose up -d
```

**Stop the server**:

```bash
docker-compose down
```

**View logs**:

```bash
docker-compose logs -f
```

**Configure via environment**:

```bash
PORT=9000 BOARD_FILE=boards/zoom.txt docker-compose up
```

## Game Rules

## How It Works

### Concurrent Request Flow

1. **HTTP Request Arrives**: aiohttp receives GET/POST request
2. **Route to Handler**: URL mapped to async handler function
3. **Extract Parameters**: Player ID, position, or function spec parsed
4. **Validate Input**: Player ID regex, coordinate bounds checked
5. **Command Execution**: Handler calls appropriate Board ADT method
6. **Lock Acquisition**: Board acquires global lock for critical section
7. **Rule Enforcement**: Board checks game rules and player state
8. **Blocking (if needed)**: If card controlled, await on condition variable
9. **State Update**: Card flipped, controller assigned, version incremented
10. **Lock Release**: Critical section complete, lock released
11. **Notification**: Watchers notified if version changed
12. **Response Generation**: Board state rendered as text
13. **HTTP Response**: Status code and body returned to client

### Key Components

#### 1. Board ADT (`board.py`)

**Card Class**:

```python
class Card:
    """Mutable card with value, visibility, and control state"""
    value: str                      # Card text (emoji, word, etc.)
    on_board: bool                  # Presence (False if removed)
    face_up: bool                   # Visibility
    controller: Optional[str]       # Player ID or None
```

**PlayerState Class**:

```python
class PlayerState:
    """Per-player transient state"""
    player_id: str                  # Player identifier
    first_card: Optional[Pos]       # First card position if controlled
    second_card: Optional[Pos]      # Second card position if matched
    matched_pair: Optional[...]     # Pair to remove on next turn
```

**Board Class**:

```python
class Board:
    """Main game board with concurrency control"""
    _grid: List[List[Card]]         # 2D card grid
    _players: Dict[str, PlayerState] # Player state map
    _lock: asyncio.Lock             # Global lock
    _spot_cvs: Dict[Pos, Condition] # Per-spot conditions
    _change_cv: asyncio.Condition   # Watcher notification
    _version: int                   # Change counter
```

#### 2. Command Layer (`commands.py`)

Thin wrappers delegating to Board:

```python
async def look(board: Board, player_id: str) -> str:
    """Returns board state from player's perspective"""
    return board.look(player_id)

async def flip(board: Board, player_id: str, row: int, col: int) -> str:
    """Attempts to flip card at position"""
    await board.flip(player_id, row, col)
    return board.look(player_id)

async def watch(board: Board, player_id: str) -> str:
    """Blocks until board changes, then returns state"""
    await board.watch()
    return board.look(player_id)
```

#### 3. HTTP Server (`server.py`)

aiohttp-based async server:

```python
class WebServer:
    """HTTP server with CORS support"""
    
    async def handle_look(self, request):
        """GET /look?player={id}"""
        player_id = request.query.get('player')
        return web.Response(text=await look(self.board, player_id))
    
    async def handle_flip(self, request):
        """POST /flip with JSON body"""
        data = await request.json()
        result = await flip(self.board, data['player'], 
                          data['row'], data['col'])
        return web.Response(text=result)
    
    async def handle_watch(self, request):
        """GET /watch?player={id} (long-poll)"""
        player_id = request.query.get('player')
        result = await watch(self.board, player_id)
        return web.Response(text=result)
```

### Concurrency Mechanisms

#### Waiting for Controlled Cards

When a player tries to flip a card controlled by another:

```python
async def flip_first(self, player: str, pos: Pos) -> None:
    async with self._lock:
        card = self._grid[pos[0]][pos[1]]
        
        # Fast path: card available
        if card.controller is None:
            card.flip_up()
            card.set_controller(player)
            return
    
    # Slow path: wait for release
    async with self._spot_cvs[pos]:
        while True:
            async with self._lock:
                card = self._grid[pos[0]][pos[1]]
                if card.controller is None:
                    card.flip_up()
                    card.set_controller(player)
                    return
            
            # Release lock, wait for notification
            await self._spot_cvs[pos].wait()
```

#### Map Consistency

Ensures matching cards remain consistent during transformation:

```python
async def map(self, f: Transformer) -> None:
    # Phase 1: Collect all cards and group by value
    value_groups = {}  # value -> [positions]
    async with self._lock:
        for pos, card in self._all_cards():
            value_groups.setdefault(card.value, []).append(pos)
    
    # Phase 2: Transform each value (outside lock)
    new_values = {}
    for old_value in value_groups:
        new_values[old_value] = await f(old_value)
    
    # Phase 3: Commit per equivalence class (under lock)
    for old_value, positions in value_groups.items():
        async with self._lock:
            for pos in positions:
                self._grid[pos[0]][pos[1]].value = new_values[old_value]
            self._version += 1
        
        # Notify after each group
        async with self._change_cv:
            self._change_cv.notify_all()
```

#### Watch Notifications

Version-based change detection:

```python
async def watch(self) -> None:
    """Blocks until any visible change occurs"""
    async with self._change_cv:
        version_before = self._version
        while self._version == version_before:
            await self._change_cv.wait()
```

### Security & Correctness

1. **Representation Invariants**: Checked via `_check_rep()`
   - Removed cards are face-down and uncontrolled
   - Face-down cards are uncontrolled
   - Controlled cards are face-up and on board

2. **Input Validation**:
   - Player IDs: `^[A-Za-z0-9_]+$`
   - Coordinates: Within grid bounds
   - Card values: Non-empty, no whitespace

3. **Atomicity**: All board modifications inside locks

4. **Fairness**: FIFO queuing on per-spot conditions

5. **No Rep Exposure**: Board state rendered to immutable strings

### Coordinate System

Grid positions use zero-indexed `(row, col)` coordinates:

- `(0, 0)` is top-left
- Rows increase downward
- Columns increase rightward

### Card Flipping Protocol

#### First Card Flip

1. **No card at position** → Fail with `FlipError`
2. **Card face-down** → Flip up, grant control to player
3. **Card face-up, uncontrolled** → Grant control (no flip)
4. **Card controlled by another** → Wait (non-blocking) until released

#### Second Card Flip

1. **No card at position** → Fail, relinquish first card (stays up)
2. **Card controlled** → Fail, relinquish first card (stays up)
3. **Otherwise**:
   - If face-down: flip up
   - Compare with first card:
     - **Match** → Keep control of both (stays up)
     - **No match** → Relinquish both (stays up)

#### Turn Boundary Cleanup

Before a player's next first-card flip:

- **If matched**: Remove both cards, relinquish control
- **If no match**: For each card:
  - If still on board, face-up, and uncontrolled → flip down

### Board State Format

Text-based format from player's perspective:

```txt
<rows>x<cols>
<spot_1>
<spot_2>
...
<spot_N>
```

**Spot descriptions**:

- `none` - No card (removed)
- `down` - Face-down card
- `up <value>` - Face-up card controlled by another (or uncontrolled)
- `my <value>` - Face-up card controlled by this player

**Example**:

```txt
3x3
down
my 🦄
down
up 🌈
none
down
down
up 🦄
down
```

## HTTP API

All endpoints return board state in text format. Player IDs must match `^[A-Za-z0-9_]+$`.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/look?player={id}` | GET | Returns current board state |
| `/flip` | POST | Flips card at position (JSON: `{player, row, col}`) |
| `/map` | POST | Transforms all card values (JSON: `{player, f_spec}`) |
| `/watch?player={id}` | GET | Long-polls until board changes |
| `/reset` | POST | Resets board to initial state (JSON: `{player}`) |

**Example**:

```bash
# Look at board
curl "http://localhost:8080/look?player=alice"

# Flip a card
curl -X POST http://localhost:8080/flip \
  -H "Content-Type: application/json" \
  -d '{"player":"alice","row":0,"col":1}'

# Watch for changes (blocks until something changes)
curl "http://localhost:8080/watch?player=alice"
```

## Examples

### Web Client

1. Start server: `python -m app.server`
2. Open `public/index.html` in browser
3. Enter player name and click cards to flip
4. Open multiple tabs with different players to see real-time updates

### Command-Line Gameplay

```bash
# Start server
python -m app.server

# Player flips first card
curl -X POST http://localhost:8080/flip \
  -H "Content-Type: application/json" \
  -d '{"player":"alice","row":0,"col":0}'

# Watch for changes (blocks until board updates)
curl "http://localhost:8080/watch?player=observer"
```

### Example 2: Watching for Changes

Open two terminals:

**Terminal 1 (Watcher)**:

```bash
# This will block until someone flips a card
curl "http://localhost:8080/watch?player=observer"
```

**Terminal 2 (Player)**:

```bash
# This flip will wake the watcher
curl -X POST http://localhost:8080/flip \
  -H "Content-Type: application/json" \
  -d '{"player":"alice","row":0,"col":0}'
```

### Example 3: Web Client

1. Start server:

   ```bash
   python -m app.server
   ```

2. Open `public/index.html` in browser

3. Enter player name (e.g., "alice")

4. Click cards to flip them

5. Open another browser tab with different player name (e.g., "bob")

6. Both players see real-time updates via watch polling

### Example 4: Stress Testing

```bash
# Run simulation with default settings
python -m app.simulation

# Use larger board for more contention
python -m app.simulation boards/zoom.txt
```

### Example 5: Error Handling

**Invalid position**:

```bash
curl -X POST http://localhost:8080/flip \
  -H "Content-Type: application/json" \
  -d '{"player":"alice","row":10,"col":10}'
```

Response (409 Conflict):

```json
{"error": "Position (10, 10) out of bounds"}
```

**Invalid player ID**:

```bash
curl "http://localhost:8080/look?player=alice%20smith"
```

Response (400 Bad Request):

```json
{"error": "Invalid player ID format"}
```

## Development

### Code Organization

The project follows a **modular ADT-based architecture**:

- **`board.py`** (890 lines): Core game logic
  - `Card`: Card representation with invariants
  - `PlayerState`: Per-player game context
  - `Board`: Main ADT with all game operations

- **`server.py`** (252 lines): HTTP server
  - `WebServer`: aiohttp server with CORS
  - Route handlers (thin wrappers)

- **`commands.py`** (103 lines): Command layer
  - `look`, `flip`, `map_board`, `watch`, `reset`

- **`config.py`** (59 lines): Configuration management

- **`simulation.py`** (169 lines): Stress testing framework

### Extending the Server

#### Adding New Commands

1. **Add method to Board ADT** (`app/board.py`):

   ```python
   async def shuffle(self) -> None:
       """Randomly rearrange cards on board"""
       async with self._lock:
           # Shuffle logic
           self._version += 1
       async with self._change_cv:
           self._change_cv.notify_all()
   ```

2. **Add command wrapper** (`app/commands.py`):

   ```python
   async def shuffle(board: Board, player_id: str) -> str:
       await board.shuffle()
       return board.look(player_id)
   ```

3. **Add HTTP endpoint** (`app/server.py`):

   ```python
   async def handle_shuffle(self, request):
       data = await request.json()
       result = await shuffle(self.board, data['player'])
       return web.Response(text=result)
   
   # In setup_routes()
   app.router.add_post('/shuffle', self.handle_shuffle)
   ```

#### Adding New Board Files

Create a text file following the format:

```txt
<rows>x<cols>
<card_value_1>
<card_value_2>
...
```

Example (`boards/animals.txt`):

```txt
2x4
🐶
🐱
🐶
🐱
🦁
🐯
🦁
🐯
```

Use it:

```bash
python -m app.server 8080 boards/animals.txt
```

#### Customizing the Web Client

Edit `public/index.html`:

- Modify styles in `<style>` section
- Change polling interval: `setInterval(..., 1000)`
- Add features: score tracking, timer, animations

### Testing Strategies

#### Unit Testing

Test individual components in isolation:

```python
@pytest.mark.asyncio
async def test_card_flip():
    card = Card("🦄")
    assert not card.face_up
    card.flip_up()
    assert card.face_up
```

#### Integration Testing

Test interactions between components:

```python
@pytest.mark.asyncio
async def test_two_player_flip():
    board = await Board.parse_from_file("boards/ab.txt")
    await board.flip("alice", 0, 0)
    await board.flip("bob", 0, 1)
    assert "alice" in board.look("alice")
```

#### Concurrency Testing

Test concurrent operations with `asyncio.gather()`:

```python
@pytest.mark.asyncio
async def test_concurrent_flips():
    board = await Board.parse_from_file("boards/perfect.txt")
    
    async def player_flip(player, row, col):
        try:
            await board.flip(player, row, col)
        except FlipError:
            pass
    
    # Both players try to flip same card
    await asyncio.gather(
        player_flip("alice", 0, 0),
        player_flip("bob", 0, 0)
    )
    
    # Only one should control it
    state = board.look("alice")
    assert state.count("my") == 1
```

## License

This project is licensed under the [MIT License](LICENSE), except where otherwise stated.

Copyright (c) 2021-25 MIT 6.102/6.031 course staff. All rights reserved.  
Redistribution of original or derived work requires permission of course staff.

## Resources

### Course Materials

- [MIT 6.102: Software Construction](https://web.mit.edu/6.102/www/sp25/)
- [Testing](https://web.mit.edu/6.102/www/sp25/classes/02-testing/)
- [Abstract Data Types](https://web.mit.edu/6.102/www/sp25/classes/06-abstract-data-types/)
- [Abstraction Functions & Rep Invariants](https://web.mit.edu/6.102/www/sp25/classes/07-abstraction-functions-rep-invariants/)
- [Concurrency](https://web.mit.edu/6.102/www/sp25/classes/14-concurrency/)
- [Thread Safety](https://web.mit.edu/6.102/www/sp25/classes/15-thread-safety/)
- [Promises & Async Programming](https://web.mit.edu/6.102/www/sp25/classes/15-promises/)

### Python Async Programming

- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [PEP 492 - Coroutines with async and await](https://www.python.org/dev/peps/pep-0492/)
- [Lock-Free and Wait-Free Algorithms](https://preshing.com/20120612/an-introduction-to-lock-free-programming/)
