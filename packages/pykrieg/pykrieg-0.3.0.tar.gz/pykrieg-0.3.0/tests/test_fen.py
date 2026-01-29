"""
Tests for FEN (Forsyth-Edwards Notation) serialization and deserialization.
"""

import pytest

from pykrieg.board import Board
from pykrieg.fen import Fen


class TestFenSerialization:
    """Test FEN format serialization and deserialization."""

    def test_empty_board_to_fen(self):
        """Test converting empty board to FEN."""
        board = Board()
        fen = Fen.board_to_fen(board)

        # Should have 20 rows of 25 underscores each
        parts = fen.split('/')
        assert len(parts) == 25  # 20 rows + 5 metadata (turn, phase, actions, turn_number, retreats)

        # Check board data is all underscores (strip newlines added for user-friendly formatting)
        board_data = parts[:20]
        for row in board_data:
            assert row.strip() == '_' * 25

    def test_empty_board_fen_roundtrip(self):
        """Test empty board FEN roundtrip."""
        board1 = Board()
        fen = Fen.board_to_fen(board1)
        board2 = Fen.fen_to_board(fen)

        # Verify boards are identical
        assert board1.turn == board2.turn
        for row in range(board1.rows):
            for col in range(board1.cols):
                assert board1.get_piece(row, col) == board2.get_piece(row, col)

    def test_board_with_pieces_to_fen(self):
        """Test converting board with pieces to FEN."""
        board = Board()

        # Add some pieces
        board.set_piece(0, 0, {'type': 'INFANTRY', 'owner': 'NORTH'})
        board.set_piece(5, 10, {'type': 'CAVALRY', 'owner': 'NORTH'})
        board.set_piece(15, 20, {'type': 'INFANTRY', 'owner': 'SOUTH'})

        fen = Fen.board_to_fen(board)

        # Verify FEN contains correct symbols
        assert 'I' in fen  # North infantry (uppercase)
        assert 'C' in fen  # North cavalry (uppercase)
        assert 'i' in fen  # South infantry (lowercase)

    def test_board_with_pieces_fen_roundtrip(self):
        """Test board with pieces FEN roundtrip."""
        board1 = Board()

        # Add pieces in various positions (arsenals as terrain)
        pieces = [
            (0, 0, 'INFANTRY', 'NORTH'),
            (2, 5, 'CAVALRY', 'NORTH'),
            (4, 10, 'CANNON', 'NORTH'),
            (8, 20, 'RELAY', 'NORTH'),
            (19, 24, 'INFANTRY', 'SOUTH'),
            (17, 19, 'CAVALRY', 'SOUTH'),
            (15, 14, 'CANNON', 'SOUTH'),
            (11, 4, 'RELAY', 'SOUTH'),
        ]

        for row, col, piece_type, owner in pieces:
            board1.set_piece(row, col, {'type': piece_type, 'owner': owner})

        # Add arsenals as terrain
        board1.set_arsenal(6, 15, 'NORTH')
        board1.set_arsenal(13, 9, 'SOUTH')

        fen = Fen.board_to_fen(board1)
        board2 = Fen.fen_to_board(fen)

        # Verify all pieces preserved
        for row, col, piece_type, owner in pieces:
            piece = board2.get_piece(row, col)
            assert piece is not None
            assert piece.unit_type == piece_type
            assert piece.owner == owner

    def test_turn_in_fen(self):
        """Test turn information in FEN."""
        # North's turn
        board1 = Board()
        fen1 = Fen.board_to_fen(board1)
        assert '/N/' in fen1

        # South's turn
        board2 = Board()
        board2._turn = 'SOUTH'
        fen2 = Fen.board_to_fen(board2)
        assert '/S/' in fen2

        # Verify turn preserved
        board3 = Fen.fen_to_board(fen2)
        assert board3.turn == 'SOUTH'

    def test_invalid_fen_wrong_parts(self):
        """Test invalid FEN strings with wrong number of parts."""
        with pytest.raises(ValueError):
            Fen.fen_to_board("abc/def")

    def test_invalid_fen_bad_turn(self):
        """Test invalid FEN with bad turn character."""
        # Create valid FEN but with bad turn
        empty_rows = '/'.join(['_' * 25] * 20)
        with pytest.raises(ValueError):
            Fen.fen_to_board(f"{empty_rows}/X/M/[]")

    def test_invalid_fen_wrong_row_length(self):
        """Test invalid FEN with wrong row length."""
        # Construct FEN with one short row
        rows = ['_' * 24 if i == 0 else '_' * 25 for i in range(20)]
        short_fen = '/'.join(rows) + "/N/M/[]"
        with pytest.raises(ValueError):
            Fen.fen_to_board(short_fen)

    def test_invalid_fen_bad_piece_symbol(self):
        """Test invalid FEN with bad piece symbol."""
        # Construct FEN with invalid piece symbol
        rows = ['_' * 25] * 20
        rows[5] = 'Z' + '_' * 24  # Z is not a valid piece symbol
        bad_fen = '/'.join(rows) + "/N/M/[]"
        with pytest.raises(ValueError):
            Fen.fen_to_board(bad_fen)

    def test_fen_non_string_input(self):
        """Test FEN with non-string input."""
        with pytest.raises(TypeError):
            Fen.fen_to_board(123)

        with pytest.raises(TypeError):
            Fen.fen_to_board(None)

    def test_fen_all_piece_types(self):
        """Test FEN handles all piece types."""
        board1 = Board()

        # Add one of each type for North and South (excluding ARSENAL - now terrain)
        pieces_north = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']
        pieces_south = ['INFANTRY', 'CAVALRY', 'CANNON', 'RELAY', 'SWIFT_CANNON', 'SWIFT_RELAY']

        col = 0
        for piece_type in pieces_north:
            board1.set_piece(0, col, {'type': piece_type, 'owner': 'NORTH'})
            col += 1

        col = 0
        for piece_type in pieces_south:
            board1.set_piece(19, col, {'type': piece_type, 'owner': 'SOUTH'})
            col += 1

        # Add arsenals as terrain
        board1.set_arsenal(0, 6, 'NORTH')
        board1.set_arsenal(19, 6, 'SOUTH')

        fen = Fen.board_to_fen(board1)
        board2 = Fen.fen_to_board(fen)

        # Verify all pieces preserved
        col = 0
        for piece_type in pieces_north:
            piece = board2.get_piece(0, col)
            assert piece.unit_type == piece_type
            assert piece.owner == 'NORTH'
            col += 1

        col = 0
        for piece_type in pieces_south:
            piece = board2.get_piece(19, col)
            assert piece.unit_type == piece_type
            assert piece.owner == 'SOUTH'
            col += 1

        # Verify arsenals
        assert board2.get_arsenal_owner(0, 6) == 'NORTH'
        assert board2.get_arsenal_owner(19, 6) == 'SOUTH'

    def test_fen_multiple_roundtrip(self):
        """Test multiple FEN roundtrips preserve state."""
        board1 = Board()

        # Add pieces randomly
        positions = [
            (0, 0, 'INFANTRY', 'NORTH'),
            (1, 5, 'CAVALRY', 'NORTH'),
            (2, 10, 'CANNON', 'NORTH'),
            (18, 0, 'INFANTRY', 'SOUTH'),
            (17, 5, 'CAVALRY', 'SOUTH'),
            (16, 10, 'CANNON', 'SOUTH'),
        ]

        for row, col, piece_type, owner in positions:
            board1.set_piece(row, col, {'type': piece_type, 'owner': owner})

        # Do multiple roundtrips
        board2 = Fen.fen_to_board(Fen.board_to_fen(board1))
        board3 = Fen.fen_to_board(Fen.board_to_fen(board2))
        board4 = Fen.fen_to_board(Fen.board_to_fen(board3))

        # Verify all boards are identical
        for row, col, piece_type, owner in positions:
            board1.get_piece(row, col)
            piece2 = board2.get_piece(row, col)
            piece3 = board3.get_piece(row, col)
            piece4 = board4.get_piece(row, col)

            # After FEN roundtrip, all pieces should be Unit objects
            assert piece2.unit_type == piece_type
            assert piece3.unit_type == piece_type
            assert piece4.unit_type == piece_type
            assert piece4.owner == owner

    def test_fen_phase_and_actions(self):
        """Test FEN includes phase and actions fields."""
        board = Board()
        fen = Fen.board_to_fen(board)

        parts = fen.split('/')
        # parts[20] is turn, parts[21] is phase ('M'), parts[22] is actions ('[]')
        # parts[23] is turn_number ('1'), parts[24] is retreats ('[]')
        assert len(parts) == 25
        assert parts[21] == 'M'  # Movement phase
        assert parts[22] == '[]'  # No actions
        assert parts[23] == '1'  # Turn number
        assert parts[24] == '[]'  # No retreats

    def test_fen_piece_symbols(self):
        """Test piece symbol mapping is correct."""
        assert Fen.PIECE_SYMBOLS['INFANTRY'] == 'I'
        assert Fen.PIECE_SYMBOLS['CAVALRY'] == 'C'
        assert Fen.PIECE_SYMBOLS['CANNON'] == 'K'
        assert Fen.PIECE_SYMBOLS['RELAY'] == 'R'
        assert Fen.PIECE_SYMBOLS['SWIFT_CANNON'] == 'W'
        assert Fen.PIECE_SYMBOLS['SWIFT_RELAY'] == 'X'

        assert Fen.SYMBOL_TO_PIECE['I'] == 'INFANTRY'
        assert Fen.SYMBOL_TO_PIECE['C'] == 'CAVALRY'
        assert Fen.SYMBOL_TO_PIECE['K'] == 'CANNON'
        assert Fen.SYMBOL_TO_PIECE['R'] == 'RELAY'
        assert Fen.SYMBOL_TO_PIECE['W'] == 'SWIFT_CANNON'
        assert Fen.SYMBOL_TO_PIECE['X'] == 'SWIFT_RELAY'

    def test_fen_extra_delimiters(self):
        """Test FEN with too many delimiters raises error."""
        # Construct valid FEN with extra delimiters
        rows = ['_' * 25] * 20
        # Add extra delimiter after board data
        extra_delim_fen = '/'.join(rows) + "/N/M/[]/extra"
        with pytest.raises(ValueError):
            Fen.fen_to_board(extra_delim_fen)

    def test_fen_missing_delimiters(self):
        """Test FEN with too few delimiters raises error."""
        # Construct FEN missing turn/phase/actions
        rows = ['_' * 25] * 19  # Only 19 rows instead of 20
        missing_delim_fen = '/'.join(rows) + "/N/M"
        with pytest.raises(ValueError):
            Fen.fen_to_board(missing_delim_fen)

    def test_fen_whitespace_handling(self):
        """Test FEN with leading/trailing whitespace."""
        board = Board()
        fen = Fen.board_to_fen(board)

        # FEN with leading/trailing whitespace should still work after stripping
        board2 = Fen.fen_to_board(fen.strip())
        assert board2.turn == board.turn

        # FEN with extra whitespace in the string should fail
        # (because split will create extra parts or invalid row data)
        with pytest.raises(ValueError):
            Fen.fen_to_board("  " + fen + "  ")

    def test_fen_lowercase_and_uppercase_pieces(self):
        """Test FEN correctly handles both uppercase (North) and lowercase (South) pieces."""
        board1 = Board()

        # Add North pieces (uppercase in FEN)
        board1.set_piece(0, 0, {'type': 'INFANTRY', 'owner': 'NORTH'})
        board1.set_piece(0, 1, {'type': 'CAVALRY', 'owner': 'NORTH'})

        # Add South pieces (lowercase in FEN)
        board1.set_piece(19, 0, {'type': 'INFANTRY', 'owner': 'SOUTH'})
        board1.set_piece(19, 1, {'type': 'CAVALRY', 'owner': 'SOUTH'})

        fen = Fen.board_to_fen(board1)

        # Verify uppercase and lowercase in FEN
        assert 'I' in fen  # North infantry
        assert 'C' in fen  # North cavalry
        assert 'i' in fen  # South infantry
        assert 'c' in fen  # South cavalry

        # Deserialize and verify
        board2 = Fen.fen_to_board(fen)
        piece_00 = board2.get_piece(0, 0)
        piece_01 = board2.get_piece(0, 1)
        piece_190 = board2.get_piece(19, 0)
        piece_191 = board2.get_piece(19, 1)

        assert piece_00.unit_type == 'INFANTRY'
        assert piece_00.owner == 'NORTH'
        assert piece_01.unit_type == 'CAVALRY'
        assert piece_01.owner == 'NORTH'
        assert piece_190.unit_type == 'INFANTRY'
        assert piece_190.owner == 'SOUTH'
        assert piece_191.unit_type == 'CAVALRY'
        assert piece_191.owner == 'SOUTH'

    def test_fen_all_squares_empty(self):
        """Test FEN with all squares empty."""
        board = Board()
        fen = Fen.board_to_fen(board)

        # Count underscores
        underscore_count = fen.count('_')
        assert underscore_count == 500, "Should have 500 empty squares"

        # No piece symbols
        for symbol in ['I', 'C', 'K', 'A', 'R', 'W', 'X', 'i', 'c', 'k', 'a', 'r', 'w', 'x']:
            assert symbol not in fen.split('/')[0], f"Should not have {symbol} in empty board"

    def test_fen_dict_style_piece(self):
        """Test FEN serialization with dict-style pieces (lines 73-74 coverage)."""
        board = Board()

        # Add a dict-style piece (common pattern for backward compatibility)
        dict_piece = {'type': 'INFANTRY', 'owner': 'NORTH'}
        board.set_piece(0, 0, dict_piece)

        # Should serialize successfully
        fen = Fen.board_to_fen(board)

        # Verify it appears in FEN
        assert 'I' in fen  # Infantry symbol

        # Verify roundtrip works
        board2 = Fen.fen_to_board(fen)
        retrieved = board2.get_piece(0, 0)
        assert retrieved.unit_type == 'INFANTRY'
        assert retrieved.owner == 'NORTH'

    def test_fen_invalid_piece_without_unit_type(self):
        """Test FEN serialization with invalid piece missing unit_type."""
        board = Board()

        # Create an invalid piece object (not a dict, no unit_type attribute)
        class InvalidPiece:
            def __init__(self):
                self.name = "invalid"

        invalid_piece = InvalidPiece()
        board.set_piece(0, 0, invalid_piece)

        # Should raise ValueError when trying to serialize
        with pytest.raises(ValueError, match="Piece has no unit_type attribute"):
            Fen.board_to_fen(board)
