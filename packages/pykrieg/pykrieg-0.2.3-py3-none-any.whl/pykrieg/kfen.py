"""
KFEN (Krieg Forsyth-Edwards Notation) for Pykrieg game records.

This module implements KFEN, a JSON-based format for complete game records
including board state, turn history, metadata, and replay capabilities.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .board import Board

# =====================================================================
# KFEN Data Structures
# =====================================================================

def _default_timestamp() -> str:
    """Generate default timestamp for KFEN metadata."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


@dataclass
class KFENMetadata:
    """Metadata for a KFEN game record."""
    game_name: Optional[str] = None
    save_date: str = field(default_factory=_default_timestamp)
    created_date: str = field(default_factory=_default_timestamp)
    players: Optional[Dict[str, str]] = None
    event: Optional[str] = None
    result: str = "ONGOING"  # ONGOING, NORTH_WINS, SOUTH_WINS, DRAW


@dataclass
class KFENBoardInfo:
    """Board information for KFEN."""
    rows: int = 20
    cols: int = 25
    fen: str = ""  # FEN string representation


@dataclass
class KFENGameState:
    """Current game state for KFEN."""
    turn_number: int = 1
    current_player: str = "NORTH"
    current_phase: str = "M"  # M for Movement, B for Battle
    pending_retreats: List[Dict[str, int]] = field(default_factory=list)
    # Format: [{"row": 1, "col": 5}, {"row": 2, "col": 10}, ...]


@dataclass
class KFENMove:
    """Represents a single move in KFEN."""
    from_pos: Dict[str, int]  # {"row": int, "col": int}
    to_pos: Dict[str, int]  # {"row": int, "col": int}
    unit_type: str
    unit_id: int
    was_retreat: bool
    destroyed_arsenal: Optional[Dict[str, Any]] = None  # {"row": int, "col": int, "owner": str}


@dataclass
class KFENPhaseChange:
    """Represents a phase change in KFEN."""
    from_phase: str
    to_phase: str
    moves_made: int


@dataclass
class KFENAttack:
    """Represents an attack in KFEN."""
    target: Dict[str, int]  # {"row": int, "col": int}
    outcome: str  # CAPTURE, RETREAT, FAIL
    captured_unit: Optional[Dict[str, str]] = None  # {"unit_type": str, "owner": str}
    retreat_positions: List[Dict[str, int]] = field(default_factory=list)


@dataclass
class KFENTurnEnd:
    """Represents end of turn information in KFEN."""
    captured_units: List[Dict[str, Any]] = field(default_factory=list)
    # Each captured unit: {"row", "col", "unit": {"unit_type", "owner"}, "reason"}


@dataclass
class KFENTurn:
    """Represents a complete turn in KFEN."""
    turn_number: int
    player: str  # NORTH or SOUTH
    phase: str  # M or B
    moves: List[KFENMove] = field(default_factory=list)
    phase_change: Optional[KFENPhaseChange] = None
    attack: Optional[KFENAttack] = None
    end_turn: Optional[KFENTurnEnd] = None


@dataclass
class KFENUndoRedo:
    """Undo/redo state for KFEN."""
    max_history: int = 100
    current_index: int = 0


@dataclass
class KFENDocument:
    """Complete KFEN document."""
    kfen_version: str = "1.0"
    metadata: KFENMetadata = field(default_factory=KFENMetadata)
    board_info: KFENBoardInfo = field(default_factory=KFENBoardInfo)
    game_state: KFENGameState = field(default_factory=KFENGameState)
    turn_history: List[KFENTurn] = field(default_factory=list)
    undo_redo: KFENUndoRedo = field(default_factory=KFENUndoRedo)


# =====================================================================
# KFEN Serialization (Writer)
# =====================================================================

