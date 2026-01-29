"""
Integration tests for Pykrieg - testing complete workflows and scenarios.
"""

from pykrieg import Board, Fen


def test_full_board_serialization():
    """Test complete board serialization/deserialization with all squares filled."""
    board1 = Board()

    # Fill entire board with pieces (excluding ARSENAL - now terrain, not unit)
    unit_types = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

    for row in range(board1.rows):
        for col in range(board1.cols):
            owner = 'NORTH' if row < board1.territory_boundary else 'SOUTH'
            # Alternate unit types
            unit_type = unit_types[(row + col) % len(unit_types)]
            board1.create_and_place_unit(row, col, unit_type, owner)

    # Serialize
    fen = Fen.board_to_fen(board1)

    # Deserialize
    board2 = Fen.fen_to_board(fen)

    # Verify all pieces match (compare unit_type and owner)
    for row in range(board1.rows):
        for col in range(board1.cols):
            unit1 = board1.get_unit(row, col)
            unit2 = board2.get_unit(row, col)
            if unit1 is None and unit2 is None:
                continue
            if unit1 is None or unit2 is None:
                raise AssertionError(f"Mismatch at ({row}, {col})")
            assert unit1.unit_type == unit2.unit_type, f"Mismatch at ({row}, {col})"
            assert unit1.owner == unit2.owner, f"Mismatch at ({row}, {col})"

    # Verify turn is preserved
    assert board1.turn == board2.turn


def test_complex_scenario_with_turns():
    """Test complex scenario with multiple pieces and turn changes."""
    # Create initial board state
    board1 = Board()

    # Add pieces in strategic positions (arsenals as terrain)
    pieces = [
        (0, 0, 'INFANTRY', 'NORTH'),
        (0, 5, 'CAVALRY', 'NORTH'),
        (0, 10, 'CANNON', 'NORTH'),
        (0, 20, 'RELAY', 'NORTH'),
        (2, 2, 'SWIFT_CANNON', 'NORTH'),
        (2, 22, 'SWIFT_RELAY', 'NORTH'),
        (19, 0, 'INFANTRY', 'SOUTH'),
        (19, 5, 'CAVALRY', 'SOUTH'),
        (19, 10, 'CANNON', 'SOUTH'),
        (19, 20, 'RELAY', 'SOUTH'),
        (17, 2, 'SWIFT_CANNON', 'SOUTH'),
        (17, 22, 'SWIFT_RELAY', 'SOUTH'),
    ]

    for row, col, piece_type, owner in pieces:
        board1.create_and_place_unit(row, col, piece_type, owner)

    # Add arsenals as terrain
    board1.set_arsenal(0, 15, 'NORTH')
    board1.set_arsenal(19, 15, 'SOUTH')

    # Set turn to SOUTH
    board1._turn = 'SOUTH'

    # Serialize and deserialize
    fen = Fen.board_to_fen(board1)
    board2 = Fen.fen_to_board(fen)

    # Verify all pieces
    for row, col, piece_type, owner in pieces:
        unit = board2.get_unit(row, col)
        assert unit is not None, f"No unit at ({row}, {col})"
        assert unit.unit_type == piece_type, f"Wrong type at ({row}, {col})"
        assert unit.owner == owner, f"Wrong owner at ({row}, {col})"

    # Verify arsenals
    assert board2.get_arsenal_owner(0, 15) == 'NORTH'
    assert board2.get_arsenal_owner(19, 15) == 'SOUTH'

    # Verify turn
    assert board2.turn == 'SOUTH'


def test_territory_distribution():
    """Test territory distribution across full board."""
    board = Board()

    north_squares = board.get_territory_squares('NORTH')
    south_squares = board.get_territory_squares('SOUTH')

    # Verify exact counts
    assert len(north_squares) == 250, "North should have exactly 250 squares"
    assert len(south_squares) == 250, "South should have exactly 250 squares"

    # Fill territories and verify
    for row, col in north_squares:
        board.create_and_place_unit(row, col, 'INFANTRY', 'NORTH')

    for row, col in south_squares:
        board.create_and_place_unit(row, col, 'INFANTRY', 'SOUTH')

    # Serialize and verify
    fen = Fen.board_to_fen(board)
    board2 = Fen.fen_to_board(fen)

    # Count pieces by owner
    north_count = 0
    south_count = 0

    for row in range(board2.rows):
        for col in range(board2.cols):
            unit = board2.get_unit(row, col)
            if unit:
                if unit.owner == 'NORTH':
                    north_count += 1
                else:
                    south_count += 1

    assert north_count == 250, f"Expected 250 NORTH pieces, got {north_count}"
    assert south_count == 250, f"Expected 250 SOUTH pieces, got {south_count}"


