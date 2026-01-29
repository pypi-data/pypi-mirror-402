"""
Performance tests for KFEN (Krieg Forsyth-Edwards Notation) module.

This module tests that KFEN operations meet performance requirements.
"""

import os
import tempfile
import time
import unittest

from pykrieg.board import Board as BoardClass
from pykrieg.kfen import KFENMetadata, read_kfen, reconstruct_board_from_history, write_kfen


class TestKFENSerializationPerformance(unittest.TestCase):
    """Test KFEN serialization performance."""

    def test_large_game_serialization_performance(self):
        """Test serializing large game (100 turns) is fast."""
        # Create board with many units
        board = BoardClass()
        for i in range(40):
            if i < 20:
                board.create_and_place_unit(i, 10, 'INFANTRY', 'NORTH')
            else:
                board.create_and_place_unit(i-20, 12, 'INFANTRY', 'SOUTH')

        # Play many turns
        for turn_num in range(50):
            if turn_num % 2 == 0:
                # North's turn
                units = board.get_units_by_owner('NORTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass
            else:
                # South's turn
                units = board.get_units_by_owner('SOUTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        # Time serialization
        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            start = time.time()
            write_kfen(board, filename, metadata)
            elapsed = time.time() - start

            # Should complete in < 1 second
            self.assertLess(elapsed, 1.0, f"Serialization took {elapsed:.2f}s, expected < 1.0s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_medium_game_serialization_performance(self):
        """Test serializing medium game (50 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Play 50 turns
        for i in range(50):
            if i % 2 == 0:
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)  # Move back
                except Exception:
                    board.reset_turn_state()
            else:
                try:
                    board.make_turn_move(10, 10, 10, 11)
                    board.make_turn_move(10, 11, 10, 12)  # Move back
                except Exception:
                    board.reset_turn_state()

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            start = time.time()
            write_kfen(board, filename, metadata)
            elapsed = time.time() - start

            # Should complete in < 0.5 second
            self.assertLess(elapsed, 0.5, f"Serialization took {elapsed:.2f}s, expected < 0.5s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_small_game_serialization_performance(self):
        """Test serializing small game (10 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        # Play 10 turns
        for i in range(10):
            if i % 2 == 0:
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)  # Move back
                except Exception:
                    board.reset_turn_state()
            else:
                try:
                    board.make_turn_move(10, 10, 10, 11)
                    board.make_turn_move(10, 11, 10, 12)  # Move back
                except Exception:
                    board.reset_turn_state()

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            start = time.time()
            write_kfen(board, filename, metadata)
            elapsed = time.time() - start

            # Should complete in < 0.1 second
            self.assertLess(elapsed, 0.1, f"Serialization took {elapsed:.2f}s, expected < 0.1s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENDeserializationPerformance(unittest.TestCase):
    """Test KFEN deserialization performance."""

    def test_large_game_deserialization_performance(self):
        """Test deserializing large game (50 turns) is fast."""
        # Create large KFEN file
        board = BoardClass()
        for i in range(20):
            if i % 2 == 0:
                board.create_and_place_unit(i, 10, 'INFANTRY', 'NORTH')
            else:
                board.create_and_place_unit(i, 12, 'INFANTRY', 'SOUTH')

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Time deserialization
            start = time.time()
            read_kfen(filename)
            elapsed = time.time() - start

            # Should complete in < 1 second
            self.assertLess(elapsed, 1.0, f"Deserialization took {elapsed:.2f}s, expected < 1.0s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_medium_game_deserialization_performance(self):
        """Test deserializing medium game (50 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            start = time.time()
            read_kfen(filename)
            elapsed = time.time() - start

            # Should complete in < 0.5 second
            self.assertLess(elapsed, 0.5, f"Deserialization took {elapsed:.2f}s, expected < 0.5s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_small_game_deserialization_performance(self):
        """Test deserializing small game (10 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(10):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            start = time.time()
            read_kfen(filename)
            elapsed = time.time() - start

            # Should complete in < 0.1 second
            self.assertLess(elapsed, 0.1, f"Deserialization took {elapsed:.2f}s, expected < 0.1s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENReconstructionPerformance(unittest.TestCase):
    """Test board reconstruction performance."""

    def test_large_game_reconstruction_performance(self):
        """Test reconstructing large game (50 turns) is fast."""
        # Create KFEN with many turns
        board = BoardClass()
        for i in range(20):
            if i % 2 == 0:
                board.create_and_place_unit(i, 10, 'INFANTRY', 'NORTH')
            else:
                board.create_and_place_unit(i, 12, 'INFANTRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                units = board.get_units_by_owner('NORTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass
            else:
                units = board.get_units_by_owner('SOUTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Time reconstruction
            doc = read_kfen(filename)
            start = time.time()
            reconstruct_board_from_history(doc)
            elapsed = time.time() - start

            # Should complete in < 2 seconds
            self.assertLess(elapsed, 2.0, f"Reconstruction took {elapsed:.2f}s, expected < 2.0s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_medium_game_reconstruction_performance(self):
        """Test reconstructing medium game (50 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            start = time.time()
            reconstruct_board_from_history(doc)
            elapsed = time.time() - start

            # Should complete in < 1 second
            self.assertLess(elapsed, 1.0, f"Reconstruction took {elapsed:.2f}s, expected < 1.0s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_small_game_reconstruction_performance(self):
        """Test reconstructing small game (10 turns) is fast."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(10):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            doc = read_kfen(filename)
            start = time.time()
            reconstruct_board_from_history(doc)
            elapsed = time.time() - start

            # Should complete in < 0.2 second
            self.assertLess(elapsed, 0.2, f"Reconstruction took {elapsed:.2f}s, expected < 0.2s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENRoundTripPerformance(unittest.TestCase):
    """Test complete save-load round trip performance."""

    def test_large_game_round_trip_performance(self):
        """Test complete save-load round trip for large game (50 turns)."""
        board = BoardClass()
        for i in range(20):
            if i % 2 == 0:
                board.create_and_place_unit(i, 10, 'INFANTRY', 'NORTH')
            else:
                board.create_and_place_unit(i, 12, 'INFANTRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                units = board.get_units_by_owner('NORTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass
            else:
                units = board.get_units_by_owner('SOUTH')
                if units and board.can_move_more():
                    from_pos = units[0]
                    moves = board.get_legal_moves(*from_pos)
                    if moves:
                        try:
                            board.make_turn_move(from_pos[0], from_pos[1], moves[0][0], moves[0][1])
                        except Exception:
                            pass

            try:
                board.switch_to_battle_phase()
                board.pass_attack()
                board.end_turn()
            except Exception:
                board.reset_turn_state()

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            # Time complete round trip
            start = time.time()

            write_kfen(board, filename, metadata)
            doc = read_kfen(filename)
            reconstruct_board_from_history(doc)

            elapsed = time.time() - start

            # Should complete in < 3 seconds
            self.assertLess(elapsed, 3.0, f"Round trip took {elapsed:.2f}s, expected < 3.0s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_medium_game_round_trip_performance(self):
        """Test complete save-load round trip for medium game (50 turns)."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            start = time.time()

            write_kfen(board, filename, metadata)
            doc = read_kfen(filename)
            reconstruct_board_from_history(doc)

            elapsed = time.time() - start

            # Should complete in < 1.5 seconds
            self.assertLess(elapsed, 1.5, f"Round trip took {elapsed:.2f}s, expected < 1.5s")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


class TestKFENFileSize(unittest.TestCase):
    """Test that KFEN file sizes are reasonable."""

    def test_small_game_file_size(self):
        """Test that small game KFEN file size is reasonable."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(10):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Check file size
            file_size = os.path.getsize(filename)

            # Should be less than 50KB for 10 turns
            self.assertLess(file_size, 50 * 1024, f"File size {file_size} bytes, expected < 50KB")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_medium_game_file_size(self):
        """Test that medium game KFEN file size is reasonable."""
        board = BoardClass()
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(10, 10, 'CAVALRY', 'SOUTH')

        for _ in range(50):
            if board.turn == "NORTH":
                try:
                    board.make_turn_move(5, 10, 5, 11)
                    board.make_turn_move(5, 11, 5, 12)
                except Exception:
                    board.reset_turn_state()
            else:
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

        metadata = KFENMetadata(
            save_date="2026-01-17T12:00:00Z",
            created_date="2026-01-15T10:00:00Z"
        )

        filename = tempfile.mktemp(suffix='.kfenn')
        try:
            write_kfen(board, filename, metadata)

            # Check file size
            file_size = os.path.getsize(filename)

            # Should be less than 250KB for 50 turns
            self.assertLess(file_size, 250 * 1024, f"File size {file_size} bytes, expected < 250KB")
        finally:
            if os.path.exists(filename):
                os.unlink(filename)


if __name__ == '__main__':
    unittest.main()