def write_kfen(board: 'Board', filename: str, metadata: Optional[KFENMetadata] = None) -> None:
    """
    Write board state and turn history to KFEN file.

    Args:
        board: The Board object to serialize
        filename: Path to output KFEN file
        metadata: Optional metadata for the game record

    Example:
        >>> board = Board()
        >>> # ... play game ...
        >>> metadata = KFENMetadata(game_name="Tournament Final")
        >>> write_kfen(board, "game_123.kfen", metadata)
    """
    from . import fen

    # Use provided metadata or create default
    if metadata is None:
        metadata = KFENMetadata()
    else:
        # Update save_date to current time
        metadata.save_date = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Set result from board state
    if board.is_game_over():
        metadata.result = board.game_state
    else:
        metadata.result = "ONGOING"

    # Extract board info (without redundant turn state - that's in game_state)
    # FEN is written as a single line (JSON doesn't allow raw newlines in strings)
    fen_string = fen.Fen.board_to_fen(board, include_turn_state=False)

    board_info = KFENBoardInfo(
        rows=board.rows,
        cols=board.cols,
        fen=fen_string
    )

    # Extract game state
    pending_retreats_list = []
    for row, col in board.get_pending_retreats():
        pending_retreats_list.append({"row": row, "col": col})

    game_state = KFENGameState(
        turn_number=board.turn_number,
        current_player=board.turn,
        current_phase=board.current_phase,
        pending_retreats=pending_retreats_list
    )

    # Extract turn history from undo/redo manager
    turn_history = _extract_turn_history(board)

    # Extract undo/redo state
    undo_redo_info = KFENUndoRedo(
        max_history=board.undo_redo_manager.max_history,
        current_index=len(board.undo_redo_manager.undo_stack)
    )

    # Create document
    document = KFENDocument(
        kfen_version="1.0",
        metadata=metadata,
        board_info=board_info,
        game_state=game_state,
        turn_history=turn_history,
        undo_redo=undo_redo_info
    )

    # Serialize to JSON with pretty formatting
    json_data = _document_to_dict(document)

    # Note: FEN string is written as a single line (JSON doesn't allow
    # raw newlines in strings). For readability, users can use
    # a JSON pretty-printer, but the FEN itself must be one line.

    # Write to file
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=2)


def _extract_turn_history(board: 'Board') -> List[KFENTurn]:
    """
    Extract turn history from board's undo/redo manager.

    Args:
        board: The Board object

    Returns:
        List of KFENTurn objects representing complete turn history
    """
    from .undo_redo import AttackAction, MoveAction, TurnBoundary

    history = board.undo_redo_manager.action_history
    turns: List[KFENTurn] = []
    current_turn: Optional[KFENTurn] = None
    turn_number = 1
    player = "NORTH"
    phase = "M"

    for action in history:
        if isinstance(action, TurnBoundary):
            # This marks the end of a turn
            if current_turn is not None:
                # Add turn boundary info
                current_turn.end_turn = KFENTurnEnd(
                    captured_units=[]  # TODO: Extract captured units from turn boundary
                )
                turns.append(current_turn)

            # Start new turn
            turn_number = action.to_turn[1]
            player = action.to_turn[0]
            phase = "M"  # Always start with movement phase
            current_turn = KFENTurn(
                turn_number=turn_number,
                player=player,
                phase=phase
            )

        elif isinstance(action, MoveAction):
            if current_turn is None:
                # Create initial turn if we haven't seen a TurnBoundary yet
                current_turn = KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M"
                )

            move = KFENMove(
                from_pos={"row": action.from_pos[0], "col": action.from_pos[1]},
                to_pos={"row": action.to_pos[0], "col": action.to_pos[1]},
                unit_type=action.unit_type,
                unit_id=action.unit_id,
                was_retreat=action.was_retreat,
                destroyed_arsenal=(
                    {"row": action.destroyed_arsenal[0],
                     "col": action.destroyed_arsenal[1],
                     "owner": action.destroyed_arsenal[2]}
                    if action.destroyed_arsenal else None
                )
            )
            current_turn.moves.append(move)

        elif isinstance(action, AttackAction):
            if current_turn is None:
                # Create initial turn if we haven't seen a TurnBoundary yet
                current_turn = KFENTurn(
                    turn_number=1,
                    player="NORTH",
                    phase="M"
                )

            retreat_pos = [{"row": pos[0], "col": pos[1]} for pos in action.retreat_positions]
            attack = KFENAttack(
                target={"row": action.target_pos[0], "col": action.target_pos[1]},
                outcome=action.outcome,
                captured_unit=action.captured_unit,
                retreat_positions=retreat_pos
            )
            current_turn.attack = attack

    # Add the last turn if it doesn't end with a TurnBoundary
    if current_turn is not None and (not turns or turns[-1] != current_turn):
        turns.append(current_turn)

    return turns


