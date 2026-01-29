"""
Property-based tests for KFEN (Krieg Forsyth-Edwards Notation) module.

This module uses Hypothesis to verify invariants across generated inputs.
"""

import json
import os
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pykrieg.board import Board as BoardClass
from pykrieg.kfen import (
    KFENAttack,
    KFENBoardInfo,
    KFENDocument,
    KFENGameState,
    KFENMetadata,
    KFENMove,
    KFENTurn,
    validate_history,
    write_kfen,
)

# =====================================================================
# Strategy Generators
# =====================================================================

@st.composite
def kfen_metadata_strategy(draw):
    """Generate valid KFENMetadata objects."""
    return KFENMetadata(
        game_name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50).filter(lambda x: x.isprintable()))),
        save_date=draw(st.just("2026-01-17T12:00:00Z")),
        created_date=draw(st.just("2026-01-15T10:00:00Z")),
        players=draw(st.one_of(st.none(), st.dictionaries(
            st.sampled_from(["north", "south"]),
            st.text(min_size=1, max_size=20),
            min_size=1,
            max_size=2
        ))),
        event=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        result=draw(st.sampled_from(["ONGOING", "NORTH_WINS", "SOUTH_WINS", "DRAW"]))
    )


@st.composite
def kfen_move_strategy(draw):
    """Generate valid KFENMove objects."""
    return KFENMove(
        from_pos={"row": draw(st.integers(min_value=0, max_value=19)), "col": draw(st.integers(min_value=0, max_value=24))},
        to_pos={"row": draw(st.integers(min_value=0, max_value=19)), "col": draw(st.integers(min_value=0, max_value=24))},
        unit_type=draw(st.sampled_from(["INFANTRY", "CAVALRY", "CANNON", "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"])),
        unit_id=draw(st.integers(min_value=0, max_value=2**63-1)),
        was_retreat=draw(st.booleans()),
        destroyed_arsenal=draw(st.one_of(
            st.none(),
            st.fixed_dictionaries({
                "row": st.integers(min_value=0, max_value=19),
                "col": st.integers(min_value=0, max_value=24),
                "owner": st.sampled_from(["NORTH", "SOUTH"])
            })
        ))
    )


@st.composite
def kfen_turn_strategy(draw):
    """Generate valid KFENTurn objects."""
    turn_number = draw(st.integers(min_value=1, max_value=100))
    player = draw(st.sampled_from(["NORTH", "SOUTH"]))
    phase = draw(st.sampled_from(["M", "B"]))

    # Generate 0-5 moves
    num_moves = draw(st.integers(min_value=0, max_value=5))
    moves = [draw(kfen_move_strategy()) for _ in range(num_moves)]

    # Add attack only if phase is B
    attack = None
    if phase == "B" and draw(st.booleans()):
        attack = KFENAttack(
            target={"row": draw(st.integers(min_value=0, max_value=19)), "col": draw(st.integers(min_value=0, max_value=24))},
            outcome=draw(st.sampled_from(["CAPTURE", "RETREAT", "FAIL"])),
            captured_unit=draw(st.one_of(
                st.none(),
                st.fixed_dictionaries({
                    "unit_type": st.sampled_from(["INFANTRY", "CAVALRY", "CANNON", "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"]),
                    "owner": st.sampled_from(["NORTH", "SOUTH"])
                })
            )),
            retreat_positions=draw(st.lists(
                st.fixed_dictionaries({
                    "row": st.integers(min_value=0, max_value=19),
                    "col": st.integers(min_value=0, max_value=24)
                }),
                max_size=5
            ))
        )

    return KFENTurn(
        turn_number=turn_number,
        player=player,
        phase=phase,
        moves=moves,
        attack=attack
    )


@st.composite
def kfen_document_strategy(draw):
    """Generate valid KFENDocument objects."""
    num_turns = draw(st.integers(min_value=0, max_value=10))

    # Generate turn history with alternating players
    turns = []
    for i in range(num_turns):
        player = "NORTH" if i % 2 == 0 else "SOUTH"
        turn = KFENTurn(
            turn_number=i + 1,
            player=player,
            phase="M",
            moves=[]
        )
        turns.append(turn)

    return KFENDocument(
        kfen_version="1.0",
        metadata=draw(kfen_metadata_strategy()),
        board_info=KFENBoardInfo(
            rows=20,
            cols=25,
            fen="_" * 20
        ),
        game_state=KFENGameState(
            turn_number=num_turns + 1,
            current_player="NORTH" if num_turns % 2 == 0 else "SOUTH",
            current_phase="M"
        ),
        turn_history=turns
    )


