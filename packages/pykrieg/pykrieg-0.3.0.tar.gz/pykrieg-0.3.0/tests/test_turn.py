"""Tests for turn management system (0.1.4)."""

import pytest

from pykrieg import Board, TurnState, get_turn_state, get_turn_summary


class TestTurnStateTracking:
    """Test turn state tracking functionality."""

    def test_initial_turn_state(self):
        """Test board initializes with correct turn state."""
        board = Board()

        assert board.turn_number == 1
        assert board.turn == 'NORTH'
        assert board.current_phase == 'M'
        assert board.get_moves_this_turn() == 0
        assert board.get_attacks_this_turn() == 0
        assert len(board.get_pending_retreats()) == 0

    def test_moved_units_tracking(self):
        """Test that moved units are tracked correctly."""
        board = Board()
        # Add arsenal so units are online (required for 0.2.0 network system)
        board.set_arsenal(5, 0, "NORTH")
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")

        # Make moves
        board.make_turn_move(5, 10, 6, 10)
        board.make_turn_move(5, 11, 6, 11)

        assert board.get_moves_this_turn() == 2
        assert board.has_moved_this_turn(5, 10) is True
        assert board.has_moved_this_turn(6, 10) is False  # New position not tracked
        assert board.has_moved_this_turn(5, 11) is True

    def test_moved_units_cleared_on_end_turn(self):
        """Test that moved units are cleared when turn ends."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        board.make_turn_move(5, 10, 6, 10)
        assert board.get_moves_this_turn() == 1

        board.end_turn()
        assert board.get_moves_this_turn() == 0
        assert board.has_moved_this_turn(5, 10) is False

    def test_attack_tracking(self):
        """Test that attacks are tracked correctly."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        board.make_turn_attack(5, 12)

        assert board.get_attacks_this_turn() == 1
        assert board.can_attack_more() is False

    def test_attack_tracking_cleared_on_end_turn(self):
        """Test that attack counter is cleared when turn ends."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        board.make_turn_attack(5, 12)
        assert board.get_attacks_this_turn() == 1

        board.end_turn()
        assert board.get_attacks_this_turn() == 0
        assert board.can_attack_more() is True

    def test_turn_state_object(self):
        """Test TurnState object creation and serialization."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)

        state = get_turn_state(board)

        assert isinstance(state, TurnState)
        assert len(state.moved_units) == 1
        assert (5, 10) in state.moved_units
        assert state.attacks_this_turn == 0
        assert state.current_phase == 'M'

    def test_turn_state_dict_conversion(self):
        """Test TurnState to/from dict conversion."""
        state = TurnState(
            moved_units={(5, 10), (6, 11)},
            attacks_this_turn=1,
            current_phase='B',
            pending_retreats=[(7, 12)]
        )

        data = state.to_dict()
        assert data['moved_units'] == [(5, 10), (6, 11)]
        assert data['attacks_this_turn'] == 1
        assert data['current_phase'] == 'B'
        assert data['pending_retreats'] == [(7, 12)]

        restored = TurnState.from_dict(data)
        assert restored.moved_units == state.moved_units
        assert restored.attacks_this_turn == state.attacks_this_turn
        assert restored.current_phase == state.current_phase
        assert restored.pending_retreats == state.pending_retreats

    def test_turn_summary(self):
        """Test turn summary generation."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()
        board.make_turn_attack(5, 12)  # Valid attack with target

        summary = get_turn_summary(board)

        assert summary['turn_number'] == 1
        assert summary['current_player'] == 'NORTH'
        assert summary['current_phase'] == 'B'
        assert summary['moves_made'] == 1
        assert summary['moves_remaining'] == 4
        assert summary['attacks_made'] == 1
        assert summary['attacks_remaining'] == 0


class TestMoveValidation:
    """Test move validation according to turn rules."""

    def test_valid_move_in_movement_phase(self):
        """Test valid move in movement phase."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        assert board.validate_move(5, 10, 6, 10) is True

    def test_move_invalid_in_battle_phase(self):
        """Test move is invalid in battle phase."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.switch_to_battle_phase()

        assert board.validate_move(5, 10, 6, 10) is False

    def test_move_invalid_wrong_player(self):
        """Test move is invalid for wrong player's unit."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")

        assert board.validate_move(5, 10, 6, 10) is False

    def test_move_invalid_already_moved(self):
        """Test move is invalid if unit already moved."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)

        # Try to move same unit again - the unit is now at (6, 10) but we track
        # original positions, so (5, 10) is in _moved_units
        assert board.validate_move(6, 10, 7, 10) is False

    def test_move_invalid_exceeds_limit(self):
        """Test move is invalid after 5 moves."""
        board = Board()

        # Place 6 units
        for i in range(6):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")

        # Make 5 moves
        for i in range(5):
            board.make_turn_move(5, i, 6, i)

        # Try to move 6th unit
        assert board.validate_move(5, 5, 6, 5) is False

    def test_move_valid_fewer_than_5(self):
        """Test move is valid with fewer than 5 moves."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")

        board.make_turn_move(5, 10, 6, 10)
        assert board.can_move_more() is True
        assert board.validate_move(5, 11, 6, 11) is True

    def test_can_move_more(self):
        """Test can_move_more returns correct value."""
        board = Board()

        for i in range(5):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")
            assert board.can_move_more() is True
            board.make_turn_move(5, i, 6, i)

        assert board.can_move_more() is False


