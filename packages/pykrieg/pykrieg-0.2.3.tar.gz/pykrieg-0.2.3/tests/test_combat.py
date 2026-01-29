"""Test suite for combat system in Pykrieg.

This module provides comprehensive tests for vector-based combat calculation,
cavalry charge mechanics, retreat tracking, and turn management.
"""

import pytest

from pykrieg import Board, CombatOutcome
from pykrieg.combat import (
    calculate_attack_power,
    calculate_combat,
    calculate_defense_power,
    can_attack,
    execute_capture,
    get_directions,
    get_line_units,
    is_adjacent,
    resolve_combat,
)


class TestDirections:
    """Test direction enumeration."""

    def test_get_directions_returns_8_directions(self):
        """Test get_directions returns 8 directions."""
        directions = get_directions()
        assert len(directions) == 8

    def test_get_directions_includes_cardinal(self):
        """Test get_directions includes cardinal directions."""
        directions = get_directions()
        assert (-1, 0) in directions  # Up
        assert (1, 0) in directions   # Down
        assert (0, -1) in directions  # Left
        assert (0, 1) in directions   # Right

    def test_get_directions_includes_diagonal(self):
        """Test get_directions includes diagonal directions."""
        directions = get_directions()
        assert (-1, -1) in directions  # Up-Left
        assert (-1, 1) in directions   # Up-Right
        assert (1, -1) in directions   # Down-Left
        assert (1, 1) in directions    # Down-Right


class TestLineUnits:
    """Test line unit detection."""

    def test_get_line_units_horizontal_right(self):
        """Test detecting units to the right."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "CANNON", "SOUTH")

        units = get_line_units(board, 5, 10, (0, 1), "NORTH")
        assert len(units) == 1
        assert units[0] == (5, 11, board.get_unit(5, 11))

    def test_get_line_units_horizontal_left(self):
        """Test detecting units to the left."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")

        units = get_line_units(board, 5, 12, (0, -1), "NORTH")
        assert len(units) == 1
        assert units[0] == (5, 11, board.get_unit(5, 11))

    def test_get_line_units_vertical_down(self):
        """Test detecting units below."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 10, "CAVALRY", "NORTH")
        board.create_and_place_unit(7, 10, "CANNON", "NORTH")

        units = get_line_units(board, 5, 10, (1, 0), "NORTH")
        assert len(units) == 2

    def test_get_line_units_vertical_up(self):
        """Test detecting units above."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(9, 10, "CAVALRY", "NORTH")

        units = get_line_units(board, 10, 10, (-1, 0), "NORTH")
        assert len(units) == 1

    def test_get_line_units_diagonal(self):
        """Test detecting units on diagonal."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(7, 12, "CANNON", "NORTH")

        units = get_line_units(board, 5, 10, (1, 1), "NORTH")
        assert len(units) == 2

    def test_get_line_units_filters_by_owner(self):
        """Test get_line_units filters by owner."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 13, "CANNON", "SOUTH")

        north_units = get_line_units(board, 5, 10, (0, 1), "NORTH")
        south_units = get_line_units(board, 5, 10, (0, 1), "SOUTH")

        assert len(north_units) == 1
        assert len(south_units) == 2

    def test_get_line_units_empty_line(self):
        """Test get_line_units returns empty list for empty line."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        units = get_line_units(board, 5, 10, (0, 1), "NORTH")
        assert len(units) == 0

    def test_get_line_units_stops_at_boundary(self):
        """Test get_line_units stops at board boundary."""
        board = Board()
        board.create_and_place_unit(19, 10, "INFANTRY", "NORTH")

        units = get_line_units(board, 19, 10, (1, 0), "NORTH")
        assert len(units) == 0  # No squares below row 19

    def test_get_line_units_all_directions(self):
        """Test get_line_units works in all 8 directions."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(9, 12, "CAVALRY", "NORTH")  # Up
        board.create_and_place_unit(11, 12, "CANNON", "NORTH")  # Down
        board.create_and_place_unit(10, 11, "INFANTRY", "NORTH")  # Left
        board.create_and_place_unit(10, 13, "CAVALRY", "NORTH")  # Right
        board.create_and_place_unit(9, 11, "CANNON", "NORTH")  # Up-Left
        board.create_and_place_unit(9, 13, "INFANTRY", "NORTH")  # Up-Right
        board.create_and_place_unit(11, 11, "CAVALRY", "NORTH")  # Down-Left
        board.create_and_place_unit(11, 13, "CANNON", "NORTH")  # Down-Right

        directions = get_directions()
        for direction in directions:
            units = get_line_units(board, 10, 12, direction, "NORTH")
            assert len(units) == 1


