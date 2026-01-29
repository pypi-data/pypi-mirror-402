"""
Edge case tests for KFEN (Krieg Forsyth-Edwards Notation) module.

This module tests boundary conditions, special cases, and error scenarios.
"""

import json
import os
import tempfile
import unittest

from pykrieg.board import Board as BoardClass
from pykrieg.kfen import (
    KFENAttack,
    KFENDocument,
    KFENMetadata,
    KFENMove,
    KFENTurn,
    read_kfen,
    validate_history,
    write_kfen,
)


class TestKFENEmptyCases(unittest.TestCase):
    """Test empty or minimal KFEN documents."""

    def test_empty_turn_history(self):
        """Test saving game with no turn history."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(len(doc.turn_history), 0)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_single_turn_history(self):
        """Test saving game with single turn."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.make_turn_move(5, 10, 5, 11)
        board.end_turn()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            # Should have 2 turns (initial boundary + end_turn creates 2 entries)
            self.assertGreaterEqual(len(doc.turn_history), 1)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_board_with_no_units(self):
        """Test saving board with no units."""
        board = BoardClass()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertIsNotNone(doc.board_info.fen)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENCorruption(unittest.TestCase):
    """Test handling of corrupted or invalid data."""

    def test_malformed_json(self):
        """Test reading malformed KFEN file."""
        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            with open(filename, 'w') as f:
                f.write("{invalid json")

            with self.assertRaises((json.JSONDecodeError, ValueError)):
                read_kfen(filename)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_partial_file_read(self):
        """Test handling of partially written KFEN file."""
        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            # Write partial KFEN (missing closing brace)
            with open(filename, 'w') as f:
                f.write('{"kfen_version": "1.0", "metadata": {"save_date": "2026-01-17T12:00:00Z"')

            with self.assertRaises((json.JSONDecodeError, ValueError)):
                read_kfen(filename)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_missing_required_fields(self):
        """Test reading KFEN missing required fields."""
        kfen_data = {
            "metadata": {
                "save_date": "2026-01-17T12:00:00Z",
                "created_date": "2026-01-15T10:00:00Z"
            },
            # Missing required fields: kfen_version, board_info, game_state
        }

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            with open(filename, 'w') as f:
                json.dump(kfen_data, f)

            # Should handle missing required fields
            with self.assertRaises((KeyError, ValueError)):
                read_kfen(filename)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENSpecialCharacters(unittest.TestCase):
    """Test handling of special characters in metadata."""

    def test_special_characters_in_metadata(self):
        """Test metadata with special characters."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        metadata = KFENMetadata(
            game_name='Test "Game" with \'quotes\' & symbols',
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z",
            players={
                "north": "Alice <player1@example.com>",
                "south": "Bob & Friends"
            },
            event='Tournament "Spring 2026"'
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(doc.metadata.game_name, 'Test "Game" with \'quotes\' & symbols')
            self.assertEqual(doc.metadata.players["north"], "Alice <player1@example.com>")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_unicode_in_metadata(self):
        """Test handling of unicode characters in metadata."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        metadata = KFENMetadata(
            game_name="游戏名称 🎮",
            players={
                "north": "Игрок А",
                "south": "プレイヤー B"
            },
            event="Torneio 2026 🏆",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(doc.metadata.game_name, "游戏名称 🎮")
            self.assertEqual(doc.metadata.players["north"], "Игрок А")
            self.assertEqual(doc.metadata.event, "Torneio 2026 🏆")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_long_metadata_strings(self):
        """Test handling of very long metadata strings."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        # Very long game name
        long_name = "A" * 10000

        metadata = KFENMetadata(
            game_name=long_name,
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(len(doc.metadata.game_name), 10000)
            self.assertEqual(doc.metadata.game_name, long_name)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENOptionalFields(unittest.TestCase):
    """Test handling of optional metadata fields."""

    def test_missing_optional_metadata_fields(self):
        """Test handling of missing optional metadata fields."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        # Only required fields
        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)

            # Verify missing fields are None
            self.assertIsNone(doc.metadata.game_name)
            self.assertIsNone(doc.metadata.players)
            self.assertIsNone(doc.metadata.event)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENInvalidInputs(unittest.TestCase):
    """Test handling of invalid inputs."""

    def test_invalid_turn_sequence(self):
        """Test validation detects invalid turn sequence (turn_number < 1)."""
        from pykrieg.kfen import KFENGameState
        doc = KFENDocument(
            game_state=KFENGameState(turn_number=3, current_player="SOUTH"),
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="M"),
                KFENTurn(turn_number=0, player="SOUTH", phase="M"),  # Invalid: turn 0
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIn("must be >= 1", error)

    def test_player_alternation_violation(self):
        """Test validation detects player alternation violation."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="M"),
                KFENTurn(turn_number=2, player="NORTH", phase="M"),  # Same player twice
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIn("player", error.lower())

    def test_invalid_player_string(self):
        """Test validation detects invalid player string."""
        from pykrieg.kfen import KFENGameState
        doc = KFENDocument(
            game_state=KFENGameState(turn_number=1, current_player="INVALID"),
            turn_history=[
                KFENTurn(turn_number=1, player="INVALID", phase="M"),
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIn("invalid player", error.lower())

    def test_invalid_phase_string(self):
        """Test validation detects invalid phase string."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="X"),  # Invalid phase
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIn("invalid phase", error.lower())

    def test_invalid_result_string(self):
        """Test validation detects invalid result string."""
        doc = KFENDocument(
            metadata=KFENMetadata(result="INVALID_RESULT")
        )

        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIn("invalid metadata result", error.lower())


class TestKFENBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and edge values."""

    def test_max_moves_per_turn(self):
        """Test turn with exactly 5 moves (maximum)."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M",
                    moves=[
                        KFENMove(
                            from_pos={"row": 5 + i, "col": 10 + i},
                            to_pos={"row": 6 + i, "col": 11 + i},
                            unit_type="INFANTRY",
                            unit_id=100 + i,
                            was_retreat=False
                        )
                        for i in range(5)  # Exactly 5 moves
                    ]
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_min_moves_per_turn(self):
        """Test turn with 0 moves (minimum)."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M",
                    moves=[]  # 0 moves
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_all_valid_results(self):
        """Test all valid result values."""
        valid_results = ["ONGOING", "NORTH_WINS", "SOUTH_WINS", "DRAW"]

        for result in valid_results:
            doc = KFENDocument(
                metadata=KFENMetadata(result=result)
            )

            is_valid, error = validate_history(doc)
            self.assertTrue(is_valid, f"Result {result} should be valid")
            self.assertIsNone(error)


class TestKFENPhaseSpecific(unittest.TestCase):
    """Test phase-specific edge cases."""

    def test_save_mid_movement_phase(self):
        """Test saving during movement phase."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.make_turn_move(5, 10, 5, 11)
        # Don't switch phase - save during movement

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(doc.game_state.current_phase, "M")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_save_mid_battle_phase(self):
        """Test saving during battle phase."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'INFANTRY', 'SOUTH')

        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        # Don't attack - save during battle

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            self.assertEqual(doc.game_state.current_phase, "B")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENRetreatEdgeCases(unittest.TestCase):
    """Test retreat-related edge cases."""

    def test_move_marked_as_retreat(self):
        """Test move marked as retreat."""
        doc = KFENDocument(
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
                            was_retreat=True  # Marked as retreat
                        )
                    ]
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)
        self.assertEqual(doc.turn_history[0].moves[0].was_retreat, True)

    def test_multiple_retreats_in_turn(self):
        """Test multiple retreats in one turn."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M",
                    moves=[
                        KFENMove(
                            from_pos={"row": 5 + i, "col": 10},
                            to_pos={"row": 6 + i, "col": 11},
                            unit_type="INFANTRY",
                            unit_id=100 + i,
                            was_retreat=True
                        )
                        for i in range(3)
                    ]
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)

        # Verify all are marked as retreats
        self.assertTrue(all(move.was_retreat for move in doc.turn_history[0].moves))


class TestKFENAttackEdgeCases(unittest.TestCase):
    """Test attack-related edge cases."""

    def test_attack_with_no_retreat_positions(self):
        """Test attack with empty retreat positions."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="B",
                    attack=KFENAttack(
                        target={"row": 8, "col": 12},
                        outcome="CAPTURE",
                        captured_unit={"unit_type": "CAVALRY", "owner": "SOUTH"},
                        retreat_positions=[]  # No retreat positions
                    )
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)

    def test_attack_with_multiple_retreat_positions(self):
        """Test attack with multiple retreat positions."""
        doc = KFENDocument(
            turn_history=[
                KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="B",
                    attack=KFENAttack(
                        target={"row": 8, "col": 12},
                        outcome="RETREAT",
                        retreat_positions=[
                            {"row": 8, "col": 11},
                            {"row": 8, "col": 10},
                            {"row": 7, "col": 12}
                        ]
                    )
                )
            ]
        )

        is_valid, error = validate_history(doc)
        self.assertTrue(is_valid)
        self.assertEqual(len(doc.turn_history[0].attack.retreat_positions), 3)


if __name__ == '__main__':
    unittest.main()
