"""Test pending retreats serialization in KFEN format."""

import tempfile
from pathlib import Path

from pykrieg.board import Board
from pykrieg.kfen import (
    KFENDocument,
    KFENGameState,
    reconstruct_board_from_history,
    write_kfen,
)


class TestPendingRetreats:
    """Test pending retreats save and load in KFEN."""

    def test_save_and_load_pending_retreats(self):
        """Test that pending retreats are saved and loaded correctly."""
        # Create a board
        board = Board()

        # Place units first (required by add_pending_retreat)
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(7, 15, 'CAVALRY', 'SOUTH')
        board.create_and_place_unit(12, 3, 'INFANTRY', 'NORTH')

        # Add pending retreats
        board.add_pending_retreat(5, 10)
        board.add_pending_retreat(7, 15)
        board.add_pending_retreat(12, 3)

        # Write to KFEN
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfen', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename)

            # Read back and reconstruct
            from pykrieg.kfen import read_kfen
            document = read_kfen(filename)
            restored_board = reconstruct_board_from_history(document)

            # Verify pending retreats were restored
            pending = list(restored_board.get_pending_retreats())
            assert len(pending) == 3, f"Expected 3 pending retreats, got {len(pending)}"
            assert (5, 10) in pending, "Pending retreat (5, 10) not found"
            assert (7, 15) in pending, "Pending retreat (7, 15) not found"
            assert (12, 3) in pending, "Pending retreat (12, 3) not found"
        finally:
            Path(filename).unlink(missing_ok=True)

    def test_empty_pending_retreats(self):
        """Test that empty pending retreats list is handled correctly."""
        # Create a board with no pending retreats
        board = Board()

        # Write to KFEN
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfen', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename)

            # Read back and verify pending_retreats is empty list
            from pykrieg.kfen import read_kfen
            document = read_kfen(filename)

            assert document.game_state.pending_retreats == [], \
                f"Expected empty pending_retreats, got {document.game_state.pending_retreats}"

            # Reconstruct board and verify no pending retreats
            restored_board = reconstruct_board_from_history(document)
            pending = list(restored_board.get_pending_retreats())
            assert len(pending) == 0, f"Expected 0 pending retreats, got {len(pending)}"
        finally:
            Path(filename).unlink(missing_ok=True)

    def test_pending_retreats_in_game_state(self):
        """Test that pending_retreats field is correctly in game_state."""
        # Create game state with pending retreats
        game_state = KFENGameState(
            turn_number=5,
            current_player="NORTH",
            current_phase="M",
            pending_retreats=[
                {"row": 1, "col": 2},
                {"row": 3, "col": 4}
            ]
        )

        assert len(game_state.pending_retreats) == 2
        assert game_state.pending_retreats[0] == {"row": 1, "col": 2}
        assert game_state.pending_retreats[1] == {"row": 3, "col": 4}

    def test_document_serialization_with_retreats(self):
        """Test full document serialization with pending retreats."""
        # Create document with pending retreats
        from pykrieg.fen import Fen
        from pykrieg.kfen import KFENBoardInfo, KFENMetadata

        board = Board()
        board.create_and_place_unit(2, 5, 'INFANTRY', 'NORTH')
        board.add_pending_retreat(2, 5)

        fen_string = Fen.board_to_fen(board, include_turn_state=False)

        document = KFENDocument(
            metadata=KFENMetadata(game_name="Test"),
            board_info=KFENBoardInfo(
                rows=20,
                cols=25,
                fen=fen_string
            ),
            game_state=KFENGameState(
                turn_number=1,
                current_player="NORTH",
                current_phase="M",
                pending_retreats=[{"row": 2, "col": 5}]
            )
        )

        # Serialize to dict
        from pykrieg.kfen import _document_to_dict
        doc_dict = _document_to_dict(document)

        # Verify pending_retreats in dict
        assert "pending_retreats" in doc_dict["game_state"]
        assert len(doc_dict["game_state"]["pending_retreats"]) == 1
        assert doc_dict["game_state"]["pending_retreats"][0] == {"row": 2, "col": 5}

    def test_roundtrip_with_retreats(self):
        """Test full roundtrip: board -> KFEN -> board with pending retreats."""
        # Create board with pending retreats
        board = Board()
        board.create_and_place_unit(3, 7, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(8, 12, 'CAVALRY', 'SOUTH')
        board.add_pending_retreat(3, 7)
        board.add_pending_retreat(8, 12)

        # Write to KFEN
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kfen', delete=False) as f:
            filename = f.name

        try:
            write_kfen(board, filename)

            # Read back
            from pykrieg.kfen import read_kfen
            document = read_kfen(filename)
            restored_board = reconstruct_board_from_history(document)

            # Verify roundtrip
            original_pending = set(board.get_pending_retreats())
            restored_pending = set(restored_board.get_pending_retreats())

            assert original_pending == restored_pending, \
                f"Pending retreats mismatch: {original_pending} != {restored_pending}"

            # Verify other game state
            assert board.turn == restored_board.turn
            assert board.turn_number == restored_board.turn_number
            assert board.current_phase == restored_board.current_phase
        finally:
            Path(filename).unlink(missing_ok=True)
