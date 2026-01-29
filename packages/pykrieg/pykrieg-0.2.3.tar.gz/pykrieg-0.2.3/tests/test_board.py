"""Tests for the Board class."""

import pytest

from pykrieg.board import Board


def test_board_dimensions():
    """Test board has correct dimensions."""
    board = Board()
    assert board.rows == 20
    assert board.cols == 25


def test_board_initialization():
    """Test board starts empty with correct turn."""
    board = Board()
    # Check all squares are empty
    for row in range(board.rows):
        for col in range(board.cols):
            assert board.get_piece(row, col) is None
    assert board.turn == 'NORTH'


def test_valid_square_coordinates():
    """Test coordinate validation."""
    board = Board()
    assert board.is_valid_square(0, 0) is True
    assert board.is_valid_square(19, 24) is True
    assert board.is_valid_square(-1, 0) is False
    assert board.is_valid_square(20, 0) is False
    assert board.is_valid_square(0, -1) is False
    assert board.is_valid_square(0, 25) is False


def test_set_and_get_piece():
    """Test setting and getting pieces with new Unit system."""
    from pykrieg.pieces import Infantry
    board = Board()
    dummy_unit = Infantry("NORTH")

    board.place_unit(0, 0, dummy_unit)
    retrieved_unit = board.get_unit(0, 0)

    assert retrieved_unit == dummy_unit
    assert retrieved_unit.unit_type == "INFANTRY"
    assert retrieved_unit.owner == "NORTH"
    assert board.get_piece(0, 1) is None


def test_clear_square():
    """Test clearing squares."""
    board = Board()
    dummy_piece = {"type": "INFANTRY", "owner": "NORTH"}

    board.set_piece(5, 10, dummy_piece)
    assert board.get_piece(5, 10) == dummy_piece

    board.clear_square(5, 10)
    assert board.get_piece(5, 10) is None


def test_invalid_coordinates_raise_error():
    """Test that invalid coordinates raise ValueError."""
    board = Board()

    with pytest.raises(ValueError):
        board.get_piece(-1, 0)

    with pytest.raises(ValueError):
        board.set_piece(20, 0, {})

    with pytest.raises(ValueError):
        board.clear_square(0, 25)


def test_get_unit_invalid_coordinates():
    """Test that get_unit raises ValueError for invalid coordinates."""
    board = Board()

    with pytest.raises(ValueError, match="Invalid coordinates"):
        board.get_unit(-1, 0)

    with pytest.raises(ValueError, match="Invalid coordinates"):
        board.get_unit(20, 0)

    with pytest.raises(ValueError, match="Invalid coordinates"):
        board.get_unit(0, -1)

    with pytest.raises(ValueError, match="Invalid coordinates"):
        board.get_unit(0, 25)


def test_turn_side():
    """Test turn_side method returns current turn."""
    board = Board()
    assert board.turn_side() == 'NORTH'
    board._turn = 'SOUTH'
    assert board.turn_side() == 'SOUTH'


def test_territory_boundary():
    """Test territory boundary is set correctly."""
    board = Board()
    assert board.territory_boundary == 10


def test_territory_classification():
    """Test squares are correctly classified by territory."""
    board = Board()

    # North territory: rows 0-9
    assert board.get_territory(0, 0) == 'NORTH'
    assert board.get_territory(9, 24) == 'NORTH'

    # South territory: rows 10-19
    assert board.get_territory(10, 0) == 'SOUTH'
    assert board.get_territory(19, 24) == 'SOUTH'

    # Row 9 is North, row 10 is South
    assert board.is_north_territory(9, 0) is True
    assert board.is_north_territory(10, 0) is False
    assert board.is_south_territory(9, 0) is False
    assert board.is_south_territory(10, 0) is True


def test_territory_squares():
    """Test getting all squares in a territory."""
    board = Board()

    north_squares = board.get_territory_squares('NORTH')
    south_squares = board.get_territory_squares('SOUTH')

    # North has 10 rows × 25 cols = 250 squares
    assert len(north_squares) == 250
    assert all(board.is_north_territory(r, c) for r, c in north_squares)

    # South has 10 rows × 25 cols = 250 squares
    assert len(south_squares) == 250
    assert all(board.is_south_territory(r, c) for r, c in south_squares)

    # No overlap
    assert set(north_squares).isdisjoint(set(south_squares))

    # Total is 500
    assert len(north_squares) + len(south_squares) == 500


def test_invalid_territory():
    """Test that invalid territory raises error."""
    board = Board()

    with pytest.raises(ValueError):
        board.get_territory_squares('EAST')


def test_territory_with_invalid_coordinates():
    """Test territory methods handle invalid coordinates."""
    board = Board()

    with pytest.raises(ValueError):
        board.get_territory(-1, 0)

    with pytest.raises(ValueError):
        board.get_territory(0, -1)

    with pytest.raises(ValueError):
        board.get_territory(20, 0)

    with pytest.raises(ValueError):
        board.is_north_territory(0, 25)

    with pytest.raises(ValueError):
        board.is_south_territory(-1, 0)


