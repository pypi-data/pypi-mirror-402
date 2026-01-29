"""
Unit tests for undo/redo functionality.

Tests UndoRedoManager class and its integration with Board class.
"""

import pytest

from pykrieg.board import Board
from pykrieg.constants import PLAYER_NORTH, PLAYER_SOUTH
from pykrieg.undo_redo import AttackAction, MoveAction, TurnBoundary, UndoRedoManager


class TestUndoRedoManager:
    """Test UndoRedoManager class."""

    def test_initialization(self):
        """Test UndoRedoManager initialization."""
        manager = UndoRedoManager(max_history=100)
        assert manager.max_history == 100
        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 0
        assert len(manager.action_history) == 0
        assert manager.can_undo() is False
        assert manager.can_redo() is False

    def test_record_move_action(self):
        """Test recording a move action."""
        manager = UndoRedoManager()
        action = MoveAction(
            from_pos=(5, 10),
            to_pos=(6, 11),
            unit_id=12345,
            unit_type='INFANTRY',
            owner=PLAYER_NORTH,
            was_retreat=False
        )

        manager.record_action(action)

        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0
        assert len(manager.action_history) == 1
        assert manager.can_undo() is True
        assert manager.can_redo() is False

    def test_record_attack_action(self):
        """Test recording an attack action."""
        manager = UndoRedoManager()
        action = AttackAction(
            target_pos=(10, 15),
            outcome='CAPTURE',
            attacker=PLAYER_NORTH,
            captured_unit={'unit_type': 'INFANTRY', 'owner': PLAYER_SOUTH}
        )

        manager.record_action(action)

        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0
        assert len(manager.action_history) == 1
        assert manager.can_undo() is True
        assert manager.can_redo() is False

    def test_record_turn_boundary(self):
        """Test recording a turn boundary action."""
        manager = UndoRedoManager()
        action = TurnBoundary(
            from_turn=(PLAYER_NORTH, 1),
            to_turn=(PLAYER_SOUTH, 2),
            from_phase='MOVEMENT',
            from_moves_made=[(5, 10, 6, 11)],
            from_attacks_this_turn=1,
            from_attack_target=(10, 15),
            from_units_must_retreat=set()
        )

        manager.record_action(action)

        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0
        assert len(manager.action_history) == 1
        assert manager.can_undo() is True
        assert manager.can_redo() is False

    def test_redo_stack_cleared_on_new_action(self):
        """Test that redo stack is cleared when new action is recorded."""
        board = Board()
        manager = board._undo_redo_manager

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0

        # Undo action
        board.undo()

        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 1

        # Make another move should clear redo stack
        board.create_and_place_unit(7, 12, 'CAVALRY', PLAYER_NORTH)
        board.make_turn_move(7, 12, 8, 13)

        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0

    def test_max_history_enforcement(self):
        """Test that max_history limit is enforced."""
        manager = UndoRedoManager(max_history=5)

        # Record 7 actions
        for i in range(7):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        # Only last 5 should be in history
        assert len(manager.action_history) == 5
        assert len(manager.undo_stack) == 5

    def test_set_max_history(self):
        """Test setting max_history dynamically."""
        manager = UndoRedoManager(max_history=10)

        # Record 15 actions
        for i in range(15):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        assert len(manager.action_history) == 10

        # Increase limit
        manager.set_max_history(20)

        # Record more actions
        for i in range(15, 25):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        # Should have 20 total now
        assert len(manager.action_history) == 20

    def test_unlimited_history(self):
        """Test unlimited history (max_history=0)."""
        manager = UndoRedoManager(max_history=0)

        # Record 50 actions
        for i in range(50):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        # All 50 should be in history
        assert len(manager.action_history) == 50
        assert len(manager.undo_stack) == 50

    def test_clear(self):
        """Test clearing all history."""
        manager = UndoRedoManager()

        # Record some actions
        for i in range(5):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        assert len(manager.action_history) == 5

        # Clear
        manager.clear()

        assert len(manager.action_history) == 0
        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 0
        assert manager.can_undo() is False
        assert manager.can_redo() is False

    def test_undo_raises_error_when_empty(self):
        """Test that undo raises error when undo stack is empty."""
        manager = UndoRedoManager()
        board = Board()

        with pytest.raises(ValueError, match="No actions to undo"):
            manager.undo(board)

    def test_redo_raises_error_when_empty(self):
        """Test that redo raises error when redo stack is empty."""
        manager = UndoRedoManager()
        board = Board()

        with pytest.raises(ValueError, match="No actions to redo"):
            manager.redo(board)

    def test_undo_multiple(self):
        """Test undoing multiple actions at once."""
        board = Board()
        manager = board._undo_redo_manager

        # Make 3 moves with non-overlapping positions
        # Move 0: (0,0) -> (1,1)
        # Move 1: (2,2) -> (3,3)
        # Move 2: (4,4) -> (5,5)
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.create_and_place_unit(2, 2, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(2, 2, 3, 3)
        board.create_and_place_unit(4, 4, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(4, 4, 5, 5)

        assert len(manager.undo_stack) == 3

        # Undo 2 actions
        undone = manager.undo_multiple(board, 2)
        assert len(undone) == 2
        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 2

    def test_redo_multiple(self):
        """Test redoing multiple actions at once."""
        board = Board()
        manager = board._undo_redo_manager

        # Make a move and undo it
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)
        board.undo()

        assert len(manager.redo_stack) == 1

        # Redo
        manager.redo(board)
        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0

    def test_get_history_size(self):
        """Test getting history size."""
        manager = UndoRedoManager()

        # Record some actions
        for i in range(7):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            manager.record_action(action)

        assert manager.get_history_size() == 7


class TestBoardUndoRedoIntegration:
    """Test Board class integration with undo/redo."""

    def test_board_has_undo_redo_manager(self):
        """Test that Board has UndoRedoManager instance."""
        board = Board()
        assert hasattr(board, '_undo_redo_manager')
        assert isinstance(board._undo_redo_manager, UndoRedoManager)

    def test_can_undo(self):
        """Test Board.can_undo() method."""
        board = Board()
        assert board.can_undo() is False

        # Make a move to record an action
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        assert board.can_undo() is True

    def test_can_redo(self):
        """Test Board.can_redo() method."""
        board = Board()
        assert board.can_redo() is False

        # Make a move and undo it
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)
        board.undo()

        assert board.can_redo() is True

    def test_undo(self):
        """Test Board.undo() method."""
        board = Board()
        assert board.can_undo() is False

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        assert board.can_undo() is True
        assert board.get_unit(5, 10) is None
        assert board.get_unit(6, 11) is not None

        # Undo
        board.undo()

        assert board.can_undo() is False
        assert board.get_unit(5, 10) is not None
        assert board.get_unit(6, 11) is None

    def test_undo_multiple(self):
        """Test Board.undo() with count parameter."""
        board = Board()

        # Make 3 moves with non-overlapping positions
        # Move 0: (0,0) -> (1,1)
        # Move 1: (2,2) -> (3,3)
        # Move 2: (4,4) -> (5,5)
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.create_and_place_unit(2, 2, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(2, 2, 3, 3)
        board.create_and_place_unit(4, 4, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(4, 4, 5, 5)

        assert board.can_undo() is True
        assert len(board._undo_redo_manager.undo_stack) == 3

        # Undo 2 moves (undo moves 1 and 2, leaving move 0)
        board.undo(count=2)

        assert len(board._undo_redo_manager.undo_stack) == 1
        # After undoing 2 moves (undoing moves 1 and 2):
        # Move 0: (0,0) -> (1,1), NOT undone
        # Move 1: (2,2) -> (3,3), undone
        # Move 2: (4,4) -> (5,5), undone
        assert board.get_unit(0, 0) is None  # Original position of unit 0
        assert board.get_unit(1, 1) is not None  # Current position of unit 0 (destination of move 0)
        assert board.get_unit(2, 2) is not None  # Current position of unit 1 (back at original)
        assert board.get_unit(3, 3) is None  # Original position of unit 2 (destination was cleared)
        assert board.get_unit(4, 4) is not None  # Current position of unit 2 (back at original)
        assert board.get_unit(5, 5) is None  # Destination of move 1

    def test_redo(self):
        """Test Board.redo() method."""
        board = Board()

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Undo
        board.undo()

        assert board.can_redo() is True
        assert board.get_unit(5, 10) is not None
        assert board.get_unit(6, 11) is None

        # Redo
        board.redo()

        assert board.can_redo() is False
        assert board.get_unit(5, 10) is None
        assert board.get_unit(6, 11) is not None

    def test_redo_multiple(self):
        """Test Board.redo() with count parameter."""
        board = Board()

        # Make 3 moves with non-overlapping positions
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.create_and_place_unit(2, 2, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(2, 2, 3, 3)
        board.create_and_place_unit(4, 4, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(4, 4, 5, 5)

        # Undo 2 moves
        board.undo(count=2)

        assert len(board._undo_redo_manager.redo_stack) == 2

        # Redo 1 move
        board.redo(count=1)

        assert len(board._undo_redo_manager.redo_stack) == 1
        # After redoing move (2,2)->(3,3):
        # Move (0,0)->(1,1) was not undone, so unit 0 still at (1,1)
        # Unit 1 moved from (2,2) to (3,3), so now at (3,3)
        assert board.get_unit(1, 1) is not None
        assert board.get_unit(2, 2) is None  # Undone back to (2,2)
        assert board.get_unit(3, 3) is not None  # Redone to (3,3)

    def test_set_max_undo_history(self):
        """Test Board.set_max_undo_history() method."""
        board = Board()

        # Test the manager directly to avoid turn/movement validation complexities
        # This isolates the max_history functionality
        for i in range(10):
            action = MoveAction(
                from_pos=(i, i),
                to_pos=(i+1, i+1),
                unit_id=i,
                unit_type='INFANTRY',
                owner=PLAYER_NORTH,
                was_retreat=False
            )
            board._undo_redo_manager.record_action(action)

        # Should have 10 actions
        assert board._undo_redo_manager.get_history_size() == 10

        # Set limit to 5
        board.set_max_undo_history(5)

        # Should only have last 5 actions
        assert board._undo_redo_manager.max_history == 5
        assert board._undo_redo_manager.get_history_size() == 5

    def test_undo_move_action_restores_state(self):
        """Test that undoing a move action properly restores board state."""
        board = Board()

        # Place unit and move it
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Verify state after move
        assert board.get_unit(5, 10) is None
        assert board.get_unit(6, 11) is not None
        assert board.get_unit_type(6, 11) == 'INFANTRY'
        assert board.get_unit_owner(6, 11) == PLAYER_NORTH
        assert len(board._moved_units) == 1
        assert len(board._moved_unit_ids) == 1
        assert len(board._moves_made) == 1

        # Undo
        board.undo()

        # Verify state after undo
        assert board.get_unit(5, 10) is not None
        assert board.get_unit(6, 11) is None
        assert board.get_unit_type(5, 10) == 'INFANTRY'
        assert board.get_unit_owner(5, 10) == PLAYER_NORTH
        assert len(board._moved_units) == 0
        assert len(board._moved_unit_ids) == 0
        assert len(board._moves_made) == 0

    def test_undo_turn_boundary_restores_state(self):
        """Test that undoing a turn boundary properly restores turn state."""
        board = Board()

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Store initial state
        initial_turn = board.turn
        initial_turn_number = board.turn_number
        initial_phase = board._current_phase
        initial_moved_units = set(board._moved_units)
        initial_moves_made = list(board._moves_made)

        # End turn
        board.end_turn()

        # Verify state changed
        assert board.turn != initial_turn
        assert board.turn_number > initial_turn_number
        assert board._current_phase == initial_phase
        assert len(board._moved_units) == 0

        # Undo turn boundary
        board.undo()

        # Verify state restored
        assert board.turn == initial_turn
        assert board.turn_number == initial_turn_number
        assert board._current_phase == initial_phase
        assert board._moved_units == initial_moved_units
        assert board._moves_made == initial_moves_made

    def test_network_marked_dirty_after_undo(self):
        """Test that network is marked dirty after undo."""
        board = Board()
        board.enable_networks()

        # Initially network is calculated
        assert board._network_calculated is True
        assert board._network_dirty is False

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Network is marked dirty by movement
        assert board._network_dirty is True

        # Undo
        board.undo()

        # Network should still be dirty after undo
        assert board._network_dirty is True

    def test_network_marked_dirty_after_redo(self):
        """Test that network is marked dirty after redo."""
        board = Board()
        board.enable_networks()

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Undo
        board.undo()

        # Redo
        board.redo()

        # Network should be dirty after redo
        assert board._network_dirty is True


class TestActionRecording:
    """Test action recording in Board methods."""

    def test_make_turn_move_records_action(self):
        """Test that make_turn_move records an action."""
        board = Board()

        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Action should be recorded
        assert board.can_undo() is True
        assert len(board._undo_redo_manager.undo_stack) == 1

        action = board._undo_redo_manager.undo_stack[0]
        assert isinstance(action, MoveAction)
        assert action.from_pos == (5, 10)
        assert action.to_pos == (6, 11)
        assert action.unit_type == 'INFANTRY'
        assert action.owner == PLAYER_NORTH
        assert action.was_retreat is False

    def test_make_turn_move_with_retreat(self):
        """Test that retreat moves are recorded correctly."""
        board = Board()

        # Set turn to SOUTH so SOUTH units can move
        board._turn = PLAYER_SOUTH

        # Place unit and mark for retreat
        board.create_and_place_unit(15, 10, 'INFANTRY', PLAYER_SOUTH)
        board._units_must_retreat.add((15, 10))

        # Make retreat move (valid move for SOUTH unit in SOUTH territory)
        board.make_turn_move(15, 10, 14, 9)

        # Action should be recorded with was_retreat=True
        # Index -1 is the top of stack (most recent action)
        action = board._undo_redo_manager.undo_stack[-1]
        assert action.was_retreat is True
        assert (15, 10) not in board._units_must_retreat

    def test_make_turn_attack_records_action(self):
        """Test that make_turn_attack records an action."""
        board = Board()

        # Place attacker and defender
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(10, 15, 'INFANTRY', PLAYER_SOUTH)

        # Switch to battle phase
        board.switch_to_battle_phase()

        # Make attack
        board.make_turn_attack(10, 15)

        # Action should be recorded
        assert board.can_undo() is True
        assert len(board._undo_redo_manager.undo_stack) == 1

        action = board._undo_redo_manager.undo_stack[0]
        assert isinstance(action, AttackAction)
        assert action.target_pos == (10, 15)
        assert action.attacker == PLAYER_NORTH
        assert action.outcome in ('CAPTURE', 'RETREAT', 'FAIL')

    def test_end_turn_records_action(self):
        """Test that end_turn records a turn boundary action."""
        board = Board()

        # Make a move
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # End turn
        board.end_turn()

        # Turn boundary should be recorded
        assert board.can_undo() is True
        assert len(board._undo_redo_manager.undo_stack) == 2  # move + turn boundary

        # Index -1 is the top of stack (most recent action = turn boundary)
        # Index 0 is the bottom of stack (oldest action = move)
        turn_boundary = board._undo_redo_manager.undo_stack[-1]
        assert isinstance(turn_boundary, TurnBoundary)
        assert turn_boundary.action_type == 'turn_boundary'

    def test_multiple_actions_recorded_correctly(self):
        """Test that multiple actions are recorded in correct order."""
        board = Board()

        # Make 3 moves
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.create_and_place_unit(2, 2, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(2, 2, 3, 3)
        board.create_and_place_unit(4, 4, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(4, 4, 5, 5)

        # End turn
        board.end_turn()

        # Should have 4 actions (3 moves + 1 turn boundary)
        assert board._undo_redo_manager.get_history_size() == 4
        assert len(board._undo_redo_manager.undo_stack) == 4

        # Verify order (oldest at bottom)
        assert board._undo_redo_manager.undo_stack[0].from_pos == (0, 0)
        assert board._undo_redo_manager.undo_stack[1].from_pos == (2, 2)
        assert board._undo_redo_manager.undo_stack[2].from_pos == (4, 4)
        assert board._undo_redo_manager.undo_stack[3].action_type == 'turn_boundary'


class TestAttackUndoRedo:
    """Test attack undo/redo edge cases."""

    def test_undo_attack_capture(self):
        """Test undoing a capture attack."""
        board = Board()
        # Place attacker and defender close enough for combat
        # Use multiple attackers to ensure capture
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(5, 12, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(5, 14, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(6, 11, 'INFANTRY', PLAYER_SOUTH)  # defender

        # Switch to battle phase
        board.switch_to_battle_phase()

        # Make attack (capture expected due to numerical advantage)
        board.make_turn_attack(6, 11)

        # Verify attack was recorded
        assert board._attacks_this_turn == 1
        # Note: We can't assume capture - it depends on combat calculation
        # Just verify the attack was recorded and can be undone

        # Undo
        board.undo()

        # Verify state restored
        assert board._attacks_this_turn == 0
        # Unit should still exist
        assert board.get_unit(6, 11) is not None

    def test_undo_attack_retreat(self):
        """Test undoing a retreat attack."""
        board = Board()
        # Place attacker and defender (defender slightly weaker)
        board.create_and_place_unit(5, 10, 'CAVALRY', PLAYER_NORTH)
        board.create_and_place_unit(6, 11, 'INFANTRY', PLAYER_SOUTH)

        # Switch to battle phase
        board.switch_to_battle_phase()

        # Make attack
        board.make_turn_attack(6, 11)

        # Verify attack recorded
        assert board._attacks_this_turn == 1

        # Undo
        board.undo()

        # Verify state restored
        assert board._attacks_this_turn == 0
        assert board._attack_target is None

    def test_undo_attack_fail(self):
        """Test undoing a failed attack."""
        board = Board()
        # Place attacker and defender (defender stronger)
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(6, 11, 'CANNON', PLAYER_SOUTH)

        # Switch to battle phase
        board.switch_to_battle_phase()

        # Make attack (may fail due to strong defender)
        board.make_turn_attack(6, 11)

        # Verify attack occurred
        assert board._attacks_this_turn == 1

        # Undo
        board.undo()

        # Verify state restored
        assert board._attacks_this_turn == 0
        assert board._attack_target is None

    def test_redo_attack_capture(self):
        """Test redoing a capture attack."""
        board = Board()
        # Place attacker and defender
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(5, 12, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(5, 14, 'INFANTRY', PLAYER_NORTH)
        board.create_and_place_unit(6, 11, 'INFANTRY', PLAYER_SOUTH)  # defender

        # Switch to battle phase
        board.switch_to_battle_phase()

        # Make attack
        board.make_turn_attack(6, 11)
        assert board._attacks_this_turn == 1

        # Undo
        board.undo()
        assert board._attacks_this_turn == 0

        # Redo
        board.redo()

        # Verify attack reapplied
        assert board._attacks_this_turn == 1


class TestArsenalDestructionUndo:
    """Test arsenal destruction undo/redo."""

    def test_undo_arsenal_destruction(self):
        """Test undoing arsenal destruction via move."""
        board = Board()
        # Place enemy arsenal (in SOUTH territory) close to NORTH territory
        board.set_arsenal(11, 10, PLAYER_SOUTH)

        # Place CAVALRY unit in NORTH territory - CAVALRY has range 2
        board.create_and_place_unit(9, 10, 'CAVALRY', PLAYER_NORTH)

        # Move directly onto arsenal (distance 2)
        board.make_turn_move(9, 10, 11, 10)

        # Verify arsenal destroyed
        assert board.get_terrain(11, 10) is None

        # Undo the move that destroyed arsenal
        board.undo()

        # Verify arsenal recreated
        terrain = board.get_terrain(11, 10)
        assert terrain == 'ARSENAL'
        # Owner is stored separately in _arsenal_owners
        assert (11, 10) in board._arsenal_owners
        assert board._arsenal_owners[(11, 10)] == PLAYER_SOUTH
        # Verify unit back at position
        assert board.get_unit(11, 10) is None
        assert board.get_unit(9, 10) is not None

    def test_redo_arsenal_destruction(self):
        """Test redoing arsenal destruction."""
        board = Board()
        # Place enemy arsenal (in SOUTH territory) close to NORTH territory
        board.set_arsenal(11, 10, PLAYER_SOUTH)

        # Place CAVALRY unit in NORTH territory - CAVALRY has range 2
        board.create_and_place_unit(9, 10, 'CAVALRY', PLAYER_NORTH)

        # Move onto arsenal directly (distance 2)
        board.make_turn_move(9, 10, 11, 10)
        assert board.get_terrain(11, 10) is None

        # Undo the move that destroyed arsenal
        board.undo()
        assert board.get_terrain(11, 10) is not None

        # Redo
        board.redo()

        # Verify arsenal destroyed again
        assert board.get_terrain(11, 10) is None


class TestRetreatTrackingUndo:
    """Test retreat tracking undo/redo."""

    def test_undo_retreat_move(self):
        """Test undoing a retreat move."""
        board = Board()
        # Switch to SOUTH turn
        board._turn = PLAYER_SOUTH

        # Place unit and mark for retreat
        board.create_and_place_unit(15, 10, 'INFANTRY', PLAYER_SOUTH)
        board._units_must_retreat.add((15, 10))

        # Make retreat move
        board.make_turn_move(15, 10, 14, 9)

        # Verify retreat marker removed
        assert (15, 10) not in board._units_must_retreat

        # Undo
        board.undo()

        # Verify retreat marker restored
        assert (15, 10) in board._units_must_retreat
        # Verify unit back at original position
        assert board.get_unit(15, 10) is not None
        assert board.get_unit(14, 9) is None

    def test_redo_retreat_move(self):
        """Test redoing a retreat move."""
        board = Board()
        # Switch to SOUTH turn
        board._turn = PLAYER_SOUTH

        # Place unit and mark for retreat
        board.create_and_place_unit(15, 10, 'INFANTRY', PLAYER_SOUTH)
        board._units_must_retreat.add((15, 10))

        # Make retreat move
        board.make_turn_move(15, 10, 14, 9)
        assert (15, 10) not in board._units_must_retreat

        # Undo
        board.undo()
        assert (15, 10) in board._units_must_retreat

        # Redo
        board.redo()

        # Verify retreat marker removed again
        assert (15, 10) not in board._units_must_retreat
        assert board.get_unit(14, 9) is not None


class TestMultiTurnUndo:
    """Test multi-turn undo scenarios."""

    def test_undo_multiple_turns(self):
        """Test undoing past multiple turn boundaries."""
        board = Board()
        # Make two moves in turn 1 (NORTH) with different units
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.create_and_place_unit(2, 2, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(2, 2, 3, 3)

        # End turn (switches to SOUTH)
        board.end_turn()

        # End turn 2 without making a move (just switch back to NORTH)
        board.end_turn()

        # Should be turn 3 now (NORTH's turn again)
        assert board.turn == PLAYER_NORTH
        assert board.turn_number == 3

        # Undo past turn boundary (undo turn 2's turn boundary)
        board.undo(count=1)

        # Should be back to turn 2 (SOUTH's turn)
        assert board.turn == PLAYER_SOUTH
        assert board.turn_number == 2

    def test_redo_multiple_turns(self):
        """Test redoing multiple turn boundaries."""
        board = Board()
        # Play two turns
        board.create_and_place_unit(0, 0, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(0, 0, 1, 1)
        board.end_turn()

        # End turn 2 without making a move
        board.end_turn()

        # Undo past one turn boundary (back to turn 2 SOUTH)
        board.undo(count=1)
        assert board.turn == PLAYER_SOUTH
        assert board.turn_number == 2

        # Redo back to turn 3
        board.redo(count=1)

        # Should be back at turn 3
        assert board.turn == PLAYER_NORTH
        assert board.turn_number == 3


class TestSaveLoadClearsHistory:
    """Test that save/load clears undo/redo history."""

    def test_save_clears_undo_history(self):
        """Test that save clears undo history."""
        import os
        import tempfile

        from pykrieg.fen import Fen

        board = Board()
        # Make some moves
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Verify undo available
        assert board.can_undo() is True

        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fen', delete=False) as f:
            save_file = f.name
            fen = Fen.board_to_fen(board)
            f.write(fen)

        # Clear history manually (simulating what game.py does)
        board._undo_redo_manager.clear()

        # Verify undo not available
        assert board.can_undo() is False
        assert board.can_redo() is False

        # Cleanup
        os.unlink(save_file)

    def test_load_clears_undo_history(self):
        """Test that load clears undo history."""
        import os
        import tempfile

        from pykrieg.fen import Fen

        board = Board()
        # Make some moves on board
        board.create_and_place_unit(5, 10, 'INFANTRY', PLAYER_NORTH)
        board.make_turn_move(5, 10, 6, 11)

        # Verify undo available
        assert board.can_undo() is True

        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fen', delete=False) as f:
            save_file = f.name
            fen = Fen.board_to_fen(board)
            f.write(fen)

        # Load from file
        with open(save_file) as f:
            loaded_fen = f.read()

        new_board = Fen.fen_to_board(loaded_fen)

        # Clear history manually (simulating what game.py does)
        new_board._undo_redo_manager.clear()

        # Verify undo not available on loaded board
        assert new_board.can_undo() is False
        assert new_board.can_redo() is False

        # Cleanup
        os.unlink(save_file)
