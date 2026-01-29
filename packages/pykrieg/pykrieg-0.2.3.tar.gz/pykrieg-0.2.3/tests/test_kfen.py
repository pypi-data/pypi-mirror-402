"""
Unit tests for KFEN (Krieg Forsyth-Edwards Notation) module.

This module tests KFEN serialization, deserialization, validation,
and board reconstruction.
"""

import json
import os
import tempfile
import unittest

from pykrieg.board import Board as BoardClass
from pykrieg.fen import Fen
from pykrieg.kfen import (
    KFENAttack,
    KFENBoardInfo,
    KFENDocument,
    KFENGameState,
    KFENMetadata,
    KFENMove,
    KFENTurn,
    _dict_to_document,
    _document_to_dict,
    convert_fen_to_kfen,
    export_kfen_to_fen,
    read_kfen,
    reconstruct_board_from_history,
    validate_history,
    write_kfen,
)


class TestKFENDataStructures(unittest.TestCase):
    """Test KFEN data structure initialization."""

    def test_kfen_metadata_default(self):
        """Test KFENMetadata with default values."""
        metadata = KFENMetadata()
        self.assertIsNone(metadata.game_name)
        self.assertIsNotNone(metadata.save_date)
        self.assertIsNotNone(metadata.created_date)
        self.assertEqual(metadata.result, "ONGOING")
        self.assertIsNone(metadata.players)
        self.assertIsNone(metadata.event)

    def test_kfen_metadata_custom(self):
        """Test KFENMetadata with custom values."""
        metadata = KFENMetadata(
            game_name="Test Game",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z",
            players={"north": "Alice", "south": "Bob"},
            event="Tournament",
            result="NORTH_WINS"
        )
        self.assertEqual(metadata.game_name, "Test Game")
        self.assertEqual(metadata.save_date, "2026-01-17T12:00:00Z")
        self.assertEqual(metadata.created_date, "2026-01-15T10:00:00Z")
        self.assertEqual(metadata.players, {"north": "Alice", "south": "Bob"})
        self.assertEqual(metadata.event, "Tournament")
        self.assertEqual(metadata.result, "NORTH_WINS")

    def test_kfen_board_info_default(self):
        """Test KFENBoardInfo with default values."""
        board_info = KFENBoardInfo()
        self.assertEqual(board_info.rows, 20)
        self.assertEqual(board_info.cols, 25)
        self.assertEqual(board_info.fen, "")

    def test_kfen_board_info_custom(self):
        """Test KFENBoardInfo with custom values."""
        board_info = KFENBoardInfo(
            rows=15,
            cols=20,
            fen="___________________\n..."
        )
        self.assertEqual(board_info.rows, 15)
        self.assertEqual(board_info.cols, 20)
        self.assertEqual(board_info.fen, "___________________\n...")

    def test_kfen_game_state_default(self):
        """Test KFENGameState with default values."""
        game_state = KFENGameState()
        self.assertEqual(game_state.turn_number, 1)
        self.assertEqual(game_state.current_player, "NORTH")
        self.assertEqual(game_state.current_phase, "M")

    def test_kfen_game_state_custom(self):
        """Test KFENGameState with custom values."""
        game_state = KFENGameState(
            turn_number=10,
            current_player="SOUTH",
            current_phase="B"
        )
        self.assertEqual(game_state.turn_number, 10)
        self.assertEqual(game_state.current_player, "SOUTH")
        self.assertEqual(game_state.current_phase, "B")

    def test_kfen_move(self):
        """Test KFENMove initialization."""
        move = KFENMove(
            from_pos={"row": 5, "col": 10},
            to_pos={"row": 6, "col": 11},
            unit_type="INFANTRY",
            unit_id=12345,
            was_retreat=False
        )
        self.assertEqual(move.from_pos, {"row": 5, "col": 10})
        self.assertEqual(move.to_pos, {"row": 6, "col": 11})
        self.assertEqual(move.unit_type, "INFANTRY")
        self.assertEqual(move.unit_id, 12345)
        self.assertEqual(move.was_retreat, False)
        self.assertIsNone(move.destroyed_arsenal)

    def test_kfen_move_with_arsenal_destruction(self):
        """Test KFENMove with arsenal destruction."""
        move = KFENMove(
            from_pos={"row": 5, "col": 10},
            to_pos={"row": 6, "col": 11},
            unit_type="CAVALRY",
            unit_id=54321,
            was_retreat=False,
            destroyed_arsenal={"row": 6, "col": 11, "owner": "SOUTH"}
        )
        self.assertEqual(move.destroyed_arsenal, {"row": 6, "col": 11, "owner": "SOUTH"})

    def test_kfen_attack(self):
        """Test KFENAttack initialization."""
        attack = KFENAttack(
            target={"row": 8, "col": 12},
            outcome="CAPTURE",
            captured_unit={"unit_type": "INFANTRY", "owner": "SOUTH"},
            retreat_positions=[{"row": 8, "col": 11}]
        )
        self.assertEqual(attack.target, {"row": 8, "col": 12})
        self.assertEqual(attack.outcome, "CAPTURE")
        self.assertEqual(attack.captured_unit, {"unit_type": "INFANTRY", "owner": "SOUTH"})
        self.assertEqual(len(attack.retreat_positions), 1)

    def test_kfen_turn_default(self):
        """Test KFENTurn with default values."""
        turn = KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="M"
        )
        self.assertEqual(turn.turn_number, 1)
        self.assertEqual(turn.player, "NORTH")
        self.assertEqual(turn.phase, "M")
        self.assertEqual(len(turn.moves), 0)
        self.assertIsNone(turn.phase_change)
        self.assertIsNone(turn.attack)
        self.assertIsNone(turn.end_turn)

    def test_kfen_document_default(self):
        """Test KFENDocument with default values."""
        document = KFENDocument()
        self.assertEqual(document.kfen_version, "1.0")
        self.assertEqual(len(document.turn_history), 0)

    def test_kfen_document_custom(self):
        """Test KFENDocument with custom values."""
        document = KFENDocument(
            kfen_version="1.0",
            metadata=KFENMetadata(game_name="Test"),
            board_info=KFENBoardInfo(rows=20, cols=25),
            game_state=KFENGameState(turn_number=5),
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M",
                    moves=[
                        KFENMove(
                            from_pos={"row": 5, "col": 10},
                            to_pos={"row": 6, "col": 11},
                            unit_type="INFANTRY",
                            unit_id=12345,
                            was_retreat=False
                        )
                    ]
                )
            ]
        )
        self.assertEqual(document.kfen_version, "1.0")
        self.assertEqual(document.metadata.game_name, "Test")
        self.assertEqual(document.board_info.rows, 20)
        self.assertEqual(document.game_state.turn_number, 5)
        self.assertEqual(len(document.turn_history), 1)


