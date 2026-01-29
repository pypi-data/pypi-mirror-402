"""
Additional tests for Phase 7 gaps - stress, error paths, validation, compliance, performance, and docs.
"""

import time
from pathlib import Path

import pytest

from pykrieg import Board, Fen


class TestStressTests:
    """Stress tests for full board and edge cases."""

    def test_full_board_500_pieces(self):
        """Test board with all 500 squares filled with pieces."""
        board1 = Board()
        # ARSENAL is now terrain, not a unit type (0.2.1)
        unit_types = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

        # Fill entire board
        piece_count = 0
        for row in range(board1.rows):
            for col in range(board1.cols):
                owner = 'NORTH' if row < board1.territory_boundary else 'SOUTH'
                piece_type = unit_types[(row + col) % len(unit_types)]
                board1.set_piece(row, col, {'type': piece_type, 'owner': owner})
                piece_count += 1

        assert piece_count == 500, f"Expected 500 pieces, got {piece_count}"

        # Serialize
        fen = Fen.board_to_fen(board1)

        # Deserialize
        board2 = Fen.fen_to_board(fen)

        # Verify all pieces match (board1 has dicts, board2 has Unit objects)
        for row in range(board1.rows):
            for col in range(board1.cols):
                piece1 = board1.get_piece(row, col)
                piece2 = board2.get_piece(row, col)
                # Compare by type and owner since piece1 is dict and piece2 is Unit
                if isinstance(piece1, dict):
                    assert piece2.unit_type == piece1['type'], f"Mismatch at ({row}, {col})"
                    assert piece2.owner == piece1['owner'], f"Mismatch at ({row}, {col})"
                else:
                    assert piece1 == piece2, f"Mismatch at ({row}, {col})"

    def test_multiple_rapid_serializations(self):
        """Test 100 rapid serialization/deserialization cycles."""
        board = Board()
        board.set_piece(5, 10, {'type': 'CAVALRY', 'owner': 'NORTH'})

        # Perform 100 roundtrips
        for _i in range(100):
            fen = Fen.board_to_fen(board)
            board = Fen.fen_to_board(fen)
            piece = board.get_piece(5, 10)
            assert piece.unit_type == 'CAVALRY'
            assert piece.owner == 'NORTH'

    def test_extreme_coordinate_conversions(self):
        """Test extreme spreadsheet coordinates."""
        # Test very large column numbers
        assert Board.spreadsheet_to_tuple("18278A") == (0, 18277)
        assert Board.tuple_to_spreadsheet(0, 18277) == "18278A"

        # Test large row numbers
        assert Board.spreadsheet_to_tuple("1ALK") == (998, 0)
        assert Board.tuple_to_spreadsheet(998, 0) == "1ALK"

        # Test both large
        assert Board.spreadsheet_to_tuple("18278ALK") == (998, 18277)
        assert Board.tuple_to_spreadsheet(998, 18277) == "18278ALK"

    def test_board_with_all_unit_types_on_every_square(self):
        """Test board with alternating all 6 unit types on every square."""
        board = Board()
        # ARSENAL is now terrain, not a unit type (0.2.1)
        unit_types = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

        for row in range(board.rows):
            for col in range(board.cols):
                owner = 'NORTH' if row < board.territory_boundary else 'SOUTH'
                piece_type = unit_types[(row * board.cols + col) % len(unit_types)]
                board.set_piece(row, col, {'type': piece_type, 'owner': owner})

        # Serialize and deserialize
        fen = Fen.board_to_fen(board)
        board2 = Fen.fen_to_board(fen)

        # Verify pattern preserved
        for row in range(board.rows):
            for col in range(board.cols):
                expected_type = unit_types[(row * board.cols + col) % len(unit_types)]
                expected_owner = 'NORTH' if row < board.territory_boundary else 'SOUTH'
                piece = board2.get_piece(row, col)
                assert piece.unit_type == expected_type
                assert piece.owner == expected_owner