class TestAttackValidation:
    """Test attack validation according to turn rules."""

    def test_valid_attack_in_battle_phase(self):
        """Test valid attack in battle phase."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        assert board.validate_attack(5, 12) is True

    def test_attack_invalid_in_movement_phase(self):
        """Test attack is invalid in movement phase."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        assert board.validate_attack(5, 12) is False

    def test_attack_invalid_already_attacked(self):
        """Test attack is invalid if already attacked."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        board.make_turn_attack(5, 12)
        assert board.validate_attack(5, 12) is False

    def test_can_attack_more(self):
        """Test can_attack_more returns correct value."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        assert board.can_attack_more() is True
        board.make_turn_attack(5, 12)
        assert board.can_attack_more() is False


class TestPhaseManagement:
    """Test phase transitions and management."""

    def test_initial_phase_is_movement(self):
        """Test board starts in movement phase."""
        board = Board()
        assert board.current_phase == 'M'

    def test_switch_to_battle_phase(self):
        """Test switching to battle phase."""
        board = Board()
        board.switch_to_battle_phase()
        assert board.current_phase == 'B'

    def test_cannot_switch_from_battle_to_movement_directly(self):
        """Test cannot switch from battle to movement directly."""
        board = Board()
        board.switch_to_battle_phase()

        with pytest.raises(ValueError, match="not in movement phase"):
            board.switch_to_battle_phase()  # Already in battle

    def test_end_turn_resets_phase(self):
        """Test that end_turn resets phase to movement."""
        board = Board()
        board.switch_to_battle_phase()
        assert board.current_phase == 'B'

        board.end_turn()
        assert board.current_phase == 'M'

    def test_make_move_requires_movement_phase(self):
        """Test make_turn_move requires movement phase."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.switch_to_battle_phase()

        with pytest.raises(ValueError, match="Invalid turn move"):
            board.make_turn_move(5, 10, 6, 10)

    def test_make_attack_requires_battle_phase(self):
        """Test make_turn_attack requires battle phase."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        with pytest.raises(ValueError, match="Invalid turn attack"):
            board.make_turn_attack(5, 12)