class TestAdjacency:
    """Test adjacency detection."""

    def test_adjacent_horizontal(self):
        """Test horizontal adjacency."""
        assert is_adjacent(5, 10, 5, 11) is True
        assert is_adjacent(5, 10, 5, 9) is True

    def test_adjacent_vertical(self):
        """Test vertical adjacency."""
        assert is_adjacent(5, 10, 6, 10) is True
        assert is_adjacent(5, 10, 4, 10) is True

    def test_adjacent_diagonal(self):
        """Test diagonal adjacency."""
        assert is_adjacent(5, 10, 6, 11) is True
        assert is_adjacent(5, 10, 6, 9) is True
        assert is_adjacent(5, 10, 4, 11) is True
        assert is_adjacent(5, 10, 4, 9) is True

    def test_not_adjacent_same_square(self):
        """Test same square is not adjacent."""
        assert is_adjacent(5, 10, 5, 10) is False

    def test_not_adjacent_distance_2(self):
        """Test distance 2 is not adjacent."""
        assert is_adjacent(5, 10, 5, 12) is False
        assert is_adjacent(5, 10, 7, 10) is False
        assert is_adjacent(5, 10, 7, 12) is False


class TestAttackPowerCalculation:
    """Test attack power calculation."""

    def test_single_infantry_attack(self):
        """Test single Infantry contributes Attack 4."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 4

    def test_single_cavalry_attack(self):
        """Test single Cavalry contributes Attack 4."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 4

    def test_single_cannon_attack(self):
        """Test single Cannon contributes Attack 5."""
        board = Board()
        board.create_and_place_unit(5, 10, "CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 5

    def test_multiple_units_attack(self):
        """Test multiple attacking units sum their attack."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 11  # 4 (Infantry) + 7 (Cavalry with charge)

    def test_units_in_all_directions(self):
        """Test units in all 8 directions contribute."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")  # Target

        # Surround with NORTH units
        board.create_and_place_unit(9, 12, "INFANTRY", "NORTH")   # Up
        board.create_and_place_unit(11, 12, "INFANTRY", "NORTH")  # Down
        board.create_and_place_unit(10, 11, "INFANTRY", "NORTH")  # Left
        board.create_and_place_unit(10, 13, "INFANTRY", "NORTH")  # Right
        board.create_and_place_unit(9, 11, "INFANTRY", "NORTH")  # Up-Left
        board.create_and_place_unit(9, 13, "INFANTRY", "NORTH")  # Up-Right
        board.create_and_place_unit(11, 11, "INFANTRY", "NORTH")  # Down-Left
        board.create_and_place_unit(11, 13, "INFANTRY", "NORTH")  # Down-Right

        attack = calculate_attack_power(board, 10, 12, "NORTH")
        assert attack == 32  # 8 Infantry × 4 Attack = 32

    def test_relay_no_attack(self):
        """Test Relay contributes 0 attack."""
        board = Board()
        board.create_and_place_unit(5, 10, "RELAY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 0

    def test_arsenal_no_attack(self):
        """Test Arsenal contributes 0 attack."""
        board = Board()
        board.set_arsenal(5, 10, "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 0

    def test_cavalry_charge_bonus(self):
        """Test adjacent Cavalry gets +3 attack bonus."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 7  # 4 + 3 bonus

    def test_non_adjacent_cavalry_no_bonus(self):
        """Test non-adjacent Cavalry gets no bonus."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 11, "INFANTRY", "NORTH")  # Between them

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 8  # 4 (Cavalry, no bonus) + 4 (Infantry)

    def test_multiple_cavalry_charge(self):
        """Test multiple adjacent Cavalry all get bonus."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 13, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 14  # (4+3) + (4+3) = 14

    def test_four_cavalry_charge_stack(self):
        """Test 4 Cavalry can stack charge bonus."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # 4 Cavalry in line from west (same direction)
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")  # Adjacent
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")  # Stacking
        board.create_and_place_unit(5, 9, "CAVALRY", "NORTH")   # Stacking
        board.create_and_place_unit(5, 8, "CAVALRY", "NORTH")   # Stacking

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 28  # 4 × (4+3) = 28

    def test_cavalry_charge_stopping_at_gap(self):
        """Test charge stacking stops at gap."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # Cavalry with gap in between
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")  # Adjacent, triggers charge
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")  # Stacking (consecutive)
        board.create_and_place_unit(5, 9, "CAVALRY", "NORTH")   # Consecutive (no gap)

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        # 3 cavalry in charge stack: 3 × (4+3) = 21
        assert attack == 21

    def test_cavalry_charge_multiple_directions(self):
        """Test charge stacking works in multiple directions."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # West: 2 cavalry (adjacent + stacking)
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # East: 3 cavalry (adjacent + 2 stacking)
        board.create_and_place_unit(5, 13, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 14, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 15, "CAVALRY", "NORTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 35  # 2×(4+3) + 3×(4+3) = 14 + 21 = 35

    def test_cavalry_no_charge_first_not_adjacent(self):
        """Test no charge if first cavalry not adjacent."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        # Cavalry not adjacent (cavalry range is 2)
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")  # Distance 2, within range

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        # Single cavalry within range but not adjacent: 1 × 4 = 4 (no charge bonus)
        assert attack == 4

    def test_infantry_no_charge_bonus(self):
        """Test Infantry does not get charge bonus."""
        board = Board()
        board.create_and_place_unit(5, 11, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 4  # No bonus for Infantry

    def test_cannon_no_charge_bonus(self):
        """Test Cannon does not get charge bonus."""
        board = Board()
        board.create_and_place_unit(5, 11, "CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 5  # No bonus for Cannon

    def test_mixed_units_attack(self):
        """Test mixed unit types sum correctly."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")  # 4
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")   # 4+3=7 (adjacent)
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")  # Target

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 11  # 4 + 7

    def test_no_attackers(self):
        """Test no attackers results in 0 attack power."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 0


class TestDefensePowerCalculation:
    """Test defense power calculation."""

    def test_single_infantry_defense(self):
        """Test single Infantry contributes Defense 6."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "NORTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 6

    def test_single_cavalry_defense(self):
        """Test single Cavalry contributes Defense 5."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 5

    def test_single_cannon_defense(self):
        """Test single Cannon contributes Defense 8."""
        board = Board()
        board.create_and_place_unit(5, 10, "CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 8

    def test_multiple_units_defense(self):
        """Test multiple defending units sum their defense."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 11  # 6 + 5

    def test_units_in_all_directions(self):
        """Test units in all 8 directions contribute."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")  # Target

        # Surround with NORTH units
        board.create_and_place_unit(9, 12, "INFANTRY", "NORTH")   # Up
        board.create_and_place_unit(11, 12, "INFANTRY", "NORTH")  # Down
        board.create_and_place_unit(10, 11, "INFANTRY", "NORTH")  # Left
        board.create_and_place_unit(10, 13, "INFANTRY", "NORTH")  # Right
        board.create_and_place_unit(9, 11, "INFANTRY", "NORTH")  # Up-Left
        board.create_and_place_unit(9, 13, "INFANTRY", "NORTH")  # Up-Right
        board.create_and_place_unit(11, 11, "INFANTRY", "NORTH")  # Down-Left
        board.create_and_place_unit(11, 13, "INFANTRY", "NORTH")  # Down-Right

        defense = calculate_defense_power(board, 10, 12, "NORTH")
        assert defense == 48  # 8 Infantry × 6 Defense = 48

    def test_relay_minimal_defense(self):
        """Test Relay contributes Defense 1 at target square."""
        board = Board()
        board.create_and_place_unit(5, 12, "RELAY", "NORTH")  # Relay at target

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        # Relay at target contributes defense 1 (always, even with range 0)
        assert defense == 1

    def test_arsenal_no_defense(self):
        """Test Arsenal contributes 0 defense."""
        board = Board()
        board.set_arsenal(5, 10, "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 0

    def test_no_defenders(self):
        """Test no defenders results in 0 defense power."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 0


class TestCombatResolution:
    """Test combat outcome resolution."""

    def test_attack_less_than_defense_fail(self):
        """Test Attack < Defense results in FAIL."""
        assert resolve_combat(10, 15) == CombatOutcome.FAIL
        assert resolve_combat(0, 5) == CombatOutcome.FAIL

    def test_attack_equal_defense_fail(self):
        """Test Attack == Defense results in FAIL."""
        assert resolve_combat(10, 10) == CombatOutcome.FAIL
        assert resolve_combat(5, 5) == CombatOutcome.FAIL

    def test_attack_defense_plus_one_retreat(self):
        """Test Attack = Defense + 1 results in RETREAT."""
        assert resolve_combat(11, 10) == CombatOutcome.RETREAT
        assert resolve_combat(6, 5) == CombatOutcome.RETREAT
        assert resolve_combat(1, 0) == CombatOutcome.RETREAT

    def test_attack_defense_plus_two_capture(self):
        """Test Attack ≥ Defense + 2 results in CAPTURE."""
        assert resolve_combat(12, 10) == CombatOutcome.CAPTURE
        assert resolve_combat(15, 10) == CombatOutcome.CAPTURE
        assert resolve_combat(20, 0) == CombatOutcome.CAPTURE

    def test_all_outcomes(self):
        """Test all three possible outcomes."""
        assert resolve_combat(8, 10) == CombatOutcome.FAIL
        assert resolve_combat(11, 10) == CombatOutcome.RETREAT
        assert resolve_combat(12, 10) == CombatOutcome.CAPTURE


class TestFullCombatCalculation:
    """Test complete combat calculation."""

    def test_complete_combat_fail(self):
        """Test complete combat that fails."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 4
        assert result['defense_power'] == 6
        assert result['outcome'] == CombatOutcome.FAIL
        assert len(result['attack_units']) == 1
        assert len(result['defense_units']) == 0

    def test_complete_combat_retreat(self):
        """Test complete combat that forces retreat."""
        board = Board()
        board.create_and_place_unit(4, 12, "INFANTRY", "NORTH")  # Attack 4 (north)
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")   # Attack 7 (adjacent)
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")  # Defense 6

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 11  # 4 + 7
        assert result['defense_power'] == 6
        assert result['outcome'] == CombatOutcome.CAPTURE

    def test_complete_combat_capture(self):
        """Test complete combat that captures."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")   # Attack 7 (charge)
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")  # Defense 6

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 7
        assert result['defense_power'] == 6
        assert result['outcome'] == CombatOutcome.RETREAT

    def test_complete_combat_with_defenders(self):
        """Test complete combat with defending units."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 13, "CAVALRY", "SOUTH")

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 4
        assert result['defense_power'] == 11  # 6 + 5
        assert result['outcome'] == CombatOutcome.FAIL

    def test_complete_combat_complex(self):
        """Test complex combat scenario."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")  # Target, defense 6

        # Attackers
        board.create_and_place_unit(9, 12, "INFANTRY", "NORTH")   # 4
        board.create_and_place_unit(11, 12, "CAVALRY", "NORTH")  # 7 (adjacent)
        board.create_and_place_unit(10, 11, "CAVALRY", "NORTH")  # 7 (adjacent)

        # Defenders (target at 10,12 + supporting units)
        board.create_and_place_unit(10, 13, "INFANTRY", "SOUTH")  # 6 (supporting)
        board.create_and_place_unit(9, 11, "CANNON", "SOUTH")    # 8 (supporting)
        board.create_and_place_unit(11, 13, "CANNON", "SOUTH")    # 8 (supporting)

        result = calculate_combat(board, 10, 12, "NORTH", "SOUTH")

        # Attack: 4 + 7 + 7 = 18
        # Defense: 6 (target) + 6 + 8 + 8 = 28
        assert result['attack_power'] == 18
        assert result['defense_power'] == 28
        assert result['outcome'] == CombatOutcome.FAIL


