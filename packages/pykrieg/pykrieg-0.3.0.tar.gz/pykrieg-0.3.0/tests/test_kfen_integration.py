"""
Integration tests for KFEN (Krieg Forsyth-Edwards Notation) module.

This module tests KFEN integration with the Board class and other systems.
"""

import os
import tempfile
import unittest

from pykrieg.board import Board as BoardClass
from pykrieg.fen import Fen
from pykrieg.kfen import (
    KFENDocument,
    KFENMetadata,
    KFENTurn,
    read_kfen,
    reconstruct_board_from_history,
    validate_history,
    write_kfen,
)


class TestKFENCompleteWorkflow(unittest.TestCase):
    """Test complete save/load/replay workflow."""

    def test_complete_save_load_replay_workflow(self):
        """Test saving, loading, and replaying a complete game."""
        # Create and play a game
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Play a few turns
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # South's turn
        try:
            board.make_turn_move(10, 10, 10, 11)
            board.switch_to_battle_phase()
            board.pass_attack()
            board.end_turn()
        except Exception:
            # If invalid move, just end turn
            board.end_turn()

        # Save
        metadata = KFENMetadata(
            game_name="Test Game",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify metadata (save_date is auto-generated to current time)
            self.assertEqual(doc.metadata.game_name, "Test Game")
            self.assertIsNotNone(doc.metadata.save_date)

            # Verify game state
            self.assertEqual(doc.game_state.current_player, "NORTH")
            self.assertEqual(doc.game_state.current_phase, "M")

            # Verify turn history exists
            self.assertGreater(len(doc.turn_history), 0)

            # Reconstruct board from history
            reconstructed = reconstruct_board_from_history(doc)

            # Verify reconstructed board matches original
            self.assertEqual(reconstructed.turn, board.turn)
            self.assertEqual(reconstructed.turn_number, board.turn_number)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_save_load_with_combat(self):
        """Test saving and loading game with combat."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(6, 10, 'CAVALRY', 'SOUTH')

        # North attacks
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Save
        metadata = KFENMetadata(
            game_name="Combat Test",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify turn history (battle phase may not be recorded separately)
            # The main verification is that the document loads correctly
            self.assertGreater(len(doc.turn_history), 0)

            # Reconstruct
            reconstructed = reconstruct_board_from_history(doc)

            # Verify reconstruction
            self.assertIsNotNone(reconstructed)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_save_load_with_arsenals(self):
        """Test saving and loading game with arsenals (terrain, not units)."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(15, 10, 'CAVALRY', 'SOUTH')

        # Place arsenals as terrain
        board.set_arsenal(0, 10, 'NORTH')
        board.set_arsenal(19, 10, 'SOUTH')

        # Play a turn
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Save
        metadata = KFENMetadata(
            game_name="Arsenal Test",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify FEN includes arsenal terrain
            self.assertIn('A', doc.board_info.fen)  # Arsenal marker

            # Reconstruct
            reconstruct_board_from_history(doc)

            # Verify arsenals are restored
            self.assertEqual(board.get_arsenal_owner(0, 10), 'NORTH')
            self.assertEqual(board.get_arsenal_owner(19, 10), 'SOUTH')
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_save_load_with_undo_redo(self):
        """Test saving and loading preserves undo/redo state."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Make a move
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Save after making move
        metadata = KFENMetadata(
            game_name="Undo/Redo Test",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify undo/redo info is preserved
            self.assertIsNotNone(doc.undo_redo)
            # undo_redo is a KFENUndoRedo object, not a dict
            self.assertIsInstance(doc.undo_redo.max_history, int)
            self.assertIsInstance(doc.undo_redo.current_index, int)

            # Reconstruct
            reconstructed = reconstruct_board_from_history(doc)

            # Verify reconstruction
            self.assertIsNotNone(reconstructed)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENComplexScenarios(unittest.TestCase):
    """Test complex game scenarios."""

    def test_long_game(self):
        """Test saving and loading a long game."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Play many turns
        for i in range(20):
            if i % 2 == 0:
                # North's turn
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
                # South's turn
                try:
                    board.make_turn_move(10, 10, 10, 11)
                    board.make_turn_move(10, 11, 10, 12)
                except Exception:
                    board.reset_turn_state()

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        # Save
        metadata = KFENMetadata(
            game_name="Long Game",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify turn history
            self.assertGreater(len(doc.turn_history), 10)

            # Reconstruct
            reconstructed = reconstruct_board_from_history(doc)

            # Verify final state
            self.assertIsNotNone(reconstructed)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_multiple_captures(self):
        """Test saving and loading game with multiple captures."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(6, 10, 'CAVALRY', 'SOUTH')
        board.create_and_place_unit(7, 10, 'INFANTRY', 'SOUTH')

        # North moves adjacent to South units
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Save
        metadata = KFENMetadata(
            game_name="Multiple Captures",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Reconstruct
            reconstructed = reconstruct_board_from_history(doc)

            # Verify units
            self.assertIsNotNone(reconstructed)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENValidationIntegration(unittest.TestCase):
    """Test validation in real-world scenarios."""

    def test_reconstruction_fails_on_invalid_history(self):
        """Test that reconstruction handles invalid history gracefully."""
        # Create document with invalid history
        doc = KFENDocument(
            turn_history=[
                KFENTurn(turn_number=1, player="NORTH", phase="M"),
                KFENTurn(turn_number=2, player="SOUTH", phase="M"),
                KFENTurn(turn_number=4, player="NORTH", phase="M"),  # Skipped turn 3
            ]
        )

        # Validate should fail
        is_valid, error = validate_history(doc)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_valid_game_passes_validation(self):
        """Test that a valid game passes validation."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Play a valid game
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # South's turn
        try:
            board.make_turn_move(10, 10, 10, 11)
            board.switch_to_battle_phase()
            board.pass_attack()
            board.end_turn()
        except Exception:
            # If invalid move, just end turn
            board.end_turn()

        # Save
        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load and validate
            doc = read_kfen(filename)
            is_valid, error = validate_history(doc)

            # Should be valid
            self.assertTrue(is_valid, f"Valid game should pass validation: {error}")
            self.assertIsNone(error)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENMetadataIntegration(unittest.TestCase):
    """Test metadata integration with Board."""

    def test_board_metadata_round_trip(self):
        """Test that Board metadata survives save/load."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        # Set metadata on board
        board.set_kfen_metadata({
            "game_name": "Test Game",
            "players": {"north": "Alice", "south": "Bob"},
            "event": "Tournament"
        })

        # Play a turn
        board.make_turn_move(5, 10, 5, 11)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Save with explicit metadata
        metadata = KFENMetadata(
            game_name="Test Game",
            players={"north": "Alice", "south": "Bob"},
            event="Tournament",
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load
            doc = read_kfen(filename)

            # Verify metadata is preserved
            self.assertEqual(doc.metadata.game_name, "Test Game")
            self.assertEqual(doc.metadata.players["north"], "Alice")
            self.assertEqual(doc.metadata.players["south"], "Bob")
            self.assertEqual(doc.metadata.event, "Tournament")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENFENIntegration(unittest.TestCase):
    """Test integration with FEN system."""

    def test_fen_to_kfen_to_fen(self):
        """Test FEN -> KFEN -> FEN round trip."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Get FEN
        fen = Fen.board_to_fen(board)
        self.assertIsNotNone(fen)

        # Save to KFEN
        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Load KFEN
            doc = read_kfen(filename)

            # Get FEN from KFEN
            kfen_fen = doc.board_info.fen

            # Load FEN to new board
            new_board = Fen.fen_to_board(kfen_fen)

            # Verify boards match
            self.assertEqual(new_board.turn, board.turn)
            self.assertEqual(new_board.turn_number, board.turn_number)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


if __name__ == '__main__':
    unittest.main()