class TestTurnSwitching:
    """Test turn switching logic."""

    def test_end_turn_switches_player(self):
        """Test that end_turn switches players."""
        board = Board()
        assert board.turn == 'NORTH'

        board.end_turn()
        assert board.turn == 'SOUTH'

        board.end_turn()
        assert board.turn == 'NORTH'

    def test_end_turn_increments_turn_number(self):
        """Test that end_turn increments turn number."""
        board = Board()
        assert board.turn_number == 1

        board.end_turn()
        assert board.turn_number == 2

        board.end_turn()
        assert board.turn_number == 3

    def test_end_turn_clears_moved_units(self):
        """Test that end_turn clears moved units."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)

        assert len(board._moved_unit_ids) == 1
        board.end_turn()
        assert len(board._moved_unit_ids) == 0

    def test_end_turn_clears_attack_counter(self):
        """Test that end_turn clears attack counter."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()
        board.make_turn_attack(5, 12)

        assert board._attacks_this_turn == 1
        board.end_turn()
        assert board._attacks_this_turn == 0


class TestRetreatResolution:
    """Test retreat resolution at turn start.

    NEW BEHAVIOR (0.1.5):
    - resolve_retreats() marks units as "must retreat" in _units_must_retreat
    - Player must actually move retreating unit
    - make_turn_move() clears retreat flag and adds to _moved_units
    - validate_move() blocks non-retreat moves when retreats pending
    """

    def test_retreat_marks_unit_as_must_retreat(self):
        """Test that retreat marks unit as must retreat (NEW in 0.1.5)."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # Simulate combat forcing retreat
        board.add_pending_retreat(5, 12)

        # Switch to SOUTH's turn
        board.end_turn()  # NORTH ends turn, SOUTH's turn begins

        # NEW: Unit is marked as must retreat, not moved
        assert board.is_unit_in_retreat(5, 12) is True
        assert board.has_moved_this_turn(5, 12) is False

    def test_retreat_captured_if_no_valid_move(self):
        """Test that unit is captured if no valid retreat."""
        board = Board()
        board.create_and_place_unit(0, 0, "INFANTRY", "SOUTH")  # Corner
        board.create_and_place_unit(0, 1, "INFANTRY", "NORTH")
        board.create_and_place_unit(1, 0, "INFANTRY", "NORTH")
        board.create_and_place_unit(1, 1, "INFANTRY", "NORTH")

        # Unit surrounded, no valid moves
        board.add_pending_retreat(0, 0)

        # Switch to SOUTH's turn
        board.end_turn()

        # Unit should be captured
        assert board.get_unit(0, 0) is None

    def test_multiple_retreats_resolved(self):
        """Test multiple retreats are resolved correctly (NEW behavior in 0.1.5)."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "CAVALRY", "SOUTH")

        board.add_pending_retreat(5, 10)
        board.add_pending_retreat(5, 12)

        # Switch to SOUTH's turn
        board.end_turn()

        # NEW: Both units marked as must retreat (NOT moved)
        assert board.is_unit_in_retreat(5, 10) is True
        assert board.is_unit_in_retreat(5, 12) is True
        assert board.has_moved_this_turn(5, 10) is False
        assert board.has_moved_this_turn(5, 12) is False

    def test_retreat_cleared_after_resolution(self):
        """Test that pending retreats are cleared after resolution."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        board.add_pending_retreat(5, 12)
        assert len(board.get_pending_retreats()) == 1

        # Switch to SOUTH's turn
        board.end_turn()

        assert len(board.get_pending_retreats()) == 0

    def test_retreat_move_clears_retreat_flag(self):
        """Test that moving retreating unit clears retreat flag (NEW in 0.1.5)."""
        board = Board()
        # Both players need units before end_turn to avoid victory detection
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # Add pending retreat
        board.add_pending_retreat(5, 12)
        assert len(board.get_pending_retreats()) == 1

        # Switch to SOUTH's turn - retreat should be resolved
        board.end_turn()

        # Unit should be marked as must retreat
        assert board.is_unit_in_retreat(5, 12) is True

        # Move unit to retreat
        board.make_turn_move(5, 12, 6, 12)

        # Retreat flag should be cleared after move
        assert board.is_unit_in_retreat(5, 12) is False
        # But unit should be marked as moved
        assert board.has_moved_this_turn(5, 12) is True

    def test_non_retreat_move_blocked_when_retreats_pending(self):
        """Test non-retreat moves are blocked when retreats pending (NEW in 0.1.5)."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")  # NORTH needs unit
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")  # Must retreat
        board.create_and_place_unit(5, 13, "CAVALRY", "SOUTH")  # Normal unit

        board.add_pending_retreat(5, 12)
        board.end_turn()  # SOUTH's turn, retreat resolved

        assert board.is_unit_in_retreat(5, 12) is True

        # Try to move non-retreating unit - should fail
        assert board.validate_move(5, 13, 6, 13) is False

        # Moving retreating unit should still work
        assert board.validate_move(5, 12, 6, 12) is True


