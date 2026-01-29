"""Test constants module."""

from pykrieg import constants


def test_board_dimensions():
    """Test board dimension constants."""
    assert constants.BOARD_ROWS == 20
    assert constants.BOARD_COLS == 25
    assert constants.BOARD_SIZE == 500


def test_players():
    """Test player constants."""
    assert constants.PLAYER_NORTH == "NORTH"
    assert constants.PLAYER_SOUTH == "SOUTH"


def test_unit_types():
    """Test unit type constants."""
    assert constants.UNIT_INFANTRY == "INFANTRY"
    assert constants.UNIT_CAVALRY == "CAVALRY"
    assert constants.UNIT_CANNON == "CANNON"
    assert constants.UNIT_RELAY == "RELAY"
    assert constants.UNIT_SWIFT_CANNON == "SWIFT_CANNON"
    assert constants.UNIT_SWIFT_RELAY == "SWIFT_RELAY"
    assert len(constants.ALL_UNIT_TYPES) == 6


def test_fen_symbols():
    """Test FEN symbol constants."""
    assert constants.FEN_INFANTRY == 'I'
    assert constants.FEN_CAVALRY == 'C'
    assert constants.FEN_CANNON == 'K'
    assert constants.FEN_RELAY == 'R'
    assert constants.FEN_SWIFT_CANNON == 'W'
    assert constants.FEN_SWIFT_RELAY == 'X'


def test_fen_symbols_mapping():
    """Test FEN symbols mapping to unit types."""
    assert constants.FEN_SYMBOLS['INFANTRY'] == 'I'
    assert constants.FEN_SYMBOLS['CAVALRY'] == 'C'
    assert constants.FEN_SYMBOLS['CANNON'] == 'K'
    assert constants.FEN_SYMBOLS['RELAY'] == 'R'
    assert constants.FEN_SYMBOLS['SWIFT_CANNON'] == 'W'
    assert constants.FEN_SYMBOLS['SWIFT_RELAY'] == 'X'


def test_symbol_to_unit_mapping():
    """Test reverse mapping from FEN symbol to unit type."""
    assert constants.SYMBOL_TO_UNIT['I'] == 'INFANTRY'
    assert constants.SYMBOL_TO_UNIT['C'] == 'CAVALRY'
    assert constants.SYMBOL_TO_UNIT['K'] == 'CANNON'
    assert constants.SYMBOL_TO_UNIT['R'] == 'RELAY'
    assert constants.SYMBOL_TO_UNIT['W'] == 'SWIFT_CANNON'
    assert constants.SYMBOL_TO_UNIT['X'] == 'SWIFT_RELAY'


def test_territory_boundary():
    """Test territory boundary constant."""
    assert constants.TERRITORY_BOUNDARY == 10


def test_turn_phases():
    """Test turn phase constants."""
    assert constants.PHASE_MOVEMENT == 'M'
    assert constants.PHASE_BATTLE == 'B'


def test_max_moves_per_turn():
    """Test maximum moves per turn constants."""
    assert constants.MAX_MOVES_PER_TURN == 5
    assert constants.MAX_ATTACKS_PER_TURN == 1