def _document_to_dict(document: KFENDocument) -> Dict[str, Any]:
    """
    Convert KFENDocument to dictionary for JSON serialization.

    Args:
        document: KFENDocument to convert

    Returns:
        Dictionary representation
    """
    result: Dict[str, Any] = {
        "kfen_version": document.kfen_version,
        "metadata": {
            "game_name": document.metadata.game_name,
            "save_date": document.metadata.save_date,
            "created_date": document.metadata.created_date,
            "players": document.metadata.players,
            "event": document.metadata.event,
            "result": document.metadata.result
        },
        "board_info": {
            "rows": document.board_info.rows,
            "cols": document.board_info.cols,
            "fen": document.board_info.fen
        },
        "game_state": {
            "turn_number": document.game_state.turn_number,
            "current_player": document.game_state.current_player,
            "current_phase": document.game_state.current_phase,
            "pending_retreats": document.game_state.pending_retreats
        },
        "turn_history": [],
        "undo_redo": {
            "max_history": document.undo_redo.max_history,
            "current_index": document.undo_redo.current_index
        }
    }

    # Convert turn history
    for turn in document.turn_history:
        turn_dict: Dict[str, Any] = {
            "turn_number": turn.turn_number,
            "player": turn.player,
            "phase": turn.phase,
            "moves": [],
            "phase_change": None,
            "attack": None,
            "end_turn": None
        }

        # Convert moves
        for move in turn.moves:
            move_dict = {
                "from": move.from_pos,
                "to": move.to_pos,
                "unit_type": move.unit_type,
                "unit_id": move.unit_id,
                "was_retreat": move.was_retreat,
                "destroyed_arsenal": move.destroyed_arsenal
            }
            turn_dict["moves"].append(move_dict)

        # Convert phase change
        if turn.phase_change:
            turn_dict["phase_change"] = {
                "from": turn.phase_change.from_phase,
                "to": turn.phase_change.to_phase,
                "moves_made": turn.phase_change.moves_made
            }

        # Convert attack
        if turn.attack:
            turn_dict["attack"] = {
                "target": turn.attack.target,
                "outcome": turn.attack.outcome,
                "captured_unit": turn.attack.captured_unit,
                "retreat_positions": turn.attack.retreat_positions
            }

        # Convert end turn
        if turn.end_turn:
            turn_dict["end_turn"] = {
                "captured_units": turn.end_turn.captured_units
            }

        result["turn_history"].append(turn_dict)

    return result


# =====================================================================
# KFEN Deserialization (Reader)
# =====================================================================

def read_kfen(filename: str) -> KFENDocument:
    """
    Read KFEN file and return KFENDocument.

    Args:
        filename: Path to KFEN file

    Returns:
        KFENDocument object

    Raises:
        ValueError: If file format is invalid
        IOError: If file cannot be read
    """
    with open(filename) as f:
        json_data = json.load(f)

    return _dict_to_document(json_data)


def _dict_to_document(data: Dict[str, Any]) -> KFENDocument:
    """
    Convert dictionary to KFENDocument.

    Args:
        data: Dictionary representation of KFEN

    Returns:
        KFENDocument object

    Raises:
        ValueError: If data structure is invalid
    """
    # Validate required fields
    if "kfen_version" not in data:
        raise ValueError("Missing required field: kfen_version")

    # Parse metadata
    metadata_dict = data.get("metadata", {})
    metadata = KFENMetadata(
        game_name=metadata_dict.get("game_name"),
        save_date=metadata_dict.get("save_date", ""),
        created_date=metadata_dict.get("created_date", ""),
        players=metadata_dict.get("players"),
        event=metadata_dict.get("event"),
        result=metadata_dict.get("result", "ONGOING")
    )

    # Parse board info
    board_info_dict = data.get("board_info", {})
    board_info = KFENBoardInfo(
        rows=board_info_dict.get("rows", 20),
        cols=board_info_dict.get("cols", 25),
        fen=board_info_dict.get("fen", "")
    )

    # Parse game state
    game_state_dict = data.get("game_state", {})
    game_state = KFENGameState(
        turn_number=game_state_dict.get("turn_number", 1),
        current_player=game_state_dict.get("current_player", "NORTH"),
        current_phase=game_state_dict.get("current_phase", "M"),
        pending_retreats=game_state_dict.get("pending_retreats", [])
    )

    # Parse turn history
    turn_history_list = data.get("turn_history", [])
    turn_history = []
    for turn_dict in turn_history_list:
        turn = KFENTurn(
            turn_number=turn_dict.get("turn_number", 1),
            player=turn_dict.get("player", "NORTH"),
            phase=turn_dict.get("phase", "M")
        )

        # Parse moves
        moves_list = turn_dict.get("moves", [])
        for move_dict in moves_list:
            move = KFENMove(
                from_pos=move_dict.get("from", {}),
                to_pos=move_dict.get("to", {}),
                unit_type=move_dict.get("unit_type", ""),
                unit_id=move_dict.get("unit_id", 0),
                was_retreat=move_dict.get("was_retreat", False),
                destroyed_arsenal=move_dict.get("destroyed_arsenal")
            )
            turn.moves.append(move)

        # Parse phase change
        phase_change_dict = turn_dict.get("phase_change")
        if phase_change_dict:
            turn.phase_change = KFENPhaseChange(
                from_phase=phase_change_dict.get("from", "M"),
                to_phase=phase_change_dict.get("to", "B"),
                moves_made=phase_change_dict.get("moves_made", 0)
            )

        # Parse attack
        attack_dict = turn_dict.get("attack")
        if attack_dict:
            turn.attack = KFENAttack(
                target=attack_dict.get("target", {}),
                outcome=attack_dict.get("outcome", ""),
                captured_unit=attack_dict.get("captured_unit"),
                retreat_positions=attack_dict.get("retreat_positions", [])
            )

        # Parse end turn
        end_turn_dict = turn_dict.get("end_turn")
        if end_turn_dict:
            turn.end_turn = KFENTurnEnd(
                captured_units=end_turn_dict.get("captured_units", [])
            )

        turn_history.append(turn)

    # Parse undo/redo
    undo_redo_dict = data.get("undo_redo", {})
    undo_redo = KFENUndoRedo(
        max_history=undo_redo_dict.get("max_history", 100),
        current_index=undo_redo_dict.get("current_index", 0)
    )

    return KFENDocument(
        kfen_version=data["kfen_version"],
        metadata=metadata,
        board_info=board_info,
        game_state=game_state,
        turn_history=turn_history,
        undo_redo=undo_redo
    )