def test_multiple_serialization_roundtrips():
    """Test multiple serialization/deserialization roundtrips preserve state."""
    board1 = Board()

    # Add pieces (arsenals as terrain)
    board1.create_and_place_unit(0, 0, 'INFANTRY', 'NORTH')
    board1.create_and_place_unit(5, 5, 'CAVALRY', 'NORTH')
    board1.create_and_place_unit(10, 10, 'CANNON', 'SOUTH')
    board1.set_arsenal(15, 15, 'SOUTH')

    # Perform multiple roundtrips
    board2 = Fen.fen_to_board(Fen.board_to_fen(board1))
    board3 = Fen.fen_to_board(Fen.board_to_fen(board2))
    board4 = Fen.fen_to_board(Fen.board_to_fen(board3))
    board5 = Fen.fen_to_board(Fen.board_to_fen(board4))

    # Verify units
    assert board5.get_unit(0, 0).unit_type == 'INFANTRY'
    assert board5.get_unit(5, 5).unit_type == 'CAVALRY'
    assert board5.get_unit(10, 10).unit_type == 'CANNON'
    # Verify arsenal
    assert board5.get_arsenal_owner(15, 15) == 'SOUTH'


def test_empty_board_operations():
    """Test operations on empty board."""
    board = Board()

    # Verify empty
    for row in range(board.rows):
        for col in range(board.cols):
            assert board.get_unit(row, col) is None

    # Serialize empty board
    fen = Fen.board_to_fen(board)

    # Should be all underscores
    assert 'I' not in fen  # No infantry
    assert 'i' not in fen  # No south infantry

    # Deserialize and verify
    board2 = Fen.fen_to_board(fen)
    for row in range(board2.rows):
        for col in range(board2.cols):
            assert board2.get_unit(row, col) is None


def test_board_with_single_piece():
    """Test board with single piece."""
    board1 = Board()
    board1.create_and_place_unit(10, 12, 'CAVALRY', 'SOUTH')

    fen = Fen.board_to_fen(board1)
    board2 = Fen.fen_to_board(fen)

    # Verify single piece
    unit = board2.get_unit(10, 12)
    assert unit is not None
    assert unit.unit_type == 'CAVALRY'
    assert unit.owner == 'SOUTH'

    # Verify all other squares are empty
    count = 0
    for row in range(board2.rows):
        for col in range(board2.cols):
            if board2.get_unit(row, col) is not None:
                count += 1

    assert count == 1


def test_coordinate_integration():
    """Test coordinate conversions with board operations."""
    board = Board()

    # Add piece using tuple coordinates
    board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

    # Get piece
    unit = board.get_unit(5, 10)
    assert unit.unit_type == 'INFANTRY'

    # Test spreadsheet coordinate conversion
    spreadsheet = Board.tuple_to_spreadsheet(5, 10)
    back_tuple = Board.spreadsheet_to_tuple(spreadsheet)
    assert back_tuple == (5, 10)

    # Test index conversion
    index = Board.tuple_to_index(5, 10)
    back_tuple = Board.index_to_tuple(index)
    assert back_tuple == (5, 10)

    # Verify piece still accessible through different coordinate systems
    assert board.get_unit(*back_tuple) == unit


def test_turn_integration():
    """Test turn integration with serialization."""
    board1 = Board()
    board1._turn = 'SOUTH'

    fen = Fen.board_to_fen(board1)
    assert '/S/' in fen

    board2 = Fen.fen_to_board(fen)
    assert board2.turn == 'SOUTH'

    # Change turn and re-serialize
    board2._turn = 'NORTH'
    fen2 = Fen.board_to_fen(board2)
    assert '/N/' in fen2

    board3 = Fen.fen_to_board(fen2)
    assert board3.turn == 'NORTH'


def test_all_unit_types_integration():
    """Test all unit types work correctly in integration."""
    board1 = Board()

    # Add one of each unit type for both players (excluding ARSENAL - now terrain)
    unit_types = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

    col = 0
    for unit_type in unit_types:
        board1.create_and_place_unit(0, col, unit_type, 'NORTH')
        board1.create_and_place_unit(19, col, unit_type, 'SOUTH')
        col += 1

    # Add arsenals as terrain
    board1.set_arsenal(0, 6, 'NORTH')
    board1.set_arsenal(19, 6, 'SOUTH')

    # Serialize
    fen = Fen.board_to_fen(board1)

    # Deserialize
    board2 = Fen.fen_to_board(fen)

    # Verify all unit types
    col = 0
    for unit_type in unit_types:
        north_unit = board2.get_unit(0, col)
        south_unit = board2.get_unit(19, col)

        assert north_unit.unit_type == unit_type
        assert north_unit.owner == 'NORTH'

        assert south_unit.unit_type == unit_type
        assert south_unit.owner == 'SOUTH'

        col += 1

    # Verify arsenals
    assert board2.get_arsenal_owner(0, 6) == 'NORTH'
    assert board2.get_arsenal_owner(19, 6) == 'SOUTH'
