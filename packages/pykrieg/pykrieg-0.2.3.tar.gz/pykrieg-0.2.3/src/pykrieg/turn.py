"""Turn management system for Pykrieg.

This module implements turn structure, phase management, and turn
validation rules for the game.

Turn Structure:
- Turn Start: Resolve pending retreats
- Movement Phase: Up to 5 units can move
- Battle Phase: 1 attack or pass
- End Turn: Switch player, increment turn number

Scope for 0.1.4:
- Turn validation (movement limit, attack limit)
- Phase management
- Retreat resolution
- Turn state management
- Online/offline status NOT enforced (added in 0.2.0)
"""

from typing import Any, Dict, List, Set, Tuple

from .board import Board


class TurnValidationError(Exception):
    """Raised when a turn action violates turn rules."""
    pass


class TurnState:
    """Represents the state of a turn.

    Attributes:
        moved_units: Set of original (row, col) for units moved this turn
        attacks_this_turn: Number of attacks made (0 or 1)
        current_phase: 'M' (Movement) or 'B' (Battle)
        pending_retreats: List of (row, col) for units that must retreat
    """

    def __init__(self,
                 moved_units: Set[Tuple[int, int]],
                 attacks_this_turn: int,
                 current_phase: str,
                 pending_retreats: List[Tuple[int, int]]):
        self.moved_units = moved_units
        self.attacks_this_turn = attacks_this_turn
        self.current_phase = current_phase
        self.pending_retreats = pending_retreats

    def to_dict(self) -> Dict[str, object]:
        """Convert turn state to dictionary for serialization."""
        return {
            'moved_units': list(self.moved_units),
            'attacks_this_turn': self.attacks_this_turn,
            'current_phase': self.current_phase,
            'pending_retreats': self.pending_retreats,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'TurnState':
        """Create TurnState from dictionary."""
        moved_units_data = data.get('moved_units', [])
        attacks_data = data.get('attacks_this_turn', 0)
        phase_data = data.get('current_phase', 'M')
        retreats_data = data.get('pending_retreats', [])

        # Type cast for moved_units
        units_set: Set[Tuple[int, int]] = set()
        if moved_units_data and isinstance(moved_units_data, list):
            for item in moved_units_data:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    units_set.add((int(item[0]), int(item[1])))

        # Type cast for retreats
        retreats_list: List[Tuple[int, int]] = []
        if retreats_data and isinstance(retreats_data, list):
            for item in retreats_data:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    retreats_list.append((int(item[0]), int(item[1])))

        return cls(
            moved_units=units_set,
            attacks_this_turn=int(attacks_data) if isinstance(attacks_data, (int, str)) else 0,
            current_phase=str(phase_data) if phase_data else 'M',
            pending_retreats=retreats_list,
        )


def get_turn_state(board: Board) -> TurnState:
    """Get the current turn state from board.

    Args:
        board: The game board

    Returns:
        TurnState object with current turn information
    """
    return TurnState(
        moved_units=set(board._moved_units),
        attacks_this_turn=board._attacks_this_turn,
        current_phase=board._current_phase,
        pending_retreats=board.get_pending_retreats(),
    )


def validate_turn_action(board: Board, action_type: str, **kwargs: Any) -> bool:
    """Validate a turn action.

    Args:
        board: The game board
        action_type: Type of action ('move', 'attack', 'pass')
        **kwargs: Action-specific parameters

    Returns:
        True if action is valid, False otherwise
    """
    if action_type == 'move':
        from_row = kwargs.get('from_row')
        from_col = kwargs.get('from_col')
        to_row = kwargs.get('to_row')
        to_col = kwargs.get('to_col')
        # Validate all parameters are present and are integers
        if not all(isinstance(x, int) for x in [from_row, from_col, to_row, to_col]):
            return False
        # Cast to int (mypy knows they're int after the check above)
        return board.validate_move(int(from_row), int(from_col), int(to_row), int(to_col))  # type: ignore[arg-type]
    elif action_type == 'attack':
        target_row = kwargs.get('target_row')
        target_col = kwargs.get('target_col')
        # Validate all parameters are present and are integers
        if not all(isinstance(x, int) for x in [target_row, target_col]):
            return False
        # Cast to int (mypy knows they're int after the check above)
        return board.validate_attack(int(target_row), int(target_col))  # type: ignore[arg-type]
    elif action_type == 'pass':
        return (board._current_phase == 'B' and
                board._attacks_this_turn == 0)
    else:
        return False


def can_end_turn(board: Board) -> bool:
    """Check if turn can be ended.

    Args:
        board: The game board

    Returns:
        True if turn can be ended, False otherwise

    Note:
        - In movement phase, can end turn at any time (0-5 moves)
        - In battle phase, must attack or pass before ending turn
    """
    if board._current_phase == 'B':
        # Must have attacked or passed
        return board._attacks_this_turn == 1
    else:
        # Movement phase: can end at any time
        return True


def get_turn_summary(board: Board) -> Dict:
    """Get a summary of the current turn state.

    Args:
        board: The game board

    Returns:
        Dictionary with turn summary information
    """
    return {
        'turn_number': board.turn_number,
        'current_player': board.turn,
        'current_phase': board.current_phase,
        'moves_made': len(board._moved_unit_ids),
        'moves_remaining': 5 - len(board._moved_unit_ids),
        'attacks_made': board._attacks_this_turn,
        'attacks_remaining': 1 - board._attacks_this_turn,
        'pending_retreats': len(board.get_pending_retreats()),
    }