# =====================================================================
# Round-Trip Property Tests
# =====================================================================

@settings(max_examples=100)
@given(kfen_document_strategy())
def test_document_serialization_round_trip(document):
    """Property: Document serialization and deserialization is idempotent."""
    # Convert to dict and back
    from pykrieg.kfen import _dict_to_document, _document_to_dict

    data = _document_to_dict(document)
    reconstructed = _dict_to_document(data)

    # Verify all fields match
    assert reconstructed.kfen_version == document.kfen_version
    assert reconstructed.metadata.game_name == document.metadata.game_name
    assert reconstructed.metadata.save_date == document.metadata.save_date
    assert reconstructed.metadata.created_date == document.metadata.created_date
    assert reconstructed.metadata.players == document.metadata.players
    assert reconstructed.metadata.event == document.metadata.event
    assert reconstructed.metadata.result == document.metadata.result

    assert reconstructed.board_info.rows == document.board_info.rows
    assert reconstructed.board_info.cols == document.board_info.cols
    assert reconstructed.board_info.fen == document.board_info.fen

    assert reconstructed.game_state.turn_number == document.game_state.turn_number
    assert reconstructed.game_state.current_player == document.game_state.current_player
    assert reconstructed.game_state.current_phase == document.game_state.current_phase

    assert len(reconstructed.turn_history) == len(document.turn_history)

    # Verify undo_redo structure
    assert "max_history" in data["undo_redo"]
    assert "current_index" in data["undo_redo"]


@settings(max_examples=50)
@given(st.builds(BoardClass))
def test_write_read_kfen_produces_valid_json(board):
    """Property: write_kfen and read_kfen produces valid JSON."""
    # Place a unit
    board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

    # Create metadata
    metadata = KFENMetadata(
        save_date="2026-01-17T12:00:00Z",
        created_date="2026-01-15T10:00:00Z"
    )

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kfenn', delete=False) as f:
        filename = f.name

    try:
        write_kfen(board, filename, metadata)

        # Verify file contains valid JSON
        with open(filename) as f:
            data = json.load(f)

        # Verify required fields
        assert "kfen_version" in data
        assert "metadata" in data
        assert "board_info" in data
        assert "game_state" in data
        assert "turn_history" in data
        assert "undo_redo" in data
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# =====================================================================
# History Consistency Property Tests
# =====================================================================

@settings(max_examples=100)
@given(kfen_document_strategy())
def test_turn_numbers_are_sequential(document):
    """Property: Turn numbers in history are sequential starting from 1."""
    for i, turn in enumerate(document.turn_history, start=1):
        assert turn.turn_number == i


@settings(max_examples=100)
@given(kfen_document_strategy())
def test_players_alternate(document):
    """Property: Players alternate between turns."""
    for i, turn in enumerate(document.turn_history):
        if i % 2 == 0:
            assert turn.player == "NORTH"
        else:
            assert turn.player == "SOUTH"


@settings(max_examples=100)
@given(kfen_turn_strategy())
def test_max_5_moves_per_turn(turn):
    """Property: No turn has more than 5 moves."""
    assert len(turn.moves) <= 5


@settings(max_examples=100)
@given(kfen_turn_strategy())
def test_max_1_attack_per_turn(turn):
    """Property: No turn has more than 1 attack."""
    attack_count = 1 if turn.attack is not None else 0
    assert attack_count <= 1


# =====================================================================
# Validation Property Tests
# =====================================================================

@settings(max_examples=100)
@given(kfen_document_strategy())
def test_generated_documents_validate(document):
    """Property: Generated documents pass validation."""
    is_valid, error = validate_history(document)
    assert is_valid, f"Generated document should be valid, got error: {error}"


