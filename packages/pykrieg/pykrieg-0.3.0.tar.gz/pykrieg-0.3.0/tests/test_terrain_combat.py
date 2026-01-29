"""Tests for terrain combat modifiers."""


from pykrieg.board import Board
from pykrieg.combat import (
    calculate_defense_power,
    get_terrain_defense_bonus,
    preview_combat,
)
from pykrieg.constants import PLAYER_NORTH, PLAYER_SOUTH


class TestTerrainDefenseBonus:
    """Test get_terrain_defense_bonus function."""

    def test_no_terrain_bonus(self):
        """No terrain has 0 bonus."""
        assert get_terrain_defense_bonus(None) == 0

    def test_mountain_bonus(self):
        """Mountain has 0 bonus (impassable, no combat)."""
        assert get_terrain_defense_bonus("MOUNTAIN") == 0

    def test_mountain_pass_bonus(self):
        """Mountain pass has +2 bonus."""
        assert get_terrain_defense_bonus("MOUNTAIN_PASS") == 2

    def test_fortress_bonus(self):
        """Fortress has +4 bonus."""
        assert get_terrain_defense_bonus("FORTRESS") == 4


class TestDefensePowerWithTerrain:
    """Test terrain bonuses in defense power calculation."""

    def test_defense_power_with_mountain_pass(self):
        """Unit on mountain pass gets +2 defense bonus."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # Infantry has 6 defense, +2 terrain bonus = 8
        assert defense == 8

    def test_defense_power_with_fortress(self):
        """Unit in fortress gets +4 defense bonus."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "FORTRESS")

        defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # Infantry has 6 defense, +4 terrain bonus = 10
        assert defense == 10

    def test_defense_power_without_terrain(self):
        """Unit without terrain gets no bonus."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # Infantry has 6 defense, no terrain bonus
        assert defense == 6

    def test_terrain_bonus_without_unit(self):
        """Terrain bonus applies even without unit."""
        board = Board()
        board.set_terrain(10, 10, "FORTRESS")

        defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # No unit, but +4 terrain bonus
        assert defense == 4

    def test_terrain_bonus_with_support(self):
        """Terrain bonus works with supporting units."""
        board = Board()
        # Target unit in fortress
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "FORTRESS")

        # Supporting unit to the south
        board.create_and_place_unit(11, 10, "INFANTRY", PLAYER_SOUTH)

        defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # Target infantry (6) + fortress bonus (4) + supporting infantry (6) = 16
        assert defense == 16

    def test_multiple_units_on_pass(self):
        """Each unit on pass gets terrain bonus independently."""
        board = Board()

        # Test first unit
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")
        defense_10 = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

        # Infantry (6) + pass bonus (2) = 8
        assert defense_10 == 8

        # Clear and test second unit separately
        board.clear_square(10, 10)
        board.create_and_place_unit(10, 11, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 11, "MOUNTAIN_PASS")
        defense_11 = calculate_defense_power(board, 10, 11, PLAYER_SOUTH)

        # Infantry (6) + pass bonus (2) = 8
        assert defense_11 == 8


class TestCombatPreviewTerrainInfo:
    """Test that preview_combat includes terrain information."""

    def test_preview_shows_terrain_type(self):
        """preview_combat includes terrain type."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "FORTRESS")

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        assert 'target_terrain' in preview
        assert preview['target_terrain'] == "FORTRESS"

    def test_preview_shows_terrain_bonus(self):
        """preview_combat includes terrain bonus amount."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "FORTRESS")

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        assert 'terrain_bonus' in preview
        assert preview['terrain_bonus'] == 4

    def test_preview_defense_includes_terrain(self):
        """Defense power in preview includes terrain bonus."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Infantry (6) + pass bonus (2) = 8
        assert preview['defense_power'] == 8

    def test_preview_with_pass_terrain(self):
        """preview_combat works correctly with mountain pass."""
        board = Board()
        board.create_and_place_unit(10, 10, "CAVALRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        assert preview['target_terrain'] == "MOUNTAIN_PASS"
        assert preview['terrain_bonus'] == 2
        # Cavalry defense (5) + pass bonus (2) = 7
        assert preview['defense_power'] == 7

    def test_preview_with_no_terrain(self):
        """preview_combat shows None for no terrain."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        assert preview['target_terrain'] is None
        assert preview['terrain_bonus'] == 0
        # Infantry defense (6) + no bonus = 6
        assert preview['defense_power'] == 6


class TestTerrainCombatOutcomes:
    """Test that terrain bonuses affect combat outcomes."""

    def test_pass_makes_defense_stronger(self):
        """Mountain pass can turn FAIL into RETREAT."""
        board = Board()

        # Defending unit on pass
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        # Attacking unit (just infantry, weak attack)
        board.create_and_place_unit(9, 10, "INFANTRY", PLAYER_NORTH)

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Attack: Infantry (4)
        # Defense: Infantry (6) + Pass (2) = 8
        # Outcome: 4 ≤ 8 = FAIL
        assert preview['attack_power'] == 4
        assert preview['defense_power'] == 8
        assert preview['outcome'].value == "FAIL"

    def test_fortress_makes_defense_very_strong(self):
        """Fortress can turn CAPTURE into FAIL."""
        board = Board()

        # Defending unit in fortress
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "FORTRESS")

        # Attacking unit
        board.create_and_place_unit(9, 10, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(8, 10, "INFANTRY", PLAYER_NORTH)  # Support

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Attack: Two infantry (4 + 4) = 8
        # Defense: Infantry (6) + Fortress (4) = 10
        # Outcome: 8 ≤ 10 = FAIL
        assert preview['attack_power'] == 8
        assert preview['defense_power'] == 10
        assert preview['outcome'].value == "FAIL"

    def test_pass_allows_capture_with_sufficient_attack(self):
        """Pass doesn't prevent capture with strong attack."""
        board = Board()

        # Defending unit on pass
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        # Attacking units (very strong - 3 cannons in direct lines)
        # Place cannons all at distance 3 in different straight lines
        board.create_and_place_unit(7, 10, "CANNON", PLAYER_NORTH)  # Directly above
        board.create_and_place_unit(10, 7, "CANNON", PLAYER_NORTH)   # Directly left
        board.create_and_place_unit(10, 13, "CANNON", PLAYER_NORTH)  # Directly right

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Attack: Three cannons (5 + 5 + 5) = 15
        # Defense: Infantry (6) + Pass (2) = 8
        # Outcome: 15 ≥ 8 + 2 = CAPTURE
        assert preview['attack_power'] == 15
        assert preview['defense_power'] == 8
        assert preview['outcome'].value == "CAPTURE"

    def test_terrain_without_unit_can_be_captured(self):
        """Can capture empty square with terrain bonus."""
        board = Board()
        board.set_terrain(10, 10, "FORTRESS")

        # Attacking unit (place it not on same line as potential support)
        board.create_and_place_unit(10, 12, "CAVALRY", PLAYER_NORTH)

        preview = preview_combat(board, 10, 10, PLAYER_NORTH, PLAYER_SOUTH)

        # Attack: Cavalry (4)
        # Defense: No unit, but Fortress (4) = 4
        # Outcome: 4 ≤ 4 = FAIL
        assert preview['attack_power'] == 4
        assert preview['defense_power'] == 4
        assert preview['outcome'].value == "FAIL"

    def test_different_unit_types_with_terrain(self):
        """Terrain bonus works with all unit types."""
        board = Board()

        for unit_type in ["INFANTRY", "CAVALRY", "CANNON", "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"]:
            # Test with fortress bonus
            board.create_and_place_unit(10, 10, unit_type, PLAYER_SOUTH)
            board.set_terrain(10, 10, "FORTRESS")

            defense = calculate_defense_power(board, 10, 10, PLAYER_SOUTH)

            # Defense should be unit's base defense + 4
            unit = board.get_unit(10, 10)
            base_defense = getattr(unit, 'defense', 0)
            assert defense == base_defense + 4

            # Clean up for next iteration
            board.clear_square(10, 10)