class TestKFENSerialization(unittest.TestCase):
    """Test KFEN serialization to JSON."""

    def test_document_to_dict_empty(self):
        """Test serialization of empty KFENDocument."""
        document = KFENDocument()
        data = _document_to_dict(document)

        self.assertIn("kfen_version", data)
        self.assertIn("metadata", data)
        self.assertIn("board_info", data)
        self.assertIn("game_state", data)
        self.assertIn("turn_history", data)
        self.assertIn("undo_redo", data)

        self.assertEqual(data["kfen_version"], "1.0")
        self.assertEqual(data["metadata"]["result"], "ONGOING")
        self.assertEqual(data["turn_history"], [])

    def test_document_to_dict_with_moves(self):
        """Test serialization of KFENDocument with moves."""
        turn = KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="M",
            moves=[
                KFENMove(
                    from_pos={"row": 5, "col": 10},
                    to_pos={"row": 6, "col": 11},
                    unit_type="INFANTRY",
                    unit_id=12345,
                    was_retreat=False
                ),
                KFENMove(
                    from_pos={"row": 7, "col": 12},
                    to_pos={"row": 8, "col": 13},
                    unit_type="CAVALRY",
                    unit_id=54321,
                    was_retreat=True
                )
            ]
        )
        document = KFENDocument(turn_history=[turn])
        data = _document_to_dict(document)

        self.assertEqual(len(data["turn_history"]), 1)
        turn_data = data["turn_history"][0]
        self.assertEqual(len(turn_data["moves"]), 2)
        self.assertEqual(turn_data["moves"][0]["unit_type"], "INFANTRY")
        self.assertEqual(turn_data["moves"][1]["was_retreat"], True)

    def test_document_to_dict_with_attack(self):
        """Test serialization of KFENDocument with attack."""
        turn = KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="B",
            attack=KFENAttack(
                target={"row": 8, "col": 12},
                outcome="CAPTURE",
                captured_unit={"unit_type": "INFANTRY", "owner": "SOUTH"},
                retreat_positions=[]
            )
        )
        document = KFENDocument(turn_history=[turn])
        data = _document_to_dict(document)

        self.assertEqual(len(data["turn_history"]), 1)
        turn_data = data["turn_history"][0]
        self.assertIsNotNone(turn_data["attack"])
        self.assertEqual(turn_data["attack"]["outcome"], "CAPTURE")
        self.assertEqual(turn_data["attack"]["target"], {"row": 8, "col": 12})


