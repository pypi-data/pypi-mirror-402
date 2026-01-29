"""
Undo/Redo functionality for Pykrieg.

This module implements action-based undo/redo using reversible operations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union


@dataclass
class MoveAction:
    """Represents a move action for undo/redo."""
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    unit_id: int
    unit_type: str
    owner: str
    was_retreat: bool
    destroyed_arsenal: Optional[Tuple[int, int, str]] = None  # Arsenal destroyed: (row, col, owner)
    action_type: str = 'move'

    def to_dict(self) -> Dict[str, Any]:
        """Convert MoveAction to dictionary for KFEN serialization.

        Returns:
            Dictionary representation of this action
        """
        result: Dict[str, Any] = {
            "from_pos": {"row": self.from_pos[0], "col": self.from_pos[1]},
            "to_pos": {"row": self.to_pos[0], "col": self.to_pos[1]},
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "owner": self.owner,
            "was_retreat": self.was_retreat,
            "action_type": self.action_type
        }
        if self.destroyed_arsenal:
            result["destroyed_arsenal"] = {
                "row": self.destroyed_arsenal[0],
                "col": self.destroyed_arsenal[1],
                "owner": self.destroyed_arsenal[2]
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoveAction':
        """Create MoveAction from dictionary (KFEN deserialization).

        Args:
            data: Dictionary representation of this action

        Returns:
            MoveAction object
        """
        destroyed_arsenal = None
        if "destroyed_arsenal" in data and data["destroyed_arsenal"]:
            destroyed_arsenal = (
                data["destroyed_arsenal"]["row"],
                data["destroyed_arsenal"]["col"],
                data["destroyed_arsenal"]["owner"]
            )

        return cls(
            from_pos=(data["from_pos"]["row"], data["from_pos"]["col"]),
            to_pos=(data["to_pos"]["row"], data["to_pos"]["col"]),
            unit_id=data["unit_id"],
            unit_type=data["unit_type"],
            owner=data["owner"],
            was_retreat=data["was_retreat"],
            destroyed_arsenal=destroyed_arsenal
        )


@dataclass
class AttackAction:
    """Represents an attack action for undo/redo."""
    target_pos: Tuple[int, int]
    outcome: str  # 'CAPTURE', 'RETREAT', 'FAIL'
    attacker: str
    captured_unit: Optional[Dict[str, Any]] = None  # {'unit_type': str, 'owner': str} if captured
    retreat_positions: List[Tuple[int, int]] = field(
        default_factory=list
    )  # Units marked for retreat
    action_type: str = 'attack'

    def to_dict(self) -> Dict[str, Any]:
        """Convert AttackAction to dictionary for KFEN serialization.

        Returns:
            Dictionary representation of this action
        """
        return {
            "target_pos": {"row": self.target_pos[0], "col": self.target_pos[1]},
            "outcome": self.outcome,
            "attacker": self.attacker,
            "captured_unit": self.captured_unit,
            "retreat_positions": [
                {"row": pos[0], "col": pos[1]} for pos in self.retreat_positions
            ],
            "action_type": self.action_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackAction':
        """Create AttackAction from dictionary (KFEN deserialization).

        Args:
            data: Dictionary representation of this action

        Returns:
            AttackAction object
        """
        return cls(
            target_pos=(data["target_pos"]["row"], data["target_pos"]["col"]),
            outcome=data["outcome"],
            attacker=data["attacker"],
            captured_unit=data.get("captured_unit"),
            retreat_positions=[
                (pos["row"], pos["col"]) for pos in data.get("retreat_positions", [])
            ]
        )


@dataclass
class TurnBoundary:
    """Represents a turn boundary for undo/redo."""
    from_turn: Tuple[str, int]  # (player, turn_number)
    to_turn: Tuple[str, int]  # (player, turn_number)
    from_phase: str
    from_moves_made: List[Tuple[int, int, int, int]]
    from_attacks_this_turn: int
    from_attack_target: Optional[Tuple[int, int]]
    from_units_must_retreat: Set[Tuple[int, int]]
    action_type: str = 'turn_boundary'

    def to_dict(self) -> Dict[str, Any]:
        """Convert TurnBoundary to dictionary for KFEN serialization.

        Returns:
            Dictionary representation of this action
        """
        return {
            "from_turn": {"player": self.from_turn[0], "turn_number": self.from_turn[1]},
            "to_turn": {"player": self.to_turn[0], "turn_number": self.to_turn[1]},
            "from_phase": self.from_phase,
            "from_moves_made": self.from_moves_made,
            "from_attacks_this_turn": self.from_attacks_this_turn,
            "from_attack_target": (
                {"row": self.from_attack_target[0], "col": self.from_attack_target[1]}
                if self.from_attack_target else None
            ),
            "from_units_must_retreat": list(self.from_units_must_retreat),
            "action_type": self.action_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TurnBoundary':
        """Create TurnBoundary from dictionary (KFEN deserialization).

        Args:
            data: Dictionary representation of this action

        Returns:
            TurnBoundary object
        """
        attack_target = None
        if data.get("from_attack_target"):
            attack_target = (
                data["from_attack_target"]["row"],
                data["from_attack_target"]["col"]
            )

        return cls(
            from_turn=(data["from_turn"]["player"], data["from_turn"]["turn_number"]),
            to_turn=(data["to_turn"]["player"], data["to_turn"]["turn_number"]),
            from_phase=data["from_phase"],
            from_moves_made=data["from_moves_made"],
            from_attacks_this_turn=data["from_attacks_this_turn"],
            from_attack_target=attack_target,
            from_units_must_retreat={
                (pos["row"], pos["col"]) for pos in data.get("from_units_must_retreat", [])
            }
        )


# Type alias for all action types
Action = Union[MoveAction, AttackAction, TurnBoundary]


class UndoRedoManager:
    """
    Manages undo/redo functionality for game board.

    This class maintains action history, undo stack, and redo stack,
    and provides methods to record, undo, and redo actions.
    """

    def __init__(self, max_history: int = 100) -> None:
        """Initialize UndoRedoManager.

        Args:
            max_history: Maximum number of actions to keep in history.
                        Set to 0 for unlimited history.
        """
        self.action_history: List[Action] = []
        self.undo_stack: List[Action] = []
        self.redo_stack: List[Action] = []
        self.max_history: int = max_history
        self._recording_during_undo_redo: bool = False

    def record_action(self, action: Action) -> None:
        """Record an action for undo/redo.

        Args:
            action: The action to record
        """
        # Don't record actions during undo/redo operations
        if self._recording_during_undo_redo:
            return

        # Add to action history
        self.action_history.append(action)

        # Push to undo stack
        self.undo_stack.append(action)

        # Clear redo stack
        self.redo_stack.clear()

        # Trim history if needed
        if self.max_history > 0 and len(self.action_history) > self.max_history:
            # Remove oldest action from history and undo stack
            oldest_action = self.action_history.pop(0)
            if oldest_action in self.undo_stack:
                self.undo_stack.remove(oldest_action)

    def undo(self, board: Any) -> Action:
        """Undo most recent action.

        Args:
            board: The Board object to apply undo to

        Returns:
            The action that was undone

        Raises:
            ValueError: If no actions to undo
        """
        if not self.can_undo():
            raise ValueError("No actions to undo")

        # Pop action from undo stack
        action = self.undo_stack.pop()

        # Set flag to prevent clearing redo stack during undo
        self._recording_during_undo_redo = True

        try:
            # Execute reverse operation based on action type
            if action.action_type == 'move':
                self._undo_move(board, action)  # type: ignore[arg-type]
            elif action.action_type == 'attack':
                self._undo_attack(board, action)  # type: ignore[arg-type]
            elif action.action_type == 'turn_boundary':
                self._undo_turn_boundary(board, action)  # type: ignore[arg-type]

            # Mark network as dirty
            board._network_dirty = True
        finally:
            self._recording_during_undo_redo = False

        # Push action to redo stack
        self.redo_stack.append(action)

        return action

    def redo(self, board: Any) -> Action:
        """Redo most recently undone action.

        Args:
            board: The Board object to apply redo to

        Returns:
            The action that was redone

        Raises:
            ValueError: If no actions to redo
        """
        if not self.can_redo():
            raise ValueError("No actions to redo")

        # Pop action from redo stack
        action = self.redo_stack.pop()

        # Set flag to prevent clearing redo stack during redo
        self._recording_during_undo_redo = True

        try:
            # Re-execute action based on type
            if action.action_type == 'move':
                self._redo_move(board, action)  # type: ignore[arg-type]
            elif action.action_type == 'attack':
                self._redo_attack(board, action)  # type: ignore[arg-type]
            elif action.action_type == 'turn_boundary':
                self._redo_turn_boundary(board, action)  # type: ignore[arg-type]

            # Mark network as dirty
            board._network_dirty = True
        finally:
            self._recording_during_undo_redo = False

        # Push action back to undo stack
        self.undo_stack.append(action)

        return action

    def undo_multiple(self, board: Any, count: int) -> List[Action]:
        """Undo multiple actions.

        Args:
            board: The Board object to apply undo to
            count: Number of actions to undo

        Returns:
            List of actions that were undone

        Raises:
            ValueError: If count exceeds available actions
        """
        if count > len(self.undo_stack):
            raise ValueError(f"Cannot undo {count} actions, only {len(self.undo_stack)} available")

        undone_actions = []
        for _ in range(count):
            action = self.undo(board)
            undone_actions.append(action)

        return undone_actions

    def redo_multiple(self, board: Any, count: int) -> List[Action]:
        """Redo multiple actions.

        Args:
            board: The Board object to apply redo to
            count: Number of actions to redo

        Returns:
            List of actions that were redone

        Raises:
            ValueError: If count exceeds available actions
        """
        if count > len(self.redo_stack):
            raise ValueError(f"Cannot redo {count} actions, only {len(self.redo_stack)} available")

        redone_actions = []
        for _ in range(count):
            action = self.redo(board)
            redone_actions.append(action)

        return redone_actions

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if undo is available, False otherwise
        """
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if redo is available, False otherwise
        """
        return len(self.redo_stack) > 0

    def set_max_history(self, max_size: int) -> None:
        """Set maximum history size.

        Args:
            max_size: Maximum number of actions to keep. Set to 0 for unlimited.
        """
        self.max_history = max_size

        # Trim action_history if needed
        if self.max_history > 0 and len(self.action_history) > self.max_history:
            # Remove oldest actions
            excess = len(self.action_history) - self.max_history
            for _ in range(excess):
                oldest_action = self.action_history.pop(0)
                if oldest_action in self.undo_stack:
                    self.undo_stack.remove(oldest_action)

    def clear(self) -> None:
        """Clear all undo/redo history.

        This should be called on save/load operations.
        """
        self.action_history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_history_size(self) -> int:
        """Get current history size.

        Returns:
            Number of actions in history
        """
        return len(self.action_history)

    # Private undo methods

    def _undo_move(self, board: Any, action: MoveAction) -> None:
        """Undo a move action.

        Args:
            board: The Board object
            action: The MoveAction to undo
        """
        from_pos = action.from_pos
        to_pos = action.to_pos

        # Get unit from destination
        unit = board.get_unit(to_pos[0], to_pos[1])
        if unit is None:
            raise ValueError(f"No unit at destination {to_pos} to undo move")

        # Move unit back to source
        board._board[from_pos[0]][from_pos[1]] = unit
        board._board[to_pos[0]][to_pos[1]] = None

        # Remove from board._moved_units
        if from_pos in board._moved_units:
            board._moved_units.remove(from_pos)

        # Remove from board._moved_unit_ids
        if action.unit_id in board._moved_unit_ids:
            board._moved_unit_ids.remove(action.unit_id)

        # Remove from board._moves_made
        move_tuple = (from_pos[0], from_pos[1], to_pos[0], to_pos[1])
        if move_tuple in board._moves_made:
            board._moves_made.remove(move_tuple)

        # If was retreat, add back to board._units_must_retreat
        if action.was_retreat:
            board._units_must_retreat.add(from_pos)

        # If arsenal was destroyed, recreate it
        if action.destroyed_arsenal:
            row, col, owner = action.destroyed_arsenal
            board.set_arsenal(row, col, owner)

    def _undo_attack(self, board: Any, action: AttackAction) -> None:
        """Undo an attack action.

        Args:
            board: The Board object
            action: The AttackAction to undo
        """
        target_pos = action.target_pos

        # Handle based on outcome
        if action.outcome == 'CAPTURE':
            # Recreate captured unit at target position
            if action.captured_unit:
                unit_type = action.captured_unit['unit_type']
                owner = action.captured_unit['owner']
                board.create_and_place_unit(target_pos[0], target_pos[1], unit_type, owner)

            # Remove from pending retreats if present
            if target_pos in board._pending_retreats:
                board._pending_retreats.remove(target_pos)

        elif action.outcome == 'RETREAT':
            # Remove from pending retreats
            if target_pos in board._pending_retreats:
                board._pending_retreats.remove(target_pos)

        # For both CAPTURE and RETREAT: remove retreat markers
        if action.outcome in ('CAPTURE', 'RETREAT'):
            # Remove all retreat positions marked by this attack
            for pos in action.retreat_positions:
                if pos in board._units_must_retreat:
                    board._units_must_retreat.remove(pos)

        # For all outcomes: decrement attack counter
        if board._attacks_this_turn > 0:
            board._attacks_this_turn -= 1

        # Clear attack target
        if board._attack_target == target_pos:
            board._attack_target = None

    def _undo_turn_boundary(self, board: Any, action: TurnBoundary) -> None:
        """Undo a turn boundary action.

        Args:
            board: The Board object
            action: The TurnBoundary to undo
        """
        # Restore turn number and player
        board._turn_number = action.from_turn[1]
        board._turn = action.from_turn[0]

        # Restore phase
        board._current_phase = action.from_phase

        # Restore moved_units and moved_unit_ids
        board._moved_units.clear()
        board._moved_unit_ids.clear()
        for move in action.from_moves_made:
            from_pos = (move[0], move[1])
            board._moved_units.add(from_pos)
            # We can't restore unit_id without storing it, so we skip that
            # This is a limitation that's acceptable for undo functionality

        # Restore moves_made
        board._moves_made = action.from_moves_made.copy()

        # Restore attacks_this_turn
        board._attacks_this_turn = action.from_attacks_this_turn

        # Restore attack_target
        board._attack_target = action.from_attack_target

        # Restore units_must_retreat
        board._units_must_retreat = action.from_units_must_retreat.copy()

    # Private redo methods

    def _redo_move(self, board: Any, action: MoveAction) -> None:
        """Redo a move action.

        Args:
            board: The Board object
            action: The MoveAction to redo
        """
        from_pos = action.from_pos
        to_pos = action.to_pos

        # Call make_turn_move to re-execute the move
        # This will handle all of tracking and state updates
        board.make_turn_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])

    def _redo_attack(self, board: Any, action: AttackAction) -> None:
        """Redo an attack action.

        Args:
            board: The Board object
            action: The AttackAction to redo
        """
        target_pos = action.target_pos

        # Call make_turn_attack to re-execute the attack
        # This will handle all of tracking and state updates
        board.make_turn_attack(target_pos[0], target_pos[1])

    def _redo_turn_boundary(self, board: Any, action: TurnBoundary) -> None:
        """Redo a turn boundary action.

        Args:
            board: The Board object
            action: The TurnBoundary to redo
        """
        # Manually restore turn state from action
        board._turn_number = action.to_turn[1]
        board._turn = action.to_turn[0]
        board._current_phase = 'MOVEMENT'  # Reset to movement phase

        # Clear per-turn state
        board._moved_units.clear()
        board._moved_unit_ids.clear()
        board._moves_made.clear()
        board._attacks_this_turn = 0
        board._attack_target = None

        # Note: We don't call resolve_retreats() here because
        # retreat resolution is part of the turn boundary action itself
        # and would have been handled when the turn boundary
        # was originally recorded