class TestFullTurnSequence:
    """Test complete turn sequences."""

    def test_complete_turn_with_moves_and_attack(self):
        """Test complete turn with moves and attack."""
        board = Board()

        # NORTH's turn
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # Movement phase
        board.make_turn_move(5, 10, 6, 10)
        board.make_turn_move(5, 11, 6, 11)

        # Switch to battle
        board.switch_to_battle_phase()

        # Attack
        board.make_turn_attack(5, 12)

        # Verify state
        assert board.get_moves_this_turn() == 2
        assert board.get_attacks_this_turn() == 1
        assert board.turn == 'NORTH'

        # End turn
        board.end_turn()

        # Verify reset for SOUTH's turn
        # Note: If SOUTH had a pending retreat, it would be marked as moved
        assert board.turn == 'SOUTH'
        assert board.turn_number == 2
        assert board.current_phase == 'M'
        assert board.get_attacks_this_turn() == 0

    def test_turn_with_pass_attack(self):
        """Test turn with pass instead of attack."""
        board = Board()

        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)

        board.switch_to_battle_phase()
        board.pass_attack()

        assert board.get_attacks_this_turn() == 1

        board.end_turn()
        assert board.turn == 'SOUTH'

    def test_multiple_turns_sequence(self):
        """Test sequence of multiple turns."""
        board = Board()

        # Turn 1: NORTH
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(15, 10, "INFANTRY", "SOUTH")  # SOUTH needs unit before end_turn
        board.make_turn_move(5, 10, 6, 10)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Turn 1: SOUTH
        board.make_turn_move(15, 10, 14, 10)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # Turn 2: NORTH
        # NORTH already has unit at (6, 10) from turn 1
        board.make_turn_move(6, 10, 7, 10)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        # 3 end_turn() calls = turn 4
        assert board.turn_number == 4
        assert board.turn == 'SOUTH'

    def test_max_moves_turn(self):
        """Test turn with maximum 5 moves."""
        board = Board()

        # Place 6 units
        for i in range(6):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")

        # Make 5 moves
        for i in range(5):
            board.make_turn_move(5, i, 6, i)

        assert board.get_moves_this_turn() == 5
        assert board.can_move_more() is False

        # Cannot make 6th move
        with pytest.raises(ValueError, match="Invalid turn move"):
            board.make_turn_move(5, 5, 6, 5)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_board_turn(self):
        """Test turn on empty board."""
        board = Board()

        # Movement phase: pass (0 moves)
        board.switch_to_battle_phase()
        board.pass_attack()
        board.end_turn()

        assert board.turn == 'SOUTH'
        assert board.turn_number == 2

    def test_no_attackers_can_pass(self):
        """Test can pass when no attackers available."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        board.make_turn_move(5, 10, 6, 10)
        board.switch_to_battle_phase()

        # No attackers, can still pass
        board.pass_attack()
        assert board.get_attacks_this_turn() == 1

    def test_cannot_pass_in_movement_phase(self):
        """Test cannot pass during movement phase."""
        board = Board()

        with pytest.raises(ValueError, match="not in battle phase"):
            board.pass_attack()

    def test_cannot_pass_twice(self):
        """Test cannot pass twice in battle phase."""
        board = Board()
        board.switch_to_battle_phase()

        board.pass_attack()
        with pytest.raises(ValueError, match="already attacked"):
            board.pass_attack()

    def test_reset_turn_state(self):
        """Test reset_turn_state functionality."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)
        board.switch_to_battle_phase()
        board.pass_attack()

        assert board.get_moves_this_turn() == 1
        assert board.get_attacks_this_turn() == 1
        assert board.current_phase == 'B'

        board.reset_turn_state()

        assert board.get_moves_this_turn() == 0
        assert board.get_attacks_this_turn() == 0
        assert board.current_phase == 'M'
        assert board.turn_number == 1  # Not changed
        assert board.turn == 'NORTH'  # Not changed


