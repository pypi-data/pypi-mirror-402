"""Tests for special rules and edge cases from 0.2.3.

This module tests special rules including:
- Cavalry charge restrictions (cannot attack fortress/pass)
- Fortress occupation neutrality rules
- Other edge cases from the roadmap
"""


from pykrieg.board import Board
from pykrieg.combat import calculate_combat, preview_combat
from pykrieg.constants import (
    PLAYER_NORTH,
    PLAYER_SOUTH,
    TERRAIN_ARSENAL,
    TERRAIN_FORTRESS,
    TERRAIN_MOUNTAIN_PASS,
)


class TestCavalryChargeRestrictions:
    """Test cavalry charge restrictions against terrain."""

    def test_cavalry_can_charge_normal_square(self):
        """Cavalry charge bonus works on normal terrain."""
        board = Board()

        # Attacking cavalry adjacent to target
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Cavalry gets +3 bonus when charging (4 + 3 = 7)
        # Infantry defense = 6
        assert result['attack_power'] == 7  # 4 + 3 charge bonus
        assert result['defense_power'] == 6

    def test_cavalry_cannot_charge_unit_in_fortress(self):
        """Cavalry charge bonus should NOT apply when attacking unit in fortress."""
        board = Board()

        # Set fortress terrain
        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        # Attacking cavalry adjacent to fortress
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # If charge restriction is implemented:
        # Cavalry attack = 4 (no +3 bonus)
        # Infantry defense = 6 + fortress bonus 4 = 10
        # Attack = 4, Defense = 10

        # If charge is NOT restricted:
        # Cavalry attack = 4 + 3 = 7
        # Infantry defense = 6 + 4 = 10

        # This test will fail if charge restriction is NOT implemented
        # Expected: attack_power == 4 (no bonus)
        # Actual implementation might have attack_power == 7 (with bonus)
        assert result['attack_power'] == 4, (
            "Cavalry charge bonus should NOT apply when attacking unit in fortress"
        )
        assert result['defense_power'] == 10  # 6 + 4 fortress bonus

    def test_cavalry_cannot_charge_unit_in_mountain_pass(self):
        """Cavalry charge bonus should NOT apply when attacking unit in mountain pass."""
        board = Board()

        # Set mountain pass terrain
        board.set_terrain(10, 10, TERRAIN_MOUNTAIN_PASS)

        # Attacking cavalry adjacent to pass
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # If charge restriction is implemented:
        # Cavalry attack = 4 (no +3 bonus)
        # Infantry defense = 6 + pass bonus 2 = 8

        # If charge is NOT restricted:
        # Cavalry attack = 4 + 3 = 7
        # Infantry defense = 6 + 2 = 8

        # This test will fail if charge restriction is NOT implemented
        # Expected: attack_power == 4 (no bonus)
        assert result['attack_power'] == 4, (
            "Cavalry charge bonus should NOT apply when attacking unit in mountain pass"
        )
        assert result['defense_power'] == 8  # 6 + 2 pass bonus

    def test_multiple_cavalry_cannot_charge_fortress(self):
        """Multiple cavalry should NOT get charge bonuses against fortress."""
        board = Board()

        # Set fortress terrain
        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        # Three charging cavalry in line
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(8, 8, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(7, 7, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # If charge restriction is implemented:
        # Only first two cavalry are within range 2 = 4 each = 8 total (no +3 bonuses)
        # Third cavalry is at distance 3, outside normal range

        # If charge is NOT restricted:
        # All three cavalry would be in charge stack = 4 + 3 each = 21 total
        # (charge stack extends to range 4)

        # This test will fail if charge restriction is NOT implemented
        assert result['attack_power'] == 8, (
            "Multiple cavalry should NOT get charge bonuses against fortress"
        )

    def test_cavalry_can_charge_normal_terrain_adjacent_to_fortress(self):
        """Cavalry can still charge if target is NOT on fortress."""
        board = Board()

        # Fortress nearby but not at target
        board.set_terrain(10, 11, TERRAIN_FORTRESS)

        # Attacking cavalry adjacent to normal square
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Charge bonus should still work on normal terrain
        assert result['attack_power'] == 7  # 4 + 3 charge bonus

    def test_preview_combat_shows_cavalry_charge_restriction(self):
        """preview_combat should reflect cavalry charge restrictions."""
        board = Board()

        # Set fortress terrain
        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        # Cavalry adjacent to fortress
        board.create_and_place_unit(9, 9, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Preview combat
        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Should show no charging cavalry
        assert preview['charging_cavalry_count'] == 0, (
            "preview_combat should show 0 charging cavalry against fortress"
        )

    def test_non_charging_cavalry_normal_attack(self):
        """Non-attacking cavalry should have normal attack power."""
        board = Board()

        # Set fortress terrain
        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        # Cavalry NOT adjacent (2 squares away)
        board.create_and_place_unit(8, 8, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # Calculate combat
        result = calculate_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Non-attacking cavalry = normal attack power (4)
        # Should not be affected by charge restriction since not charging anyway
        assert result['attack_power'] == 4


class TestFortressOccupationNeutrality:
    """Test fortress occupation neutrality rules."""

    def test_north_can_occupy_fortress_in_south_territory(self):
        """North unit can move into fortress in South territory."""
        board = Board()

        # Place fortress in South territory
        board.set_terrain(12, 10, TERRAIN_FORTRESS)

        # North unit moves into fortress
        board.create_and_place_unit(11, 10, "INFANTRY", PLAYER_NORTH)

        # Should be able to move into fortress
        from pykrieg.movement import is_valid_move
        assert is_valid_move(board, 11, 10, 12, 10, PLAYER_NORTH), (
            "North should be able to occupy fortress in South territory"
        )

    def test_south_can_occupy_fortress_in_north_territory(self):
        """South unit can move into fortress in North territory."""
        board = Board()

        # Place fortress in North territory
        board.set_terrain(8, 10, TERRAIN_FORTRESS)

        # South unit moves into fortress
        board.create_and_place_unit(9, 10, "INFANTRY", PLAYER_SOUTH)

        # Should be able to move into fortress
        from pykrieg.movement import is_valid_move
        assert is_valid_move(board, 9, 10, 8, 10, PLAYER_SOUTH), (
            "South should be able to occupy fortress in North territory"
        )

    def test_both_players_can_occupy_same_fortress_at_different_times(self):
        """Both players can occupy fortress (not simultaneously)."""
        board = Board()

        # Place fortress
        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        # North unit occupies it
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        # Remove North unit
        board.clear_square(10, 10)

        # South unit should be able to occupy it now
        board.create_and_place_unit(9, 10, "INFANTRY", PLAYER_SOUTH)
        from pykrieg.movement import is_valid_move
        assert is_valid_move(board, 9, 10, 10, 10, PLAYER_SOUTH), (
            "South should be able to occupy fortress after North vacates"
        )

    def test_fortress_does_not_block_movement_through_terrain(self):
        """Fortress terrain doesn't block movement path."""
        board = Board()

        # Fortress at position 2 in path
        board.set_terrain(5, 10, TERRAIN_FORTRESS)

        # Cavalry trying to move range 2 through fortress
        board.create_and_place_unit(5, 9, "CAVALRY", PLAYER_NORTH)

        # Should be able to move through fortress to position 5, 11 (distance 2)
        from pykrieg.movement import is_valid_move
        assert is_valid_move(board, 5, 9, 5, 11, PLAYER_NORTH), (
            "Cavalry should be able to move through fortress terrain"
        )

    def test_occupied_fortress_blocks_enemy_movement(self):
        """Occupied fortress blocks enemy movement like normal squares."""
        board = Board()

        # Fortress with enemy unit
        board.set_terrain(10, 10, TERRAIN_FORTRESS)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        # North unit trying to move into occupied fortress
        board.create_and_place_unit(9, 9, "INFANTRY", PLAYER_NORTH)

        # Should NOT be able to move into occupied fortress
        from pykrieg.movement import is_valid_move
        assert not is_valid_move(board, 9, 9, 10, 10, PLAYER_NORTH), (
            "Should not be able to move into occupied fortress"
        )

    def test_fortress_defense_bonus_applies_regardless_of_occupant(self):
        """Fortress defense bonus applies to any occupying unit."""
        board = Board()

        # Fortress in North territory, occupied by South
        board.set_terrain(8, 10, TERRAIN_FORTRESS)
        board.create_and_place_unit(8, 10, "INFANTRY", PLAYER_SOUTH)

        # North attacker adjacent
        board.create_and_place_unit(7, 9, "CAVALRY", PLAYER_NORTH)

        # Calculate combat
        result = calculate_combat(board, 8, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # South infantry in North's fortress should still get +4 bonus
        # Defense = 6 + 4 = 10
        assert result['defense_power'] == 10, (
            "Fortress defense bonus should apply to any occupying unit"
        )

    def test_all_unit_types_can_occupy_fortress(self):
        """All mobile unit types should be able to occupy fortress."""
        board = Board()

        board.set_terrain(10, 10, TERRAIN_FORTRESS)

        from pykrieg.movement import is_valid_move

        # Test each unit type
        for unit_type in ["INFANTRY", "CAVALRY", "CANNON", "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"]:
            board = Board()  # Fresh board each time
            board.set_terrain(10, 10, TERRAIN_FORTRESS)
            board.create_and_place_unit(9, 9, unit_type, PLAYER_NORTH)

            assert is_valid_move(board, 9, 9, 10, 10, PLAYER_NORTH), (
                f"{unit_type} should be able to occupy fortress"
            )


class TestMountainPassOccupation:
    """Test mountain pass occupation rules (similar to fortress)."""

    def test_both_players_can_occupy_mountain_pass(self):
        """Both players should be able to occupy mountain pass."""
        board = Board()

        # Place mountain pass
        board.set_terrain(10, 10, TERRAIN_MOUNTAIN_PASS)

        from pykrieg.movement import is_valid_move

        # North can occupy
        board.create_and_place_unit(9, 9, "INFANTRY", PLAYER_NORTH)
        assert is_valid_move(board, 9, 9, 10, 10, PLAYER_NORTH), (
            "North should be able to occupy mountain pass"
        )

        # South can occupy (on fresh board)
        board = Board()
        board.set_terrain(10, 10, TERRAIN_MOUNTAIN_PASS)
        board.create_and_place_unit(11, 11, "INFANTRY", PLAYER_SOUTH)
        assert is_valid_move(board, 11, 11, 10, 10, PLAYER_SOUTH), (
            "South should be able to occupy mountain pass"
        )

    def test_mountain_pass_defense_bonus_applies_regardless_of_occupant(self):
        """Mountain pass defense bonus applies to any occupying unit."""
        board = Board()

        # Pass in North territory, occupied by South
        board.set_terrain(8, 10, TERRAIN_MOUNTAIN_PASS)
        board.create_and_place_unit(8, 10, "INFANTRY", PLAYER_SOUTH)

        # North attacker
        board.create_and_place_unit(7, 9, "CAVALRY", PLAYER_NORTH)

        # Calculate combat
        result = calculate_combat(board, 8, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # South infantry in North's pass should get +2 bonus
        # Defense = 6 + 2 = 8
        assert result['defense_power'] == 8, (
            "Mountain pass defense bonus should apply to any occupying unit"
        )


class TestArsenalDestructionWithTerrain:
    """Test arsenal destruction with terrain present."""

    def test_destroy_arsenal_clears_terrain(self):
        """Destroying arsenal should clear the terrain."""
        board = Board()

        # Place arsenal (which is terrain)
        board.set_arsenal(10, 10, PLAYER_NORTH)

        # Verify terrain is set
        assert board.get_terrain(10, 10) == TERRAIN_ARSENAL  # Arsenals have ARSENAL terrain type

        # Destroy it
        board.destroy_arsenal(10, 10)

        # Terrain should be cleared
        assert board.get_terrain(10, 10) is None

        # Owner should be removed
        assert board.get_arsenal_owner(10, 10) is None

    def test_unit_can_move_to_destroyed_arsenal_position(self):
        """Unit should be able to move to position of destroyed arsenal."""
        board = Board()

        # Place and destroy arsenal
        board.set_arsenal(10, 10, PLAYER_NORTH)
        board.destroy_arsenal(10, 10)

        # Unit should be able to move there
        board.create_and_place_unit(9, 9, "INFANTRY", PLAYER_NORTH)
        from pykrieg.movement import is_valid_move
        assert is_valid_move(board, 9, 9, 10, 10, PLAYER_NORTH)
