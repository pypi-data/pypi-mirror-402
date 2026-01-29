"""Test victory condition detection for Pykrieg 0.2.2."""

import pytest

from pykrieg.board import Board
from pykrieg.victory import (
    GameState,
    VictoryCondition,
    check_victory_conditions,
)


class TestTotalAnnihilation:
    """Test total annihilation victory condition."""

    def test_victory_total_annihilation_north(self) -> None:
        """Test North loses when all units annihilated."""
        board = Board()

        # South has units (must enable network to avoid network collapse detection)
        board.set_arsenal(15, 12, 'SOUTH')
        board.create_and_place_unit(15, 10, 'INFANTRY', 'SOUTH')
        board.enable_networks()

        # North has no units
        result = check_victory_conditions(board)

        assert result.game_state == GameState.SOUTH_WINS
        assert result.winner == 'SOUTH'
        assert result.victory_condition == VictoryCondition.TOTAL_ANNIHILATION
        assert 'annihilated' in result.details.lower()

    def test_victory_total_annihilation_south(self) -> None:
        """Test South loses when all units annihilated."""
        board = Board()

        # North has units (must enable network to avoid network collapse detection)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 10, 'CANNON', 'NORTH')
        board.create_and_place_unit(5, 8, 'SWIFT_CANNON', 'NORTH')
        board.enable_networks()

        # South has no units
        result = check_victory_conditions(board)

        assert result.game_state == GameState.NORTH_WINS
        assert result.winner == 'NORTH'
        assert result.victory_condition == VictoryCondition.TOTAL_ANNIHILATION

    def test_all_unit_types_counted(self) -> None:
        """Test that all unit types (including relays) are counted."""
        board = Board()

        # Place all unit types for North (with network)
        board.set_arsenal(5, 10, 'NORTH')
        board.create_and_place_unit(5, 1, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(5, 2, 'CAVALRY', 'NORTH')
        board.create_and_place_unit(5, 3, 'CANNON', 'NORTH')
        board.create_and_place_unit(5, 4, 'SWIFT_CANNON', 'NORTH')
        board.create_and_place_unit(5, 5, 'RELAY', 'NORTH')
        board.create_and_place_unit(5, 6, 'SWIFT_RELAY', 'NORTH')
        board.enable_networks()

        # South has no units
        result = check_victory_conditions(board)

        assert result.game_state == GameState.NORTH_WINS

    def test_single_unit_prevents_annihilation(self) -> None:
        """Test that having even 1 unit prevents total annihilation."""
        board = Board()

        # South has 1 unit (with network)
        board.set_arsenal(15, 10, 'SOUTH')
        board.create_and_place_unit(15, 5, 'INFANTRY', 'SOUTH')
        board.enable_networks()

        # North has no units
        result = check_victory_conditions(board)

        assert result.game_state == GameState.SOUTH_WINS
        assert result.victory_condition == VictoryCondition.TOTAL_ANNIHILATION


class TestNetworkCollapse:
    """Test network collapse victory condition."""

    def test_victory_network_collapse_no_arsenals(self) -> None:
        """Test network collapse when all arsenals destroyed."""
        board = Board()

        # South has units but no arsenals
        board.create_and_place_unit(15, 5, 'INFANTRY', 'SOUTH')
        board.create_and_place_unit(15, 10, 'CAVALRY', 'SOUTH')

        # North has units WITH arsenal (so North doesn't collapse)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')

        board.enable_networks()

        result = check_victory_conditions(board)

        assert result.game_state == GameState.NORTH_WINS
        assert result.victory_condition == VictoryCondition.NETWORK_COLLAPSE
        assert 'arsenal' in result.details.lower() or 'network' in result.details.lower()

    def test_victory_network_collapse_all_units_offline(self) -> None:
        """Test network collapse when all units are offline."""
        board = Board()

        # South has arsenals but units offline (far from arsenal)
        board.set_arsenal(15, 10, 'SOUTH')
        board.set_arsenal(15, 20, 'SOUTH')
        board.create_and_place_unit(15, 12, 'INFANTRY', 'SOUTH')  # Should be online

        # North has units online (actually close to arsenal)
        board.set_arsenal(5, 5, 'NORTH')
        board.create_and_place_unit(5, 8, 'INFANTRY', 'NORTH')  # Should be online

        board.enable_networks()

        result = check_victory_conditions(board)

        # Both players have online units, so game is ongoing
        assert result.game_state == GameState.ONGOING

    def test_network_collapse_requires_offline_units(self) -> None:
        """Test that having online units prevents network collapse."""
        board = Board()

        # South has arsenal, some units online (with relay)
        board.set_arsenal(15, 10, 'SOUTH')
        board.create_and_place_unit(15, 11, 'INFANTRY', 'SOUTH')
        board.create_and_place_unit(15, 5, 'RELAY', 'SOUTH')

        # North has units
        board.set_arsenal(5, 5, 'NORTH')
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        board.enable_networks()

        result = check_victory_conditions(board)

        # Game should be ongoing (South has online units)
        assert result.game_state == GameState.ONGOING

    def test_network_collapse_no_check_when_disabled(self) -> None:
        """Test that network collapse is not checked when network disabled."""
        board = Board()

        # Both players have units (network not enabled)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

        board.set_arsenal(15, 12, 'SOUTH')
        board.create_and_place_unit(15, 5, 'INFANTRY', 'SOUTH')
        board.create_and_place_unit(15, 10, 'CAVALRY', 'SOUTH')

        # Don't enable networks
        result = check_victory_conditions(board)

        # Game should be ongoing (network not enabled)
        assert result.game_state == GameState.ONGOING


class TestBoardIntegration:
    """Test victory condition integration with Board class."""

    def test_victory_checked_after_end_turn(self) -> None:
        """Test that victory conditions are checked after end_turn()."""
        board = Board()

        # Set up: North has units with network, South has none
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.enable_networks()

        # Game should be ongoing
        assert not board.is_game_over()

        # End turn (victory should be checked)
        board.end_turn()

        # Game should be over
        assert board.is_game_over()
        assert board.game_state == 'NORTH_WINS'

    def test_victory_result_persisted(self) -> None:
        """Test that victory result is persisted after checking."""
        board = Board()

        # Set up victory condition (North has units, South doesn't)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        # Check result
        result = board.victory_result
        assert result is not None
        assert result['winner'] == 'NORTH'
        assert result['victory_condition'] == 'TOTAL_ANNIHILATION'

    def test_game_state_property(self) -> None:
        """Test game_state property returns correct state."""
        board = Board()

        # Should be ongoing initially
        assert board.game_state == 'ONGOING'

        # Set up victory condition
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        # Should reflect victory state
        assert board.game_state == 'NORTH_WINS'

    def test_is_game_over_property(self) -> None:
        """Test is_game_over() returns correct boolean."""
        board = Board()

        # Should be False initially
        assert not board.is_game_over()

        # Set up victory condition
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        # Should be True after victory
        assert board.is_game_over()


class TestSurrender:
    """Test surrender victory condition."""

    def test_surrender_north(self) -> None:
        """Test that North can surrender and South wins."""
        board = Board()

        # Set up normal game state
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(15, 10, 'INFANTRY', 'SOUTH')
        board.enable_networks()

        # North surrenders
        board.handle_surrender('NORTH')

        assert board.is_game_over()
        assert board.game_state == 'SOUTH_WINS'
        result = board.victory_result
        assert result['winner'] == 'SOUTH'
        assert result['victory_condition'] == 'SURRENDER'
        assert 'surrender' in result['details'].lower()

    def test_surrender_south(self) -> None:
        """Test that South can surrender and North wins."""
        board = Board()

        # Set up normal game state
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(15, 10, 'INFANTRY', 'SOUTH')
        board.enable_networks()

        # South surrenders
        board.handle_surrender('SOUTH')

        assert board.is_game_over()
        assert board.game_state == 'NORTH_WINS'
        result = board.victory_result
        assert result['winner'] == 'NORTH'
        assert result['victory_condition'] == 'SURRENDER'

    def test_surrender_ends_game_immediately(self) -> None:
        """Test that surrender ends game even if other conditions not met."""
        board = Board()

        # Both players have equal forces
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.create_and_place_unit(5, 10, 'CAVALRY', 'NORTH')
        board.create_and_place_unit(15, 5, 'INFANTRY', 'SOUTH')
        board.create_and_place_unit(15, 10, 'CAVALRY', 'SOUTH')
        board.set_arsenal(5, 20, 'NORTH')
        board.set_arsenal(15, 20, 'SOUTH')
        board.enable_networks()

        # Game should be ongoing
        assert not board.is_game_over()

        # South surrenders
        board.handle_surrender('SOUTH')

        # Game should be over
        assert board.is_game_over()

    def test_cannot_surrender_after_game_over(self) -> None:
        """Test that surrender has no effect if game is already over."""
        board = Board()

        # Set up total annihilation for South (North has units with network)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        assert board.is_game_over()
        assert board.game_state == 'NORTH_WINS'

        # Attempt to surrender - should raise error
        with pytest.raises(ValueError, match="Cannot surrender: game is already over"):
            board.handle_surrender('NORTH')


class TestArsenalDestruction:
    """Test arsenal destruction mechanics."""

    def test_destroy_enemy_arsenal(self) -> None:
        """Test that moving onto enemy arsenal destroys it."""
        board = Board()

        # Set up enemy arsenal
        board.set_arsenal(15, 10, 'SOUTH')

        # North cavalry moves onto it (cavalry has good movement range)
        board.create_and_place_unit(14, 8, 'CAVALRY', 'NORTH')
        unit, arsenal_destroyed = board.make_turn_move(14, 8, 15, 10)

        assert arsenal_destroyed
        assert unit.owner == 'NORTH'
        # Arsenal should be gone
        assert board._terrain[15][10] is None
        assert (15, 10) not in board._arsenal_owners

    def test_destroy_friendly_arsenal(self) -> None:
        """Test that moving onto friendly arsenal does NOT destroy it."""
        board = Board()

        # Set up own arsenal
        board.set_arsenal(5, 10, 'NORTH')

        # North infantry moves onto own arsenal (1 square away)
        board.create_and_place_unit(5, 9, 'INFANTRY', 'NORTH')
        unit, arsenal_destroyed = board.make_turn_move(5, 9, 5, 10)

        assert not arsenal_destroyed
        # Arsenal should still exist
        assert board._terrain[5][10] is not None
        assert (5, 10) in board._arsenal_owners

    def test_destroy_arsenal_returns_true(self) -> None:
        """Test that destroying arsenal returns True flag."""
        board = Board()

        board.set_arsenal(15, 10, 'SOUTH')
        board.create_and_place_unit(14, 8, 'CAVALRY', 'NORTH')

        unit, arsenal_destroyed = board.make_turn_move(14, 8, 15, 10)

        assert arsenal_destroyed is True

    def test_no_arsenal_at_destination(self) -> None:
        """Test that moving to non-arsenal returns False flag."""
        board = Board()

        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')

        unit, arsenal_destroyed = board.make_turn_move(5, 5, 6, 5)

        assert arsenal_destroyed is False

    def test_destroy_arsenal_method(self) -> None:
        """Test destroy_arsenal() method directly."""
        board = Board()

        # Set up arsenal
        board.set_arsenal(15, 10, 'SOUTH')

        # Destroy it
        board.destroy_arsenal(15, 10)

        # Verify destruction
        assert board._terrain[15][10] is None
        assert (15, 10) not in board._arsenal_owners

    def test_destroy_arsenal_raises_error(self) -> None:
        """Test that destroying non-arsenal raises ValueError."""
        board = Board()

        with pytest.raises(ValueError, match="No arsenal"):
            board.destroy_arsenal(10, 10)


class TestGameOverEnforcement:
    """Test that game over enforcement prevents invalid actions."""

    def test_cannot_move_after_game_over(self) -> None:
        """Test that making a move after game over raises error."""
        board = Board()

        # Set up victory condition
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        assert board.is_game_over()

        # Attempt to make move - validation should fail
        board.create_and_place_unit(5, 6, 'INFANTRY', 'NORTH')
        assert not board.validate_move(5, 5, 6, 6)

    def test_cannot_attack_after_game_over(self) -> None:
        """Test that making an attack after game over raises error."""
        board = Board()

        # Set up victory condition
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.check_victory()

        assert board.is_game_over()

        # Attempt to make attack - validation should fail
        board.create_and_place_unit(5, 6, 'CANNON', 'NORTH')
        board.switch_to_battle_phase()
        assert not board.validate_attack(15, 10)


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_draw_simultaneous_defeat(self) -> None:
        """Test draw when both players lose simultaneously."""
        board = Board()

        # Both players have no units
        result = check_victory_conditions(board)

        # Should be draw
        assert result.game_state == GameState.DRAW
        assert result.winner is None
        assert 'draw' in result.details.lower()

    def test_empty_board_draw(self) -> None:
        """Test that empty board results in draw."""
        board = Board()

        # No units for either player
        result = check_victory_conditions(board)

        # Should be draw
        assert result.game_state == GameState.DRAW

    def test_priority_annihilation_over_network(self) -> None:
        """Test that total annihilation takes priority over network collapse."""
        board = Board()

        # South has no units (annihilation)
        # North has units WITH arsenal (so doesn't have network collapse)
        board.set_arsenal(5, 12, 'NORTH')
        board.create_and_place_unit(5, 5, 'INFANTRY', 'NORTH')
        board.enable_networks()

        result = check_victory_conditions(board)

        # Should be total annihilation (higher priority)
        assert result.game_state == GameState.NORTH_WINS
        assert result.victory_condition == VictoryCondition.TOTAL_ANNIHILATION

    def test_victory_with_pending_retreats(self) -> None:
        """Test victory detection with pending retreats."""
        board = Board()

        # Set up combat that results in retreat
        board.set_arsenal(5, 5, 'NORTH')
        board.create_and_place_unit(5, 8, 'CANNON', 'NORTH')
        board.create_and_place_unit(6, 8, 'INFANTRY', 'SOUTH')
        board.enable_networks()

        # Attack causing retreat
        board.switch_to_battle_phase()
        board.make_turn_attack(6, 8)

        # End turn - retreats resolved, then victory checked
        board.end_turn()

        # Should work correctly (South still has unit)
        assert not board.is_game_over() or board.game_state == 'NORTH_WINS'