class TestComprehensiveErrorPaths:
    """Comprehensive error path testing for all public methods."""

    def test_get_piece_all_invalid_coordinates(self):
        """Test get_piece with all types of invalid coordinates."""
        board = Board()

        # Boundary values
        with pytest.raises(ValueError):
            board.get_piece(-1, 0)
        with pytest.raises(ValueError):
            board.get_piece(20, 0)
        with pytest.raises(ValueError):
            board.get_piece(0, -1)
        with pytest.raises(ValueError):
            board.get_piece(0, 25)

        # Far out of bounds
        with pytest.raises(ValueError):
            board.get_piece(-100, -100)
        with pytest.raises(ValueError):
            board.get_piece(1000, 1000)

        # Mixed valid/invalid
        with pytest.raises(ValueError):
            board.get_piece(5, 25)  # Valid row, invalid col
        with pytest.raises(ValueError):
            board.get_piece(20, 5)  # Invalid row, valid col

    def test_set_piece_all_invalid_coordinates(self):
        """Test set_piece with all types of invalid coordinates."""
        board = Board()
        piece = {'type': 'INFANTRY', 'owner': 'NORTH'}

        # Boundary values
        with pytest.raises(ValueError):
            board.set_piece(-1, 0, piece)
        with pytest.raises(ValueError):
            board.set_piece(20, 0, piece)
        with pytest.raises(ValueError):
            board.set_piece(0, -1, piece)
        with pytest.raises(ValueError):
            board.set_piece(0, 25, piece)

        # Far out of bounds
        with pytest.raises(ValueError):
            board.set_piece(-100, -100, piece)
        with pytest.raises(ValueError):
            board.set_piece(1000, 1000, piece)

    def test_clear_square_all_invalid_coordinates(self):
        """Test clear_square with all types of invalid coordinates."""
        board = Board()

        # Boundary values
        with pytest.raises(ValueError):
            board.clear_square(-1, 0)
        with pytest.raises(ValueError):
            board.clear_square(20, 0)
        with pytest.raises(ValueError):
            board.clear_square(0, -1)
        with pytest.raises(ValueError):
            board.clear_square(0, 25)

        # Far out of bounds
        with pytest.raises(ValueError):
            board.clear_square(-100, -100)
        with pytest.raises(ValueError):
            board.clear_square(1000, 1000)

    def test_get_territory_all_invalid_coordinates(self):
        """Test get_territory with all types of invalid coordinates."""
        board = Board()

        # Boundary values
        with pytest.raises(ValueError):
            board.get_territory(-1, 0)
        with pytest.raises(ValueError):
            board.get_territory(20, 0)
        with pytest.raises(ValueError):
            board.get_territory(0, -1)
        with pytest.raises(ValueError):
            board.get_territory(0, 25)

        # Far out of bounds
        with pytest.raises(ValueError):
            board.get_territory(-100, -100)
        with pytest.raises(ValueError):
            board.get_territory(1000, 1000)

    def test_is_north_territory_invalid_coordinates(self):
        """Test is_north_territory with invalid coordinates."""
        board = Board()

        with pytest.raises(ValueError):
            board.is_north_territory(-1, 0)
        with pytest.raises(ValueError):
            board.is_north_territory(20, 0)
        with pytest.raises(ValueError):
            board.is_north_territory(0, 25)

    def test_is_south_territory_invalid_coordinates(self):
        """Test is_south_territory with invalid coordinates."""
        board = Board()

        with pytest.raises(ValueError):
            board.is_south_territory(-1, 0)
        with pytest.raises(ValueError):
            board.is_south_territory(20, 0)
        with pytest.raises(ValueError):
            board.is_south_territory(0, 25)

    def test_non_dict_piece_values(self):
        """Test board methods with non-dict piece values."""
        board = Board()

        # set_piece should accept non-dict (0.1.0 doesn't validate)
        board.set_piece(5, 10, "string_piece")
        assert board.get_piece(5, 10) == "string_piece"

        board.set_piece(5, 11, 123)
        assert board.get_piece(5, 11) == 123

        board.set_piece(5, 12, None)
        assert board.get_piece(5, 12) is None

        board.set_piece(5, 13, ["list", "piece"])
        assert board.get_piece(5, 13) == ["list", "piece"]