class TestTurnCombatIntegration:
    """Test integration of turn management with combat system."""

    def test_capture_after_turn_attack(self):
        """Test that capture works correctly with turn management."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "RELAY", "SOUTH")  # Low defense
        board.switch_to_battle_phase()

        result = board.make_turn_attack(5, 12)

        assert result['outcome'].value == 'CAPTURE'
        assert board.get_unit(5, 12) is None
        assert board.get_attacks_this_turn() == 1

    def test_cannot_attack_after_capture(self):
        """Test cannot attack again after capture."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "RELAY", "SOUTH")
        board.create_and_place_unit(5, 13, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        board.make_turn_attack(5, 12)

        # Try to attack again
        with pytest.raises(ValueError, match="Invalid turn attack"):
            board.make_turn_attack(5, 13)


class TestTurnManagementUtilities:
    """Test turn management utility functions."""

    def test_can_end_turn_movement_phase(self):
        """Test can_end_turn in movement phase."""
        from pykrieg import can_end_turn
        board = Board()

        # Should always be able to end turn in movement phase
        assert can_end_turn(board) is True

        # Even after some moves
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)

        assert can_end_turn(board) is True

    def test_can_end_turn_battle_phase_before_attack(self):
        """Test can_end_turn in battle phase before attack."""
        from pykrieg import can_end_turn
        board = Board()
        board.switch_to_battle_phase()

        # Cannot end turn before attacking or passing
        assert can_end_turn(board) is False

    def test_can_end_turn_battle_phase_after_attack(self):
        """Test can_end_turn in battle phase after attack."""
        from pykrieg import can_end_turn
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()

        board.make_turn_attack(5, 12)

        assert can_end_turn(board) is True

    def test_validate_turn_action_move(self):
        """Test validate_turn_action with move action."""
        from pykrieg import validate_turn_action
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        assert validate_turn_action(board, 'move', from_row=5, from_col=10, to_row=6, to_col=10) is True

        board.switch_to_battle_phase()
        assert validate_turn_action(board, 'move', from_row=5, from_col=10, to_row=6, to_col=10) is False

    def test_validate_turn_action_attack(self):
        """Test validate_turn_action with attack action."""
        from pykrieg import validate_turn_action
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        assert validate_turn_action(board, 'attack', target_row=5, target_col=12) is False

        board.switch_to_battle_phase()
        assert validate_turn_action(board, 'attack', target_row=5, target_col=12) is True

    def test_validate_turn_action_pass(self):
        """Test validate_turn_action with pass action."""
        from pykrieg import validate_turn_action
        board = Board()

        assert validate_turn_action(board, 'pass') is False

        board.switch_to_battle_phase()
        assert validate_turn_action(board, 'pass') is True

        board.pass_attack()
        assert validate_turn_action(board, 'pass') is False

    def test_validate_turn_action_invalid_type(self):
        """Test validate_turn_action with invalid action type."""
        from pykrieg import validate_turn_action
        board = Board()

        assert validate_turn_action(board, 'invalid') is False

    def test_turn_state_serialization(self):
        """Test TurnState to_dict and from_dict."""
        from pykrieg import TurnState

        state = TurnState(
            moved_units={(5, 10), (6, 11)},
            attacks_this_turn=1,
            current_phase='B',
            pending_retreats=[(7, 12)]
        )

        data = state.to_dict()
        restored = TurnState.from_dict(data)

        assert restored.moved_units == state.moved_units
        assert restored.attacks_this_turn == state.attacks_this_turn
        assert restored.current_phase == state.current_phase
        assert restored.pending_retreats == state.pending_retreats

    def test_turn_summary_completeness(self):
        """Test get_turn_summary returns all required fields."""
        from pykrieg import get_turn_summary
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.make_turn_move(5, 10, 6, 10)
        board.switch_to_battle_phase()

        summary = get_turn_summary(board)

        required_fields = [
            'turn_number', 'current_player', 'current_phase',
            'moves_made', 'moves_remaining',
            'attacks_made', 'attacks_remaining', 'pending_retreats'
        ]

        for field in required_fields:
            assert field in summary

    def test_turn_summary_accuracy(self):
        """Test turn summary values are accurate."""
        from pykrieg import get_turn_summary
        board = Board()

        for i in range(3):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")

        for i in range(3):
            board.make_turn_move(5, i, 6, i)

        board.switch_to_battle_phase()

        summary = get_turn_summary(board)

        assert summary['turn_number'] == 1
        assert summary['current_player'] == 'NORTH'
        assert summary['current_phase'] == 'B'
        assert summary['moves_made'] == 3
        assert summary['moves_remaining'] == 2
        assert summary['attacks_made'] == 0
        assert summary['attacks_remaining'] == 1
        assert summary['pending_retreats'] == 0