class TestCaptureExecution:
    """Test capture execution."""

    def test_execute_capture_removes_unit(self):
        """Test execute_capture removes unit from board."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        captured = execute_capture(board, 5, 12)

        assert captured.unit_type == "INFANTRY"
        assert board.get_unit(5, 12) is None

    def test_execute_capture_returns_unit(self):
        """Test execute_capture returns captured unit."""
        board = Board()
        board.create_and_place_unit(5, 12, "CAVALRY", "SOUTH")

        captured = execute_capture(board, 5, 12)

        assert captured.unit_type == "CAVALRY"
        assert captured.owner == "SOUTH"

    def test_execute_capture_empty_square_error(self):
        """Test execute_capture raises error on empty square."""
        board = Board()

        with pytest.raises(ValueError, match="No unit to capture"):
            execute_capture(board, 5, 12)


class TestCanAttack:
    """Test can_attack function."""

    def test_can_attack_with_units(self):
        """Test can_attack returns True when attacker has units."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        assert can_attack(board, 5, 12, "NORTH") is True

    def test_can_attack_without_units(self):
        """Test can_attack returns False when attacker has no units."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        assert can_attack(board, 5, 12, "NORTH") is False

    def test_can_attack_multiple_directions(self):
        """Test can_attack works with units in multiple directions."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "NORTH")  # Up
        board.create_and_place_unit(15, 12, "CAVALRY", "NORTH")  # Down

        assert can_attack(board, 10, 12, "NORTH") is True