class TestKFENDeserialization(unittest.TestCase):
    """Test KFEN deserialization from JSON."""

    def test_dict_to_document_empty(self):
        """Test deserialization of empty KFEN data."""
        data = {
            "kfen_version": "1.0",
            "metadata": {
                "game_name": None,
                "save_date": "2026-01-17T12:00:00Z",
                "created_date": "2026-01-17T12:00:00Z",
                "players": None,
                "event": None,
                "result": "ONGOING"
            },
            "board_info": {
                "rows": 20,
                "cols": 25,
                "fen": ""
            },
            "game_state": {
                "turn_number": 1,
                "current_player": "NORTH",
                "current_phase": "M"
            },
            "turn_history": [],
            "undo_redo": {
                "max_history": 100,
                "current_index": 0
            }
        }

        document = _dict_to_document(data)
        self.assertEqual(document.kfen_version, "1.0")
        self.assertEqual(document.metadata.result, "ONGOING")
        self.assertEqual(len(document.turn_history), 0)

    def test_dict_to_document_with_moves(self):
        """Test deserialization of KFEN data with moves."""
        data = {
            "kfen_version": "1.0",
            "metadata": {
                "game_name": "Test Game",
                "save_date": "2026-01-17T12:00:00Z",
                "created_date": "2026-01-17T12:00:00Z",
                "players": None,
                "event": None,
                "result": "ONGOING"
            },
            "board_info": {
                "rows": 20,
                "cols": 25,
                "fen": ""
            },
            "game_state": {
                "turn_number": 1,
                "current_player": "NORTH",
                "current_phase": "M"
            },
            "turn_history": [
                {
                    "turn_number": 1,
                    "player": "NORTH",
                    "phase": "M",
                    "moves": [
                        {
                            "from": {"row": 5, "col": 10},
                            "to": {"row": 6, "col": 11},
                            "unit_type": "INFANTRY",
                            "unit_id": 12345,
                            "was_retreat": False,
                            "destroyed_arsenal": None
                        }
                    ],
                    "phase_change": None,
                    "attack": None,
                    "end_turn": None
                }
            ],
            "undo_redo": {
                "max_history": 100,
                "current_index": 1
            }
        }

        document = _dict_to_document(data)
        self.assertEqual(len(document.turn_history), 1)
        turn = document.turn_history[0]
        self.assertEqual(len(turn.moves), 1)
        self.assertEqual(turn.moves[0].unit_type, "INFANTRY")


class TestKFENValidation(unittest.TestCase):
    """Test KFEN history validation."""

    def test_validate_empty_history(self):
        """Test validation of empty turn history."""
        document = KFENDocument()
        is_valid, error = validate_history(document)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_valid_turn_sequence(self):
        """Test validation of valid turn sequence."""
        document = KFENDocument(
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="M"),
                KFENTurn(turn_number=2, player="SOUTH", phase="M"),
                KFENTurn(turn_number=3, player="NORTH", phase="M")
            ]
        )
        is_valid, error = validate_history(document)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_invalid_turn_number(self):
        """Test validation detects invalid turn numbers."""
        document = KFENDocument(
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="M"),
                KFENTurn(turn_number=3, player="SOUTH", phase="M"),  # Skipped turn 2
            ]
        )
        is_valid, error = validate_history(document)
        self.assertFalse(is_valid)
        self.assertIn("expected turn number 2", error)

    def test_validate_too_many_moves(self):
        """Test validation detects too many moves in a turn."""
        turn = KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="M",
            moves=[
                KFENMove(
                    from_pos={"row": 5, "col": 10},
                    to_pos={"row": 6, "col": 11},
                    unit_type="INFANTRY",
                    unit_id=1,
                    was_retreat=False
                ) for _ in range(6)  # 6 moves (max is 5)
            ]
        )
        document = KFENDocument(turn_history=[turn])
        is_valid, error = validate_history(document)
        self.assertFalse(is_valid)
        self.assertIn("too many moves", error)

    def test_validate_invalid_player(self):
        """Test validation detects invalid player."""
        turn = KFENTurn(
            turn_number=1,
            player="INVALID",  # Invalid player
            phase="M"
        )
        document = KFENDocument(turn_history=[turn])
        is_valid, error = validate_history(document)
        self.assertFalse(is_valid)
        self.assertIn("expected player", error)

    def test_validate_invalid_phase(self):
        """Test validation detects invalid phase."""
        turn = KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="X"  # Invalid phase
        )
        document = KFENDocument(turn_history=[turn])
        is_valid, error = validate_history(document)
        self.assertFalse(is_valid)
        self.assertIn("invalid phase", error)

    def test_validate_invalid_result(self):
        """Test validation detects invalid result."""
        document = KFENDocument(
            metadata=KFENMetadata(result="INVALID_RESULT")
        )
        is_valid, error = validate_history(document)
        self.assertFalse(is_valid)
        self.assertIn("Invalid metadata result", error)

    def test_validate_valid_results(self):
        """Test validation accepts all valid results."""
        for result in ["ONGOING", "NORTH_WINS", "SOUTH_WINS", "DRAW"]:
            document = KFENDocument(
                metadata=KFENMetadata(result=result)
            )
            is_valid, error = validate_history(document)
            self.assertTrue(is_valid, f"Result {result} should be valid")
            self.assertIsNone(error)