class TestPieceStructureValidation:
    """Tests for piece structure validation (or lack thereof in 0.1.0)."""

    def test_invalid_piece_types_accepted(self):
        """Test that invalid piece types are accepted (0.1.0 design decision).

        Note: Piece validation is deferred to 0.1.2 when unit class system
        is implemented. For 0.1.0, any dict with 'type' and 'owner' keys
        is accepted without validation.
        """
        board = Board()

        # Invalid piece types should be accepted
        invalid_types = ['DRAGON', 'UNICORN', 'WIZARD', 'KNIGHT', 'BISHOP']
        for invalid_type in invalid_types:
            board.set_piece(5, 10, {'type': invalid_type, 'owner': 'NORTH'})
            piece = board.get_piece(5, 10)
            # get_piece returns the stored dict for invalid types
            if isinstance(piece, dict):
                assert piece['type'] == invalid_type, f"Invalid type {invalid_type} should be accepted"
            else:
                assert piece.unit_type == invalid_type, f"Invalid type {invalid_type} should be accepted"

    def test_invalid_owners_accepted(self):
        """Test that invalid owners are accepted (0.1.0 design decision)."""
        board = Board()

        # Invalid owners should be accepted
        invalid_owners = ['EAST', 'WEST', 'NEUTRAL', '195620352A', '195620352B']
        for invalid_owner in invalid_owners:
            board.set_piece(5, 10, {'type': 'INFANTRY', 'owner': invalid_owner})
            piece = board.get_piece(5, 10)
            # get_piece returns the stored dict for invalid owners
            if isinstance(piece, dict):
                assert piece['owner'] == invalid_owner, f"Invalid owner {invalid_owner} should be accepted"
            else:
                assert piece.owner == invalid_owner, f"Invalid owner {invalid_owner} should be accepted"

    def test_piece_with_extra_keys_accepted(self):
        """Test that pieces with extra keys are accepted."""
        board = Board()

        # Piece with extra attributes should be accepted
        piece_with_extra = {
            'type': 'INFANTRY',
            'owner': 'NORTH',
            'extra_field': 'value',
            'another_field': 123,
            'nested': {'deep': 'value'}
        }

        board.set_piece(5, 10, piece_with_extra)
        retrieved = board.get_piece(5, 10)
        assert retrieved == piece_with_extra

    def test_fen_roundtrip_with_invalid_pieces(self):
        """Test FEN roundtrip fails with invalid piece types.

        Note: FEN will fail during deserialization if piece type
        is not in SYMBOL_TO_PIECE mapping. This is expected behavior.
        """
        board = Board()

        # Valid piece type works fine
        board.set_piece(0, 0, {'type': 'INFANTRY', 'owner': 'NORTH'})
        fen = Fen.board_to_fen(board)
        board2 = Fen.fen_to_board(fen)
        assert board2.get_piece(0, 0).unit_type == 'INFANTRY'

        # Invalid piece type causes FEN to fail
        board.set_piece(0, 1, {'type': 'DRAGON', 'owner': 'NORTH'})

        # This should raise KeyError because 'DRAGON' is not in PIECE_SYMBOLS
        with pytest.raises(KeyError, match="DRAGON"):
            Fen.board_to_fen(board)