# =====================================================================
# KFEN Validation
# =====================================================================

def validate_history(document: KFENDocument) -> Tuple[bool, Optional[str]]:
    """
    Validate turn history in KFEN document.

    Args:
        document: KFENDocument to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if history is valid, False otherwise
        - error_message: Error description if invalid, None if valid
    """
    # Check version compatibility
    if document.kfen_version not in ["1.0"]:
        return False, f"Unsupported KFEN version: {document.kfen_version}"

    # Validate board dimensions
    if document.board_info.rows <= 0 or document.board_info.cols <= 0:
        return False, "Invalid board dimensions"

    # Validate turn sequence
    expected_turn = 1
    expected_player = "NORTH"

    for i, turn in enumerate(document.turn_history):
        # Check turn number
        if turn.turn_number != expected_turn:
            return False, f"Turn {i}: expected turn number {expected_turn}, got {turn.turn_number}"

        # Check player alternation
        if turn.player != expected_player:
            return False, f"Turn {i}: expected player {expected_player}, got {turn.player}"

        # Check move count (max 5)
        if len(turn.moves) > 5:
            return False, f"Turn {i}: too many moves ({len(turn.moves)}, max 5)"

        # Check attack count (0 or 1)
        if turn.attack is not None and len(turn.moves) > 5:
            return False, f"Turn {i}: cannot have attack after 5 moves"

        # Validate player string
        if turn.player not in ["NORTH", "SOUTH"]:
            return False, f"Turn {i}: invalid player '{turn.player}'"

        # Validate phase
        if turn.phase not in ["M", "B"]:
            return False, f"Turn {i}: invalid phase '{turn.phase}'"

        # Advance to next turn
        expected_turn += 1
        expected_player = "SOUTH" if expected_player == "NORTH" else "NORTH"

    # Validate game state consistency
    if document.game_state.turn_number < 1:
        msg = "Invalid game state: turn_number must be >= 1"
        msg += f", got {document.game_state.turn_number}"
        return False, msg

    if document.game_state.current_player not in ["NORTH", "SOUTH"]:
        msg = "Invalid game state: current_player must be NORTH or SOUTH"
        msg += f", got {document.game_state.current_player}"
        return False, msg

    if document.game_state.current_phase not in ["M", "B"]:
        msg = "Invalid game state: current_phase must be M or B"
        msg += f", got {document.game_state.current_phase}"
        return False, msg

    # Validate metadata result
    valid_results = ["ONGOING", "NORTH_WINS", "SOUTH_WINS", "DRAW"]
    if document.metadata.result not in valid_results:
        return False, f"Invalid metadata result: {document.metadata.result}"

    return True, None


# =====================================================================
# Board Reconstruction
# =====================================================================