def test_multiple_pieces():
    """Test managing multiple pieces on the board."""
    board = Board()

    pieces = [
        (0, 0, {"type": "INFANTRY", "owner": "NORTH"}),
        (0, 5, {"type": "CAVALRY", "owner": "NORTH"}),
        (19, 24, {"type": "INFANTRY", "owner": "SOUTH"}),
        (10, 12, {"type": "CANNON", "owner": "SOUTH"}),
    ]

    for row, col, piece in pieces:
        board.set_piece(row, col, piece)

    # Verify all pieces are set correctly
    for row, col, piece in pieces:
        assert board.get_piece(row, col) == piece

    # Clear one piece and verify
    board.clear_square(0, 5)
    assert board.get_piece(0, 5) is None
    assert board.get_piece(0, 0) is not None


def test_board_total_size():
    """Test board has correct total size."""
    board = Board()
    total_squares = board.rows * board.cols
    assert total_squares == 500


def test_invalid_piece_structure_missing_type():
    """Test piece with missing 'type' key."""
    board = Board()

    # Piece without type should still be set (dict is stored as-is)
    # This tests that the board doesn't validate piece structure
    invalid_piece = {"owner": "NORTH"}  # Missing 'type'
    board.set_piece(5, 10, invalid_piece)

    piece = board.get_piece(5, 10)
    assert piece == invalid_piece


def test_invalid_piece_structure_missing_owner():
    """Test piece with missing 'owner' key."""
    board = Board()

    invalid_piece = {"type": "INFANTRY"}  # Missing 'owner'
    board.set_piece(5, 10, invalid_piece)

    piece = board.get_piece(5, 10)
    assert piece == invalid_piece


def test_piece_with_invalid_type():
    """Test piece with non-existent unit type."""
    board = Board()

    # Board doesn't validate piece type, so this should work
    invalid_piece = {"type": "DRAGON", "owner": "NORTH"}
    board.set_piece(5, 10, invalid_piece)

    piece = board.get_piece(5, 10)
    assert piece["type"] == "DRAGON"


def test_piece_with_invalid_owner():
    """Test piece with owner other than NORTH/SOUTH."""
    board = Board()

    # Board doesn't validate owner, so this should work
    invalid_piece = {"type": "INFANTRY", "owner": "EAST"}
    board.set_piece(5, 10, invalid_piece)

    piece = board.get_piece(5, 10)
    assert piece["owner"] == "EAST"


def test_piece_with_none_values():
    """Test piece with None values."""
    board = Board()

    # Board should handle pieces with None values
    none_piece = {"type": None, "owner": None}
    board.set_piece(5, 10, none_piece)

    piece = board.get_piece(5, 10)
    assert piece["type"] is None
    assert piece["owner"] is None


def test_piece_with_empty_string():
    """Test piece with empty string values."""
    board = Board()

    empty_piece = {"type": "", "owner": ""}
    board.set_piece(5, 10, empty_piece)

    piece = board.get_piece(5, 10)
    assert piece["type"] == ""
    assert piece["owner"] == ""


def test_overwriting_piece():
    """Test overwriting an existing piece."""
    board = Board()

    piece1 = {"type": "INFANTRY", "owner": "NORTH"}
    piece2 = {"type": "CAVALRY", "owner": "SOUTH"}

    board.set_piece(5, 10, piece1)
    assert board.get_piece(5, 10) == piece1

    board.set_piece(5, 10, piece2)
    assert board.get_piece(5, 10) == piece2


def test_clear_piece_on_square_with_piece():
    """Test clearing a square that has a piece."""
    board = Board()

    piece = {"type": "INFANTRY", "owner": "NORTH"}
    board.set_piece(5, 10, piece)
    assert board.get_piece(5, 10) == piece

    board.clear_square(5, 10)
    assert board.get_piece(5, 10) is None


def test_clear_piece_on_empty_square():
    """Test clearing a square that's already empty."""
    board = Board()

    # Square is initially empty
    assert board.get_piece(5, 10) is None

    # Clear it again (should not raise error)
    board.clear_square(5, 10)
    assert board.get_piece(5, 10) is None


def test_turn_mutation():
    """Test direct mutation of turn (should be avoided in practice)."""
    board = Board()
    assert board.turn == 'NORTH'

    # Direct mutation (not recommended but possible)
    board._turn = 'SOUTH'
    assert board.turn == 'SOUTH'
    assert board.turn_side() == 'SOUTH'

    # Change back
    board._turn = 'NORTH'
    assert board.turn == 'NORTH'


def test_piece_immutability_not_enforced():
    """Test that pieces are not immutable after setting."""
    board = Board()

    original_piece = {"type": "INFANTRY", "owner": "NORTH"}
    board.set_piece(5, 10, original_piece)

    # Modify the original dict reference
    original_piece["type"] = "CAVALRY"

    # The piece on the board is also modified (same reference)
    piece = board.get_piece(5, 10)
    assert piece["type"] == "CAVALRY"


def test_all_coordinates_valid():
    """Test that all coordinates within board bounds are valid."""
    board = Board()

    # Check all valid coordinates
    valid_count = 0
    for row in range(board.rows):
        for col in range(board.cols):
            if board.is_valid_square(row, col):
                valid_count += 1

    assert valid_count == 500  # All 500 squares should be valid