class TestKFENSpecCompliance:
    """Tests for explicit KFEN specification compliance."""

    def test_fen_structure_23_parts(self):
        """Test FEN has exactly 25 parts (20 rows + 5 metadata with turn state)."""
        board = Board()
        fen = Fen.board_to_fen(board)
        parts = fen.split('/')

        assert len(parts) == 25, f"Expected 25 parts, got {len(parts)}"

        # First 20 parts should be board data (25 chars each)
        for i in range(20):
            assert len(parts[i]) == 25, f"Row {i} should have 25 chars"

        # Part 20 should be turn (N or S)
        assert parts[20] in ['N', 'S'], f"Turn should be 'N' or 'S', got {parts[20]}"

        # Part 21 should be phase (M for 0.1.0)
        assert parts[21] == 'M', f"Phase should be 'M', got {parts[21]}"

        # Part 22 should be actions ([] for 0.1.0)
        assert parts[22] == '[]', f"Actions should be '[]', got {parts[22]}"

    def test_fen_turn_characters(self):
        """Test FEN uses correct turn characters."""
        board = Board()

        # North's turn
        board._turn = 'NORTH'
        fen_n = Fen.board_to_fen(board)
        assert '/N/' in fen_n

        # South's turn
        board._turn = 'SOUTH'
        fen_s = Fen.board_to_fen(board)
        assert '/S/' in fen_s

    def test_fen_phase_field(self):
        """Test FEN phase field is 'M' (Movement) for 0.1.0."""
        board = Board()
        fen = Fen.board_to_fen(board)
        parts = fen.split('/')

        # Phase is at index 21 (0-indexed)
        assert parts[21] == 'M', "Phase field should be 'M' for 0.1.0"

    def test_fen_actions_field(self):
        """Test FEN actions field is '[]' for 0.1.0."""
        board = Board()
        fen = Fen.board_to_fen(board)
        parts = fen.split('/')

        # Actions is at index 22 (0-indexed)
        assert parts[22] == '[]', "Actions field should be '[]' for 0.1.0"

    def test_fen_piece_symbols_match_constants(self):
        """Test FEN piece symbols match constants.py definitions."""
        board = Board()

        from pykrieg import constants

        # Add one of each piece type for North (uppercase)
        col = 0
        for unit_type in constants.ALL_UNIT_TYPES:
            symbol = constants.FEN_SYMBOLS[unit_type]
            board.set_piece(0, col, {'type': unit_type, 'owner': 'NORTH'})

            # Get FEN and verify symbol
            fen = Fen.board_to_fen(board)
            assert symbol in fen, f"Symbol {symbol} for {unit_type} not in FEN"

            col += 1
            # Clear for next iteration
            board.clear_square(0, col - 1)

    def test_fen_empty_square_symbol(self):
        """Test FEN uses '_' for empty squares."""
        board = Board()
        fen = Fen.board_to_fen(board)

        # Count underscores in board data
        parts = fen.split('/')
        board_data = parts[:20]
        underscores = sum(row.count('_') for row in board_data)

        assert underscores == 500, f"Expected 500 underscores, got {underscores}"


