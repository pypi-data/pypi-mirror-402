"""
Tests for KFEN whitespace handling in FEN strings.

Tests that KFEN files can be saved with formatted FEN strings
(newlines after each "/" for readability) and loaded correctly.
"""

import os
import tempfile
import unittest

from pykrieg.board import Board
from pykrieg.fen import Fen
from pykrieg.kfen import KFENMetadata, read_kfen, reconstruct_board_from_history, write_kfen


class TestKFENWhitespace(unittest.TestCase):
    """Test KFEN handling of formatted FEN strings."""

    def test_kfen_save_and_load(self):
        """Test that KFEN saves and loads correctly."""
        # Create a board with some units and terrain
        board = Board()
        board.create_and_place_unit(0, 0, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(5, 10, 'CAVALRY', 'NORTH')
        board.create_and_place_unit(19, 24, 'INFANTRY', 'SOUTH')

        # Add some terrain
        board.set_terrain(5, 5, 'MOUNTAIN')
        board.set_terrain(10, 10, 'MOUNTAIN_PASS')
        board.set_terrain(15, 15, 'FORTRESS')

        # Save as KFEN
        kfen_file = os.path.join(tempfile.gettempdir(), "test_formatted.kfen")
        metadata = KFENMetadata(game_name="Whitespace Test")
        write_kfen(board, kfen_file, metadata)

        # Read the file and verify it's valid JSON
        with open(kfen_file) as f:
            content = f.read()

        # Verify the JSON is valid (can be parsed without error)
        import json
        data = json.loads(content)
        self.assertIn('board_info', data)
        self.assertIn('fen', data['board_info'])

        # Verify FEN string is saved (as single line for valid JSON)
        fen_string = data['board_info']['fen']
        self.assertIsInstance(fen_string, str)
        self.assertGreater(len(fen_string), 0)

        # Verify we can load the KFEN file successfully
        document = read_kfen(kfen_file)
        self.assertIsNotNone(document)

        # Clean up
        os.remove(kfen_file)

    def test_kfen_load_formatted_fen(self):
        """Test that KFEN can load FEN with newlines and indentation."""
        # Create a board with some units and terrain
        board1 = Board()
        board1.create_and_place_unit(0, 0, 'INFANTRY', 'NORTH')
        board1.create_and_place_unit(5, 10, 'CAVALRY', 'NORTH')
        board1.create_and_place_unit(19, 24, 'INFANTRY', 'SOUTH')
        board1.set_terrain(5, 5, 'MOUNTAIN')

        # Save as KFEN (which will format the FEN)
        kfen_file = os.path.join(tempfile.gettempdir(), "test_load_formatted.kfen")
        write_kfen(board1, kfen_file)

        # Load the KFEN
        document = read_kfen(kfen_file)

        # Reconstruct the board
        board2 = reconstruct_board_from_history(document)

        # Verify the board state matches
        self.assertEqual(board1.rows, board2.rows)
        self.assertEqual(board1.cols, board2.cols)

        # Verify pieces
        board1.get_piece(0, 0)
        piece2_00 = board2.get_piece(0, 0)
        self.assertIsNotNone(piece2_00)
        self.assertEqual(piece2_00.unit_type, 'INFANTRY')
        self.assertEqual(piece2_00.owner, 'NORTH')

        board1.get_piece(5, 10)
        piece2_510 = board2.get_piece(5, 10)
        self.assertIsNotNone(piece2_510)
        self.assertEqual(piece2_510.unit_type, 'CAVALRY')
        self.assertEqual(piece2_510.owner, 'NORTH')

        board1.get_piece(19, 24)
        piece2_1924 = board2.get_piece(19, 24)
        self.assertIsNotNone(piece2_1924)
        self.assertEqual(piece2_1924.unit_type, 'INFANTRY')
        self.assertEqual(piece2_1924.owner, 'SOUTH')

        # Verify terrain
        self.assertEqual(board1.get_terrain(5, 5), 'MOUNTAIN')
        self.assertEqual(board2.get_terrain(5, 5), 'MOUNTAIN')

        # Clean up
        os.remove(kfen_file)

    def test_kfen_roundtrip_with_terrain(self):
        """Test complete roundtrip with formatted FEN including all terrain types."""
        # Create a board with all terrain types
        board1 = Board()

        # Add pieces on different terrain types
        board1.create_and_place_unit(0, 0, 'INFANTRY', 'NORTH')
        board1.create_and_place_unit(5, 5, 'CAVALRY', 'SOUTH')

        # Set various terrain
        board1.set_terrain(2, 2, 'MOUNTAIN')
        board1.set_terrain(3, 3, 'MOUNTAIN_PASS')
        board1.set_terrain(4, 4, 'FORTRESS')
        board1.set_terrain(5, 5, 'ARSENAL')
        board1.set_arsenal(5, 5, 'SOUTH')

        # Save and load
        kfen_file = os.path.join(tempfile.gettempdir(), "test_terrain_roundtrip.kfen")
        write_kfen(board1, kfen_file)

        document = read_kfen(kfen_file)
        board2 = reconstruct_board_from_history(document)

        # Verify all terrain types preserved
        self.assertEqual(board2.get_terrain(2, 2), 'MOUNTAIN')
        self.assertEqual(board2.get_terrain(3, 3), 'MOUNTAIN_PASS')
        self.assertEqual(board2.get_terrain(4, 4), 'FORTRESS')
        self.assertEqual(board2.get_terrain(5, 5), 'ARSENAL')
        self.assertEqual(board2.get_arsenal_owner(5, 5), 'SOUTH')

        # Verify pieces
        piece_00 = board2.get_piece(0, 0)
        self.assertEqual(piece_00.unit_type, 'INFANTRY')
        self.assertEqual(piece_00.owner, 'NORTH')

        piece_55 = board2.get_piece(5, 5)
        self.assertEqual(piece_55.unit_type, 'CAVALRY')
        self.assertEqual(piece_55.owner, 'SOUTH')

        # Clean up
        os.remove(kfen_file)

    def test_manual_formatted_fen_loads(self):
        """Test that manually formatted FEN (like the example file) loads correctly."""
        # Create a manually formatted FEN string with newlines and indentation
        formatted_fen = """_________________________/
            _______f______A__________/
            _________mmmm____________/
            __R____A_m_______________/
            _________m_______________/
            ____X____(I)_______________/
            __CC_IIKIm_______________/
            __CCIWIIIm__________f____/
            _____I___m__f____________/
            _________________________/
            ______________iiikc______/
            ______________iiicc______/
            __f___________iiic_______/
            ___________mmmmmx________/
            _______________(w)______r__/
            _______________m_________/
            _______________m_________/
            _______________m_________/
            _________________________/
            __a___________________a__"""

        # Load the formatted FEN
        board = Fen.fen_to_board(formatted_fen)

        # Verify board was created successfully
        self.assertIsNotNone(board)
        self.assertEqual(board.rows, 20)
        self.assertEqual(board.cols, 25)

        # Verify some pieces were loaded
        # The FEN has 'R' at row 3, col 2
        piece = board.get_piece(3, 2)
        self.assertIsNotNone(piece)
        self.assertEqual(piece.unit_type, 'RELAY')
        self.assertEqual(piece.owner, 'NORTH')

        # Verify terrain
        # Row 2: "_________mmmm____________" - mountains at cols 9,10,11,12
        self.assertEqual(board.get_terrain(2, 9), 'MOUNTAIN')
        # Row 5: "____X____(I)_______________" - (I) is at col 9 (4 + 1 + 4 spaces)
        self.assertEqual(board.get_terrain(5, 9), 'MOUNTAIN_PASS')

    def test_multiple_roundtrip_preserves_state(self):
        """Test that multiple save/load cycles preserve all state."""
        board1 = Board()

        # Add complex state
        board1.create_and_place_unit(0, 0, 'INFANTRY', 'NORTH')
        board1.create_and_place_unit(5, 10, 'CAVALRY', 'SOUTH')
        board1.create_and_place_unit(10, 15, 'CANNON', 'NORTH')
        board1.set_terrain(3, 3, 'MOUNTAIN')
        board1.set_terrain(7, 7, 'FORTRESS')
        board1.set_arsenal(12, 12, 'NORTH')

        # Do multiple roundtrips
        kfen_file = os.path.join(tempfile.gettempdir(), "test_multi_roundtrip.kfen")

        for _i in range(3):
            write_kfen(board1, kfen_file)
            document = read_kfen(kfen_file)
            board1 = reconstruct_board_from_history(document)

        # Verify state after multiple roundtrips
        piece_00 = board1.get_piece(0, 0)
        self.assertEqual(piece_00.unit_type, 'INFANTRY')
        self.assertEqual(piece_00.owner, 'NORTH')

        self.assertEqual(board1.get_terrain(3, 3), 'MOUNTAIN')
        self.assertEqual(board1.get_terrain(7, 7), 'FORTRESS')
        self.assertEqual(board1.get_arsenal_owner(12, 12), 'NORTH')

        # Clean up
        os.remove(kfen_file)


if __name__ == '__main__':
    unittest.main()