class TestRetreatTracking:
    """Test retreat tracking functionality."""

    def test_add_pending_retreat(self):
        """Test adding a unit to pending retreats."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        board.add_pending_retreat(5, 12)

        assert board.has_pending_retreat(5, 12) is True
        assert (5, 12) in board.get_pending_retreats()

    def test_add_multiple_pending_retreats(self):
        """Test adding multiple units to pending retreats."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "CAVALRY", "SOUTH")
        board.create_and_place_unit(6, 10, "CANNON", "SOUTH")

        board.add_pending_retreat(5, 10)
        board.add_pending_retreat(5, 12)
        board.add_pending_retreat(6, 10)

        retreats = board.get_pending_retreats()
        assert len(retreats) == 3
        assert (5, 10) in retreats
        assert (5, 12) in retreats
        assert (6, 10) in retreats

    def test_duplicate_retreat_prevented(self):
        """Test that duplicate retreat entries are prevented."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        board.add_pending_retreat(5, 12)
        board.add_pending_retreat(5, 12)  # Try to add again
        board.add_pending_retreat(5, 12)  # And again

        retreats = board.get_pending_retreats()
        assert len(retreats) == 1  # Only one entry
        assert retreats.count((5, 12)) == 1

    def test_clear_pending_retreats(self):
        """Test clearing all pending retreats."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "CAVALRY", "SOUTH")

        board.add_pending_retreat(5, 10)
        board.add_pending_retreat(5, 12)
        assert len(board.get_pending_retreats()) == 2

        board.clear_pending_retreats()
        assert len(board.get_pending_retreats()) == 0
        assert board.has_pending_retreat(5, 10) is False
        assert board.has_pending_retreat(5, 12) is False

    def test_has_pending_retreat(self):
        """Test has_pending_retreat returns correct boolean."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(5, 12, "CAVALRY", "SOUTH")

        assert board.has_pending_retreat(5, 10) is False
        assert board.has_pending_retreat(5, 12) is False

        board.add_pending_retreat(5, 10)

        assert board.has_pending_retreat(5, 10) is True
        assert board.has_pending_retreat(5, 12) is False

    def test_add_retreat_invalid_coordinates(self):
        """Test adding retreat with invalid coordinates raises error."""
        board = Board()

        with pytest.raises(ValueError, match="Invalid coordinates"):
            board.add_pending_retreat(-1, 0)

        with pytest.raises(ValueError, match="Invalid coordinates"):
            board.add_pending_retreat(20, 0)

        with pytest.raises(ValueError, match="Invalid coordinates"):
            board.add_pending_retreat(0, -1)

        with pytest.raises(ValueError, match="Invalid coordinates"):
            board.add_pending_retreat(0, 25)

    def test_add_retreat_empty_square(self):
        """Test adding retreat on empty square raises error."""
        board = Board()

        with pytest.raises(ValueError, match="No unit at"):
            board.add_pending_retreat(5, 12)

    def test_get_pending_retreats_returns_list(self):
        """Test that get_pending_retreats returns a list, not reference."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        board.add_pending_retreat(5, 12)
        retreats1 = board.get_pending_retreats()
        retreats2 = board.get_pending_retreats()

        # Modifying returned list shouldn't affect internal state
        retreats1.append((0, 0))
        assert (0, 0) not in board.get_pending_retreats()
        assert len(retreats2) == 1


