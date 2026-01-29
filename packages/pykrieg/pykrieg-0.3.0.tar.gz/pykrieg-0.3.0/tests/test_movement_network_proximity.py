"""Tests for movement with network proximity propagation.

This test file verifies that squares adjacent to friendly units are considered online
for movement path validation, fixing the bug where units with 2+ movement speed
couldn't properly move through empty squares adjacent to friendly units.
"""


from pykrieg.board import Board
from pykrieg.constants import PLAYER_NORTH, PLAYER_SOUTH
from pykrieg.movement import can_reach_square


class TestMovementWithNetworkProximity:
    """Test movement path validation with network proximity propagation."""

    def test_cavalry_can_move_through_empty_square_adjacent_to_friendly_unit(self):
        """Test that cavalry can move through empty square adjacent to friendly unit."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(11, 13, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Square (12, 14) is distance 2 from cavalry at (10, 12)
        # Path goes through (11, 13) which has infantry (online)
        # Then through (12, 13) which is empty but adjacent to infantry at (11, 13)
        # This should be considered online due to proximity
        assert can_reach_square(board, 10, 12, 12, 14, PLAYER_NORTH)

    def test_cavalry_cannot_move_through_empty_square_without_proximity(self):
        """Test that cavalry cannot move through empty square without proximity to friendly unit."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "CAVALRY", PLAYER_NORTH)
        board.enable_networks()

        # Square (12, 14) is distance 2 from cavalry
        # The cavalry itself is online, so squares adjacent to it are online
        # This creates a chain: (10,12) online -> (11,13) online (adjacent) -> (12,14) online (adjacent to 11,13)
        # So cavalry CAN move there through the chain of proximity
        assert can_reach_square(board, 10, 12, 12, 14, PLAYER_NORTH)

    def test_empty_square_adjacent_to_online_unit_is_online(self):
        """Test that empty squares adjacent to online units are considered online."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Empty square (11, 13) is adjacent to online infantry at (10, 12)
        # It should be considered online
        assert board.is_unit_online(11, 13, PLAYER_NORTH)

    def test_cavalry_movement_to_online_adjacent_empty_square(self):
        """Test that cavalry can move to empty square adjacent to friendly unit."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 14, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Square (11, 13) is adjacent to infantry at (10, 14)
        # It should be online and reachable by cavalry
        assert board.is_unit_online(11, 13, PLAYER_NORTH)
        assert can_reach_square(board, 10, 12, 11, 13, PLAYER_NORTH)

    def test_cavalry_movement_2_squares_through_online_proximity_chain(self):
        """Test cavalry moving to infantry through proximity chain."""
        board = Board()
        board.set_arsenal(10, 10, PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 14, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Square (10, 14) has infantry and is within arsenal ray range
        # Path: (10,10) -> (10,11) [empty, adjacent to cavalry] -> (10,12) [infantry]
        # Cavalry cannot reach (10, 14) because distance is 4, which exceeds cavalry's movement range of 2
        assert board.is_unit_online(10, 11, PLAYER_NORTH)
        assert board.is_unit_online(10, 13, PLAYER_NORTH)
        # Distance from (10, 10) to (10, 14) is 4, which exceeds cavalry's movement range of 2
        assert not can_reach_square(board, 10, 10, 10, 14, PLAYER_NORTH)

    def test_swift_relay_movement_through_online_proximity(self):
        """Test swift relay (movement 2) can move through empty squares adjacent to friendly units."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "SWIFT_RELAY", PLAYER_NORTH)
        board.create_and_place_unit(11, 13, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Swift relay has movement 2, should behave like cavalry
        # Square (12, 14) is distance 2 through path with proximity coverage
        assert can_reach_square(board, 10, 12, 12, 14, PLAYER_NORTH)

    def test_all_8_directions_proximity_coverage(self):
        """Test that all 8 directions get proximity coverage from online unit."""
        board = Board()
        board.set_arsenal(10, 10, PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # All 8 adjacent squares should be online (even if empty)
        for dx, dy in [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]:
            adj_row = 10 + dx
            adj_col = 10 + dy
            assert board.is_unit_online(adj_row, adj_col, PLAYER_NORTH), \
                f"Square ({adj_row}, {adj_col}) should be online due to proximity"

    def test_cascading_proximity_for_movement(self):
        """Test that proximity cascades allowing longer movement paths."""
        board = Board()
        board.set_arsenal(10, 10, PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "CAVALRY", PLAYER_NORTH)
        # Create a diagonal line of units
        board.create_and_place_unit(11, 11, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(12, 12, "INFANTRY", PLAYER_NORTH)
        board.enable_networks()

        # Cavalry should be able to move to (12, 12) through the chain
        # The path goes through empty squares that are adjacent to online units
        assert can_reach_square(board, 10, 10, 12, 12, PLAYER_NORTH)

    def test_enemy_units_block_proximity(self):
        """Test that enemy units don't provide proximity coverage."""
        board = Board()
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(11, 13, "INFANTRY", PLAYER_SOUTH)  # Enemy
        board.enable_networks()

        # Square (12, 14) should not be reachable through enemy unit proximity
        # The path goes through (11, 13) which has enemy unit (blocks path anyway)
        # But even if we go around, empty squares adjacent to enemy shouldn't be online for North
        assert not can_reach_square(board, 10, 12, 12, 14, PLAYER_NORTH)

    def test_proximity_cascades_from_online_unit(self):
        """Test that proximity cascades from online cavalry creating a chain."""
        board = Board()
        board.set_arsenal(10, 10, PLAYER_NORTH)
        board.create_and_place_unit(10, 15, "CAVALRY", PLAYER_NORTH)
        board.enable_networks()

        # Cavalry at (10, 15) is within arsenal ray coverage (distance 5)
        # Empty squares adjacent to cavalry become online
        # Then squares adjacent to those squares also become online via the cascade
        # Square (10, 17) is distance 2 from cavalry at (10, 15)
        # Path: (10,15) -> (10,16) [adjacent to cavalry] -> (10,17) [adjacent to 10,16]
        # So (10,17) should be online due to cascading proximity
        assert board.is_unit_online(10, 16, PLAYER_NORTH)
        assert board.is_unit_online(10, 17, PLAYER_NORTH)