class TestKFENFileIO(unittest.TestCase):
    """Test KFEN file I/O operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_write_and_read_kfen(self):
        """Test writing and reading KFEN file."""
        # Create a simple board
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(15, 12, 'CAVALRY', 'SOUTH')

        # Set metadata
        metadata = KFENMetadata(
            game_name="Test Game",
            players={"north": "Alice", "south": "Bob"}
        )

        # Write KFEN
        kfen_file = os.path.join(self.temp_dir, "test.kfenn")
        write_kfen(board, kfen_file, metadata)

        # Verify file exists
        self.assertTrue(os.path.exists(kfen_file))

        # Read KFEN
        document = read_kfen(kfen_file)

        # Verify metadata
        self.assertEqual(document.metadata.game_name, "Test Game")
        self.assertEqual(document.metadata.players, {"north": "Alice", "south": "Bob"})

        # Verify board info
        self.assertEqual(document.board_info.rows, 20)
        self.assertEqual(document.board_info.cols, 25)
        self.assertIsNotNone(document.board_info.fen)

    def test_write_kfen_without_metadata(self):
        """Test writing KFEN file without metadata."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        # Write KFEN without metadata
        kfen_file = os.path.join(self.temp_dir, "test_no_metadata.kfenn")
        write_kfen(board, kfen_file)

        # Read and verify
        document = read_kfen(kfen_file)
        self.assertIsNone(document.metadata.game_name)
        self.assertEqual(document.metadata.result, "ONGOING")

    def test_fen_to_kfen_conversion(self):
        """Test FEN to KFEN conversion."""
        # Create a FEN file
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        fen_string = Fen.board_to_fen(board)

        fen_file = os.path.join(self.temp_dir, "test.fen")
        with open(fen_file, 'w') as f:
            f.write(fen_string)

        # Convert to KFEN
        kfen_file = os.path.join(self.temp_dir, "test_converted.kfenn")
        convert_fen_to_kfen(fen_file, kfen_file)

        # Verify KFEN file exists and is valid
        self.assertTrue(os.path.exists(kfen_file))
        document = read_kfen(kfen_file)
        self.assertEqual(document.kfen_version, "1.0")
        self.assertIsNotNone(document.board_info.fen)

    def test_kfen_to_fen_export(self):
        """Test KFEN to FEN export."""
        # Create a board and save as KFEN
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(15, 12, 'CAVALRY', 'SOUTH')

        kfen_file = os.path.join(self.temp_dir, "test_export.kfenn")
        write_kfen(board, kfen_file)

        # Export to FEN
        fen_file = os.path.join(self.temp_dir, "test_exported.fen")
        export_kfen_to_fen(kfen_file, fen_file)

        # Verify FEN file exists and can be loaded
        self.assertTrue(os.path.exists(fen_file))
        loaded_board = Fen.fen_to_board(fen_string=open(fen_file).read())
        self.assertIsNotNone(loaded_board)

    def test_invalid_kfen_file(self):
        """Test reading invalid KFEN file."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.temp_dir, "invalid.kfenn")
        with open(invalid_file, 'w') as f:
            f.write("This is not valid JSON")

        # Should raise error
        with self.assertRaises((json.JSONDecodeError, ValueError)):
            read_kfen(invalid_file)


class TestKFENBoardIntegration(unittest.TestCase):
    """Integration tests for KFEN with Board operations."""

    def test_save_and_load_complete_game(self):
        """Test saving and loading a complete game state."""
        # Create board with some units
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(5, 12, 'CAVALRY', 'NORTH')
        board.create_and_place_unit(15, 10, 'INFANTRY', 'SOUTH')
        board.create_and_place_unit(15, 12, 'CAVALRY', 'SOUTH')

        # Enable networks
        board.enable_networks()

        # Make some moves
        board.make_turn_move(5, 10, 6, 11)
        board.make_turn_move(5, 12, 6, 13)

        # Save as KFEN
        kfen_file = os.path.join(tempfile.gettempdir(), "complete_game.kfenn")
        metadata = KFENMetadata(game_name="Integration Test")
        write_kfen(board, kfen_file, metadata)

        # Load KFEN
        document = read_kfen(kfen_file)
        loaded_board = reconstruct_board_from_history(document)

        # Verify board state
        self.assertEqual(loaded_board.turn_number, board.turn_number)
        self.assertEqual(loaded_board.turn, board.turn)
        self.assertEqual(loaded_board.current_phase, board.current_phase)

        # Clean up
        if os.path.exists(kfen_file):
            os.remove(kfen_file)


if __name__ == '__main__':
    unittest.main()