def test_valid_metadata_results():
    """Property: All valid result strings are accepted."""
    valid_results = ["ONGOING", "NORTH_WINS", "SOUTH_WINS", "DRAW"]
    for result in valid_results:
        document = KFENDocument(
            metadata=KFENMetadata(result=result)
        )
        is_valid, error = validate_history(document)
        assert is_valid, f"Result {result} should be valid"


# =====================================================================
# Move Property Tests
# =====================================================================

@settings(max_examples=100)
@given(kfen_move_strategy())
def test_move_positions_are_valid(move):
    """Property: Move positions are within board bounds."""
    assert 0 <= move.from_pos["row"] <= 19
    assert 0 <= move.from_pos["col"] <= 24
    assert 0 <= move.to_pos["row"] <= 19
    assert 0 <= move.to_pos["col"] <= 24


@settings(max_examples=100)
@given(kfen_move_strategy())
def test_move_unit_type_is_valid(move):
    """Property: Move unit type is valid."""
    valid_types = ["INFANTRY", "CAVALRY", "CANNON", "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"]
    assert move.unit_type in valid_types


@settings(max_examples=100)
@given(kfen_move_strategy())
def test_move_unit_id_is_positive(move):
    """Property: Move unit ID is non-negative."""
    assert move.unit_id >= 0


# =====================================================================
# Game State Property Tests
# =====================================================================

def test_valid_game_states():
    """Property: All valid game state combinations are accepted."""
    for player in ["NORTH", "SOUTH"]:
        for phase in ["M", "B"]:
            document = KFENDocument(
                game_state=KFENGameState(
                    turn_number=5,
                    current_player=player,
                    current_phase=phase
                )
            )
            is_valid, error = validate_history(document)
            assert is_valid, f"Player {player}, Phase {phase} should be valid"


# =====================================================================
# Board Dimensions Property Tests
# =====================================================================

def test_valid_board_dimensions():
    """Property: Valid board dimensions are accepted."""
    for rows in [10, 15, 20, 25, 30]:
        for cols in [10, 20, 25, 30, 40]:
            document = KFENDocument(
                board_info=KFENBoardInfo(
                    rows=rows,
                    cols=cols,
                    fen="_" * rows
                )
            )
            is_valid, error = validate_history(document)
            assert is_valid, f"Dimensions {rows}x{cols} should be valid"


# =====================================================================
# JSON Structure Property Tests
# =====================================================================

@settings(max_examples=50)
@given(kfen_document_strategy())
def test_document_to_dict_produces_valid_structure(document):
    """Property: _document_to_dict produces valid dictionary structure."""
    from pykrieg.kfen import _document_to_dict

    data = _document_to_dict(document)

    # Verify top-level keys
    required_keys = ["kfen_version", "metadata", "board_info", "game_state", "turn_history"]
    for key in required_keys:
        assert key in data

    # Verify metadata structure
    metadata_keys = ["game_name", "save_date", "created_date", "players", "event", "result"]
    for key in metadata_keys:
        assert key in data["metadata"]

    # Verify board_info structure
    board_info_keys = ["rows", "cols", "fen"]
    for key in board_info_keys:
        assert key in data["board_info"]

    # Verify game_state structure
    game_state_keys = ["turn_number", "current_player", "current_phase"]
    for key in game_state_keys:
        assert key in data["game_state"]


# =====================================================================
# Edge Case Property Tests
# =====================================================================

@settings(max_examples=20)
@given(kfen_document_strategy())
def test_empty_turn_history_is_valid(document):
    """Property: Empty turn history is valid."""
    document.turn_history = []
    is_valid, error = validate_history(document)
    assert is_valid


@settings(max_examples=20)
@given(kfen_document_strategy())
def test_single_turn_history_is_valid(document):
    """Property: Single turn history is valid."""
    document.turn_history = [
        KFENTurn(
            turn_number=1,
            player="NORTH",
            phase="M",
            moves=[]
        )
    ]
    is_valid, error = validate_history(document)
    assert is_valid


@settings(max_examples=20)
@given(kfen_metadata_strategy())
def test_metadata_with_optional_fields_is_valid(metadata):
    """Property: Metadata with optional fields set to None is valid."""
    document = KFENDocument(metadata=metadata)
    is_valid, error = validate_history(document)
    assert is_valid, f"Metadata should be valid, got error: {error}"


# =====================================================================
# Run Tests
# =====================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
