"""Game constants for Pykrieg.

This module contains all the constants used throughout the Pykrieg
game implementation, including board dimensions, players, unit types,
and FEN symbols.
"""

# Board dimensions
BOARD_ROWS = 20
BOARD_COLS = 25
BOARD_SIZE = BOARD_ROWS * BOARD_COLS  # 500

# Territory
TERRITORY_BOUNDARY = 10

# Players
PLAYER_NORTH = "NORTH"
PLAYER_SOUTH = "SOUTH"

# Unit types
UNIT_INFANTRY = "INFANTRY"
UNIT_CAVALRY = "CAVALRY"
UNIT_CANNON = "CANNON"
UNIT_RELAY = "RELAY"
UNIT_SWIFT_CANNON = "SWIFT_CANNON"
UNIT_SWIFT_RELAY = "SWIFT_RELAY"

ALL_UNIT_TYPES = [
    UNIT_INFANTRY,
    UNIT_CAVALRY,
    UNIT_CANNON,
    UNIT_RELAY,
    UNIT_SWIFT_CANNON,
    UNIT_SWIFT_RELAY,
]

# FEN piece symbols (using KFEN specification)
FEN_INFANTRY = 'I'
FEN_CAVALRY = 'C'
FEN_CANNON = 'K'
FEN_RELAY = 'R'
FEN_SWIFT_CANNON = 'W'
FEN_SWIFT_RELAY = 'X'

FEN_SYMBOLS = {
    UNIT_INFANTRY: FEN_INFANTRY,
    UNIT_CAVALRY: FEN_CAVALRY,
    UNIT_CANNON: FEN_CANNON,
    UNIT_RELAY: FEN_RELAY,
    UNIT_SWIFT_CANNON: FEN_SWIFT_CANNON,
    UNIT_SWIFT_RELAY: FEN_SWIFT_RELAY,
}

# Reverse mapping from FEN symbol to unit type
SYMBOL_TO_UNIT = {v: k for k, v in FEN_SYMBOLS.items()}

# Turn phases
PHASE_MOVEMENT = 'M'
PHASE_BATTLE = 'B'

# Maximum moves per turn
MAX_MOVES_PER_TURN = 5
MAX_ATTACKS_PER_TURN = 1

# Terrain types (for 0.2.0 network system)
TERRAIN_NONE = None
TERRAIN_MOUNTAIN = 'MOUNTAIN'
TERRAIN_MOUNTAIN_PASS = 'MOUNTAIN_PASS'
TERRAIN_FORTRESS = 'FORTRESS'
TERRAIN_ARSENAL = 'ARSENAL'

ALL_TERRAIN_TYPES = [
    TERRAIN_MOUNTAIN,
    TERRAIN_MOUNTAIN_PASS,
    TERRAIN_FORTRESS,
    TERRAIN_ARSENAL,
]

# Direction vectors for ray-casting (8 directions)
DIRECTIONS = [
    (0, -1),   # North
    (1, -1),   # Northeast
    (1, 0),    # East
    (1, 1),    # Southeast
    (0, 1),    # South
    (-1, 1),   # Southwest
    (-1, 0),   # West
    (-1, -1),  # Northwest
]