class TestTurnTracking:
    """Test turn number and phase tracking."""

    def test_turn_number_initialization(self):
        """Test turn number initializes to 1."""
        board = Board()
        assert board.turn_number == 1

    def test_turn_number_setter(self):
        """Test setting turn number."""
        board = Board()
        board.turn_number = 42
        assert board.turn_number == 42

    def test_current_phase_initialization(self):
        """Test current phase initializes to MOVEMENT."""
        board = Board()
        assert board.current_phase == "M"  # Using constant

    def test_current_phase_setter(self):
        """Test setting current phase."""
        board = Board()
        board.current_phase = "B"
        assert board.current_phase == "B"

    def test_increment_turn(self):
        """Test increment_turn increments and switches player."""
        board = Board()
        initial_turn = board.turn_number
        initial_player = board.turn

        board.increment_turn()

        assert board.turn_number == initial_turn + 1
        assert board.turn != initial_player
        assert board.current_phase == "M"  # Resets to movement

    def test_multiple_increment_turn(self):
        """Test multiple turn increments."""
        board = Board()

        for i in range(5):
            board.increment_turn()
            assert board.turn_number == i + 2

    def test_phase_persistence_within_turn(self):
        """Test phase persists when not incrementing turn."""
        board = Board()
        board.current_phase = "B"

        assert board.current_phase == "B"

        # Phase should remain B until turn is incremented
        board.turn_number = 10
        assert board.current_phase == "B"