def reconstruct_board_from_history(document: KFENDocument) -> 'Board':
    """
    Reconstruct board from KFEN document with full history.

    Args:
        document: KFENDocument to reconstruct from

    Returns:
        Board object with complete state and history

    Raises:
        ValueError: If history is invalid or reconstruction fails
    """

    # Validate history first
    is_valid, error = validate_history(document)
    if not is_valid:
        raise ValueError(f"Invalid KFEN history: {error}")

    # Load board from FEN
    from . import fen
    board = fen.Fen.fen_to_board(document.board_info.fen)

    # Set game state
    board._turn = document.game_state.current_player
    board._turn_number = document.game_state.turn_number
    board._current_phase = document.game_state.current_phase

    # Restore pending retreats
    for retreat_pos in document.game_state.pending_retreats:
        board.add_pending_retreat(retreat_pos["row"], retreat_pos["col"])

    # Reconstruct undo/redo history
    board.undo_redo_manager.clear()
    _reconstruct_undo_redo_history(board, document.turn_history)

    # Set undo/redo state
    board.undo_redo_manager.max_history = document.undo_redo.max_history

    return board


def _reconstruct_undo_redo_history(board: 'Board', turn_history: List[KFENTurn]) -> None:
    """
    Reconstruct undo/redo history from turn history.

    Args:
        board: Board object to populate history for
        turn_history: List of KFENTurn objects
    """
    from .undo_redo import AttackAction, MoveAction, TurnBoundary

    current_turn_player = "NORTH"
    current_turn_number = 1

    for turn in turn_history:
        # Add moves
        for move in turn.moves:
            move_action = MoveAction(
                from_pos=(move.from_pos["row"], move.from_pos["col"]),
                to_pos=(move.to_pos["row"], move.to_pos["col"]),
                unit_id=move.unit_id,
                unit_type=move.unit_type,
                owner=turn.player,  # Player who made the move
                was_retreat=move.was_retreat,
                destroyed_arsenal=(
                    (move.destroyed_arsenal["row"],
                     move.destroyed_arsenal["col"],
                     move.destroyed_arsenal["owner"])
                    if move.destroyed_arsenal else None
                )
            )
            board.undo_redo_manager.action_history.append(move_action)
            board.undo_redo_manager.undo_stack.append(move_action)

        # Add attack if present
        if turn.attack:
            retreat_pos_list = [(pos["row"], pos["col"]) for pos in turn.attack.retreat_positions]
            attack_action = AttackAction(
                target_pos=(turn.attack.target["row"], turn.attack.target["col"]),
                outcome=turn.attack.outcome,
                attacker=turn.player,
                captured_unit=turn.attack.captured_unit,
                retreat_positions=retreat_pos_list
            )
            board.undo_redo_manager.action_history.append(attack_action)
            board.undo_redo_manager.undo_stack.append(attack_action)

        # Add turn boundary
        turn_boundary_action = TurnBoundary(
            from_turn=(current_turn_player, current_turn_number),
            to_turn=(turn.player, turn.turn_number),
            from_phase="M",
            from_moves_made=[],
            from_attacks_this_turn=1 if turn.attack else 0,
            from_attack_target=None,
            from_units_must_retreat=set()
        )
        board.undo_redo_manager.action_history.append(turn_boundary_action)
        board.undo_redo_manager.undo_stack.append(turn_boundary_action)

        # Update turn tracking
        current_turn_number = turn.turn_number
        current_turn_player = turn.player


# =====================================================================
# FEN Conversion
# =====================================================================

def convert_fen_to_kfen(fen_file: str, kfen_file: str,
                        metadata: Optional[KFENMetadata] = None) -> None:
    """
    Convert FEN file to KFEN format.

    Args:
        fen_file: Path to input FEN file
        kfen_file: Path to output KFEN file
        metadata: Optional metadata for the game record

    Example:
        >>> convert_fen_to_kfen("old_save.fen", "new_save.kfenn")
    """
    from . import fen

    # Read FEN file
    with open(fen_file) as f:
        fen_string = f.read().strip()

    # Load board from FEN
    board = fen.Fen.fen_to_board(fen_string)

    # Set created_date from file modification time if not provided
    if metadata is None:
        import os
        metadata = KFENMetadata(
            created_date=datetime.fromtimestamp(os.path.getmtime(fen_file)).isoformat() + 'Z'
        )

    # Write KFEN
    write_kfen(board, kfen_file, metadata)


def export_kfen_to_fen(kfen_file: str, fen_file: str) -> None:
    """
    Export board state from KFEN to FEN format.

    Args:
        kfen_file: Path to input KFEN file
        fen_file: Path to output FEN file

    Example:
        >>> export_kfen_to_fen("game.kfen", "game.fen")
    """
    from . import fen

    # Read KFEN file
    document = read_kfen(kfen_file)

    # Reconstruct board from KFEN (this adds turn state)
    board = reconstruct_board_from_history(document)

    # Generate complete FEN with turn state
    fen_string = fen.Fen.board_to_fen(board, include_turn_state=True)

    # Write FEN file
    with open(fen_file, 'w') as f:
        f.write(fen_string)