class TestStateInvariants:
    """Test state invariants are maintained throughout operations."""

    def test_turn_number_never_decreases(self):
        """Test turn number never decreases."""
        board = Board()
        initial = board.turn_number

        for _ in range(10):
            board.end_turn()
            assert board.turn_number >= initial

    def test_turn_number_never_skips(self):
        """Test turn number increments by exactly 1."""
        board = Board()

        for i in range(10):
            board.end_turn()
            assert board.turn_number == i + 2

    def test_phase_is_valid(self):
        """Test phase is always 'M' or 'B'."""
        board = Board()

        valid_phases = ['M', 'B']

        assert board.current_phase in valid_phases

        board.switch_to_battle_phase()
        assert board.current_phase in valid_phases

        board.end_turn()
        assert board.current_phase in valid_phases

    def test_moves_counter_range(self):
        """Test moves counter is always 0-5."""
        board = Board()

        for i in range(10):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")

        for i in range(5):
            board.make_turn_move(5, i, 6, i)
            assert 0 <= board.get_moves_this_turn() <= 5

        board.end_turn()
        assert board.get_moves_this_turn() == 0

    def test_attack_counter_range(self):
        """Test attack counter is always 0 or 1."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        assert board.get_attacks_this_turn() == 0

        board.switch_to_battle_phase()
        board.make_turn_attack(5, 12)

        assert board.get_attacks_this_turn() == 1

        board.end_turn()
        assert board.get_attacks_this_turn() == 0

    def test_current_player_is_valid(self):
        """Test current player is always NORTH or SOUTH."""
        board = Board()
        valid_players = ['NORTH', 'SOUTH']

        assert board.turn in valid_players

        for _ in range(10):
            board.end_turn()
            assert board.turn in valid_players

    def test_end_turn_clears_per_turn_state(self):
        """Test end_turn clears all per-turn state."""
        board = Board()

        for i in range(3):
            board.create_and_place_unit(5, i, "INFANTRY", "NORTH")

        for i in range(3):
            board.make_turn_move(5, i, 6, i)

        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.switch_to_battle_phase()
        board.pass_attack()

        board.end_turn()

        assert len(board._moved_unit_ids) == 0
        assert board._attacks_this_turn == 0
        assert board.current_phase == 'M'

    def test_pending_retreats_contain_valid_positions(self):
        """Test pending retreats always contain valid positions."""
        board = Board()

        for i in range(3):
            board.create_and_place_unit(5, i, "INFANTRY", "SOUTH")
            board.add_pending_retreat(5, i)

        retreats = board.get_pending_retreats()

        for row, col in retreats:
            assert 0 <= row < 20
            assert 0 <= col < 25