class TestSwiftUnits:
    """Test Swift Cannon and Swift Relay units."""

    def test_swift_cannon_attack_contribution(self):
        """Test Swift Cannon contributes Attack 5."""
        board = Board()
        board.create_and_place_unit(5, 10, "SWIFT_CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 5  # Swift Cannon Attack = 5

    def test_swift_cannon_defense_contribution(self):
        """Test Swift Cannon contributes Defense 8."""
        board = Board()
        board.create_and_place_unit(5, 10, "SWIFT_CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        assert defense == 8  # Swift Cannon Defense = 8

    def test_swift_relay_no_attack_contribution(self):
        """Test Swift Relay contributes 0 attack."""
        board = Board()
        board.create_and_place_unit(5, 10, "SWIFT_RELAY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 0

    def test_swift_relay_defense_contribution(self):
        """Test Swift Relay contributes Defense 1 at target square."""
        board = Board()
        board.create_and_place_unit(5, 12, "SWIFT_RELAY", "NORTH")  # Swift Relay at target

        defense = calculate_defense_power(board, 5, 12, "NORTH")
        # Swift Relay at target contributes defense 1 (always, even with range 0)
        assert defense == 1

    def test_swift_units_no_charge_bonus(self):
        """Test Swift units don't get cavalry charge bonus."""
        board = Board()
        board.create_and_place_unit(5, 11, "SWIFT_CANNON", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        attack = calculate_attack_power(board, 5, 12, "NORTH")
        assert attack == 5  # No charge bonus for Swift Cannon


class TestBoardCombatMethods:
    """Test Board convenience methods for combat."""

    def test_board_calculate_combat(self):
        """Test Board.calculate_combat wrapper."""
        board = Board()
        board.create_and_place_unit(5, 11, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        result = board.calculate_combat(5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 7
        assert result['defense_power'] == 6
        assert result['outcome'] == CombatOutcome.RETREAT

    def test_board_execute_capture(self):
        """Test Board.execute_capture wrapper."""
        board = Board()
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        captured = board.execute_capture(5, 12)

        assert captured.unit_type == "INFANTRY"
        assert board.get_unit(5, 12) is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_combat_at_corner(self):
        """Test combat calculation at board corner."""
        board = Board()
        board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
        board.create_and_place_unit(0, 1, "CAVALRY", "SOUTH")

        result = calculate_combat(board, 0, 0, "SOUTH", "NORTH")

        assert result['attack_power'] == 7  # Cavalry adjacent gets +3 bonus
        assert result['defense_power'] == 6

    def test_combat_at_edge(self):
        """Test combat calculation at board edge."""
        board = Board()
        board.create_and_place_unit(0, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(1, 12, "CAVALRY", "SOUTH")

        result = calculate_combat(board, 0, 12, "SOUTH", "NORTH")

        assert result['attack_power'] == 7  # Adjacent Cavalry
        assert result['defense_power'] == 6

    def test_combat_empty_target(self):
        """Test combat calculation on empty square."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 4
        assert result['defense_power'] == 0

    def test_zero_attack_power(self):
        """Test attack power of 0 (no attackers or Relays only)."""
        board = Board()
        board.create_and_place_unit(5, 11, "RELAY", "NORTH")
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")
        assert result['attack_power'] == 0
        assert result['outcome'] == CombatOutcome.FAIL

    def test_zero_defense_power(self):
        """Test defense power of 0 (Arsenal or no defenders)."""
        board = Board()
        board.create_and_place_unit(5, 11, "INFANTRY", "NORTH")
        board.set_arsenal(5, 12, "SOUTH")

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")
        assert result['defense_power'] == 0
        assert result['outcome'] == CombatOutcome.CAPTURE

    def test_maximum_cavalry_charge_28(self):
        """Test maximum cavalry charge bonus equals 28."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")  # Target

        # 4 Cavalry in one direction, all getting charge bonus
        board.create_and_place_unit(10, 11, "CAVALRY", "NORTH")  # Adjacent
        board.create_and_place_unit(10, 10, "CAVALRY", "NORTH")  # Stacking
        board.create_and_place_unit(10, 9, "CAVALRY", "NORTH")   # Stacking
        board.create_and_place_unit(10, 8, "CAVALRY", "NORTH")   # Stacking

        attack = calculate_attack_power(board, 10, 12, "NORTH")
        assert attack == 28  # 4 × (4+3) = 28

    def test_outcome_boundary_conditions(self):
        """Test combat outcomes at threshold boundaries."""
        # Attack = Defense - 1: FAIL
        assert resolve_combat(9, 10) == CombatOutcome.FAIL

        # Attack = Defense: FAIL
        assert resolve_combat(10, 10) == CombatOutcome.FAIL

        # Attack = Defense + 1: RETREAT
        assert resolve_combat(11, 10) == CombatOutcome.RETREAT

        # Attack = Defense + 2: CAPTURE
        assert resolve_combat(12, 10) == CombatOutcome.CAPTURE

        # Attack = Defense + 100: CAPTURE
        assert resolve_combat(110, 10) == CombatOutcome.CAPTURE


class TestIntegrationScenarios:
    """Test combat in realistic game scenarios."""

    def test_surround_and_capture(self):
        """Test surrounding a unit results in capture."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "SOUTH")  # Defense 6

        # Surround with 4 Cavalry (all adjacent)
        board.create_and_place_unit(9, 12, "CAVALRY", "NORTH")   # 7
        board.create_and_place_unit(11, 12, "CAVALRY", "NORTH")  # 7
        board.create_and_place_unit(10, 11, "CAVALRY", "NORTH")  # 7
        board.create_and_place_unit(10, 13, "CAVALRY", "NORTH")  # 7

        result = calculate_combat(board, 10, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 28
        assert result['defense_power'] == 6
        assert result['outcome'] == CombatOutcome.CAPTURE

    def test_attack_weak_defense(self):
        """Test attacking weakly defended target."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")  # Attack 4 (not adjacent)
        board.create_and_place_unit(5, 12, "RELAY", "SOUTH")     # Defense 1

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 4  # Cavalry not adjacent, no charge
        assert result['defense_power'] == 1
        assert result['outcome'] == CombatOutcome.CAPTURE

    def test_defensive_line(self):
        """Test strong defensive line holds attack."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")   # Attack 4
        board.create_and_place_unit(5, 12, "INFANTRY", "SOUTH")   # Defense 6
        board.create_and_place_unit(5, 13, "CANNON", "SOUTH")     # Defense 8
        board.create_and_place_unit(5, 14, "CANNON", "SOUTH")     # Defense 8

        result = calculate_combat(board, 5, 12, "NORTH", "SOUTH")

        assert result['attack_power'] == 4
        assert result['defense_power'] == 22  # 6 + 8 + 8
        assert result['outcome'] == CombatOutcome.FAIL