class TestPerformanceSanityChecks:
    """Performance sanity checks to ensure operations complete in reasonable time."""

    def test_full_board_serialization_performance(self):
        """Test full board serialization completes in <1 second."""
        board = Board()
        # ARSENAL is now terrain, not a unit type (0.2.1)
        unit_types = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

        # Fill entire board
        for row in range(board.rows):
            for col in range(board.cols):
                owner = 'NORTH' if row < board.territory_boundary else 'SOUTH'
                piece_type = unit_types[(row + col) % len(unit_types)]
                board.set_piece(row, col, {'type': piece_type, 'owner': owner})

        # Measure serialization time
        start = time.time()
        fen = Fen.board_to_fen(board)
        serialize_time = time.time() - start

        # Should complete in <1 second
        assert serialize_time < 1.0, f"Serialization took {serialize_time:.3f}s, expected <1.0s"

        # Measure deserialization time
        start = time.time()
        Fen.fen_to_board(fen)
        deserialize_time = time.time() - start

        # Should complete in <1 second
        assert deserialize_time < 1.0, f"Deserialization took {deserialize_time:.3f}s, expected <1.0s"

    def test_coordinate_conversions_performance(self):
        """Test 10,000 coordinate conversions complete in <1 second."""
        conversions = [
            lambda: Board.spreadsheet_to_tuple("18278ALK"),
            lambda: Board.tuple_to_spreadsheet(998, 18277),
            lambda: Board.tuple_to_index(998, 18277),
            lambda: Board.index_to_tuple(9999, board_cols=100, board_rows=100),
        ]

        start = time.time()
        for conversion in conversions:
            for _ in range(2500):  # 2500 * 4 = 10,000 conversions
                conversion()
        total_time = time.time() - start

        # Should complete in <1 second
        assert total_time < 1.0, f"10,000 conversions took {total_time:.3f}s, expected <1.0s"

    def test_100_serialization_roundtrips_performance(self):
        """Test 100 serialization roundtrips complete in <1 second."""
        board = Board()
        board.set_piece(5, 10, {'type': 'CAVALRY', 'owner': 'NORTH'})

        start = time.time()
        for _ in range(100):
            fen = Fen.board_to_fen(board)
            board = Fen.fen_to_board(fen)
        total_time = time.time() - start

        # Should complete in <1 second
        assert total_time < 1.0, f"100 roundtrips took {total_time:.3f}s, expected <1.0s"

    def test_empty_board_operations_performance(self):
        """Test empty board operations complete in <0.1 seconds."""
        board = Board()

        start = time.time()

        # 100 get operations
        for i in range(100):
            row = i // 25
            col = i % 25
            board.get_piece(row, col)

        # 100 set operations
        for i in range(100):
            row = i // 25
            col = i % 25
            board.set_piece(row, col, {'type': 'INFANTRY', 'owner': 'NORTH'})

        # 100 clear operations
        for i in range(100):
            row = i // 25
            col = i % 25
            board.clear_square(row, col)

        total_time = time.time() - start

        # Should complete in <0.1 second
        assert total_time < 0.1, f"300 operations took {total_time:.3f}s, expected <0.1s"


class TestDocumentationBuildVerification:
    """Tests to verify documentation builds successfully."""

    def test_documentation_files_exist(self):
        """Test all required documentation files exist."""
        project_root = Path(__file__).parent.parent

        # Check Sphinx configuration
        assert (project_root / 'docs' / 'conf.py').exists(), "Sphinx config not found"
        assert (project_root / 'docs' / 'Makefile').exists(), "Makefile not found"

        # Check documentation files
        assert (project_root / 'docs' / 'index.rst').exists(), "index.rst not found"
        assert (project_root / 'docs' / 'api.rst').exists(), "api.rst not found"

        # Check source files have docstrings
        import pykrieg.board
        import pykrieg.constants
        import pykrieg.fen

        assert pykrieg.board.__doc__ is not None, "board module missing docstring"
        assert pykrieg.fen.__doc__ is not None, "fen module missing docstring"
        assert pykrieg.constants.__doc__ is not None, "constants module missing docstring"

        assert Board.__doc__ is not None, "Board class missing docstring"
        assert Fen.__doc__ is not None, "Fen class missing docstring"

    def test_public_apis_have_docstrings(self):
        """Test all public Board and Fen methods have docstrings."""
        # Board methods
        assert Board.__init__.__doc__ is not None, "Board.__init__ missing docstring"
        assert Board.is_valid_square.__doc__ is not None, "is_valid_square missing docstring"
        assert Board.get_piece.__doc__ is not None, "get_piece missing docstring"
        assert Board.set_piece.__doc__ is not None, "set_piece missing docstring"
        assert Board.clear_square.__doc__ is not None, "clear_square missing docstring"
        assert Board.get_territory.__doc__ is not None, "get_territory missing docstring"

        # Coordinate methods
        assert Board.spreadsheet_to_tuple.__doc__ is not None, "spreadsheet_to_tuple missing docstring"
        assert Board.tuple_to_spreadsheet.__doc__ is not None, "tuple_to_spreadsheet missing docstring"
        assert Board.tuple_to_index.__doc__ is not None, "tuple_to_index missing docstring"
        assert Board.index_to_tuple.__doc__ is not None, "index_to_tuple missing docstring"

        # Fen methods
        assert Fen.board_to_fen.__doc__ is not None, "board_to_fen missing docstring"
        assert Fen.fen_to_board.__doc__ is not None, "fen_to_board missing docstring"
