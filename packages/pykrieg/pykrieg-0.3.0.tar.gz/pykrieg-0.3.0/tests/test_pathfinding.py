"""Tests for pathfinding-based movement validation.

This module tests the BFS pathfinding algorithm that ensures units cannot move
through solid walls of enemy units, but can move through friendly units and gaps
in enemy lines.
"""

from pykrieg.board import Board
from pykrieg.movement import can_reach_square, generate_moves, is_valid_move


class TestPathfindingBasic:
    """Test basic pathfinding functionality."""

    def test_can_reach_empty_square(self):
        """Test movement through empty squares."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        # Should be able to reach any adjacent empty square
        assert can_reach_square(board, 5, 10, 6, 11, "NORTH")  # Diagonal
        assert can_reach_square(board, 5, 10, 5, 11, "NORTH")  # Right
        assert can_reach_square(board, 5, 10, 6, 10, "NORTH")  # Down

    def test_cannot_reach_blocked_by_enemy(self):
        """Test that enemy units block the path."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")

        # Should not be able to reach square occupied by enemy
        assert not can_reach_square(board, 5, 10, 6, 11, "NORTH")

    def test_can_reach_through_friendly(self):
        """Test that friendly units are passable."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "INFANTRY", "NORTH")

        # Should be able to move through friendly unit
        assert can_reach_square(board, 5, 10, 6, 11, "NORTH")

    def test_cannot_reach_through_enemy_wall(self):
        """Test that a solid wall of enemy units blocks movement."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create a solid wall of enemy infantry
        for col in range(11, 16):
            board.create_and_place_unit(6, col, "INFANTRY", "SOUTH")

        # Should not be able to reach behind the wall
        assert not can_reach_square(board, 5, 10, 7, 13, "NORTH")

    def test_can_reach_through_gap_in_enemy_wall(self):
        """Test that a gap in enemy lines allows movement."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create enemy wall with a gap at column 11
        for col in range(11, 14):
            if col != 11:  # Leave gap at col 11
                board.create_and_place_unit(6, col, "INFANTRY", "SOUTH")

        # Should be able to reach through gap at column 11
        # (5,10) -> (6,11) -> (7,11) is within range 2
        assert can_reach_square(board, 5, 10, 6, 11, "NORTH")
        assert can_reach_square(board, 5, 10, 7, 11, "NORTH")


class TestCavalryMovement:
    """Test cavalry (range 2) pathfinding scenarios."""

    def test_cavalry_around_enemy_wall(self):
        """Test cavalry moving around enemy wall."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create partial enemy wall
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")
        board.create_and_place_unit(6, 12, "INFANTRY", "SOUTH")
        board.create_and_place_unit(6, 13, "INFANTRY", "SOUTH")

        # Cavalry should be able to go around wall
        assert can_reach_square(board, 5, 10, 7, 10, "NORTH")  # Below wall
        assert can_reach_square(board, 5, 10, 7, 11, "NORTH")  # Through gap if exists

    def test_cavalry_movement_range_with_obstacles(self):
        """Test cavalry respects movement range even with obstacles."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create obstacles
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")

        # Should reach squares within range 2
        assert can_reach_square(board, 5, 10, 7, 10, "NORTH")
        # (5,10) to (7,12) is max(2,2) = 2, within range, but path blocked
        # Let's check a simpler reachable square
        assert can_reach_square(board, 5, 10, 6, 10, "NORTH")

        # Should not reach squares beyond range 2
        assert not can_reach_square(board, 5, 10, 8, 10, "NORTH")


class TestInfantryMovement:
    """Test infantry (range 1) pathfinding scenarios."""

    def test_infantry_adjacent_enemy_blocks(self):
        """Test infantry cannot move through adjacent enemy."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")

        # Infantry range is 1, so enemy directly blocks
        assert not can_reach_square(board, 5, 10, 6, 11, "NORTH")

        # But can move to other adjacent squares
        assert can_reach_square(board, 5, 10, 6, 10, "NORTH")
        assert can_reach_square(board, 5, 10, 5, 11, "NORTH")

    def test_infantry_through_friendly(self):
        """Test infantry can move through friendly units."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "INFANTRY", "NORTH")

        # Can move to adjacent square with friendly unit
        assert can_reach_square(board, 5, 10, 6, 11, "NORTH")


class TestGenerateMovesWithPathfinding:
    """Test that generate_moves respects pathfinding."""

    def test_generate_moves_respects_enemy_wall(self):
        """Test generate_moves doesn't include moves through enemy walls."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create solid enemy wall
        for col in range(11, 16):
            board.create_and_place_unit(6, col, "INFANTRY", "SOUTH")

        moves = generate_moves(board, 5, 10)

        # Should not include moves behind the wall
        assert (7, 13) not in moves
        assert (7, 12) not in moves
        assert (7, 14) not in moves

    def test_generate_moves_includes_gaps(self):
        """Test generate_moves includes moves through gaps."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create enemy wall with gap at column 11
        for col in range(11, 14):
            if col != 11:
                board.create_and_place_unit(6, col, "INFANTRY", "SOUTH")

        moves = generate_moves(board, 5, 10)

        # Should include moves through gap at column 11
        assert (6, 11) in moves
        assert (7, 11) in moves


class TestIsValidMoveWithPathfinding:
    """Test that is_valid_move uses pathfinding."""

    def test_is_valid_move_pathfinding(self):
        """Test is_valid_move checks path."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create enemy wall
        for col in range(11, 16):
            board.create_and_place_unit(6, col, "INFANTRY", "SOUTH")

        # Should not be valid to move through wall
        assert not is_valid_move(board, 5, 10, 7, 13, "NORTH")

        # Should be valid to move around wall
        assert is_valid_move(board, 5, 10, 7, 10, "NORTH")

    def test_is_valid_move_destination_occupied(self):
        """Test is_valid_move still checks destination occupation."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")

        # Should not be valid to move to occupied square
        assert not is_valid_move(board, 5, 10, 6, 11, "NORTH")

    def test_is_valid_move_respects_range(self):
        """Test is_valid_move still checks movement range."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        # Infantry range is 1, so should not be valid
        assert not is_valid_move(board, 5, 10, 7, 12, "NORTH")


class TestCornerCases:
    """Test edge cases and corner scenarios."""

    def test_no_path_exceeds_range(self):
        """Test that pathfinding stops at movement range."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create obstacles that force long path
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")
        board.create_and_place_unit(7, 10, "INFANTRY", "SOUTH")
        board.create_and_place_unit(6, 9, "INFANTRY", "SOUTH")

        # Should not be able to reach - would exceed range 2
        assert not can_reach_square(board, 5, 10, 8, 10, "NORTH")

    def test_multiple_enemies_block(self):
        """Test that multiple enemy units block correctly."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create multiple enemy units
        board.create_and_place_unit(6, 11, "INFANTRY", "SOUTH")
        board.create_and_place_unit(6, 12, "CAVALRY", "SOUTH")
        board.create_and_place_unit(7, 11, "CANNON", "SOUTH")

        # Should block movement through any enemy
        assert not can_reach_square(board, 5, 10, 7, 12, "NORTH")

    def test_board_boundaries(self):
        """Test that pathfinding respects board boundaries."""
        board = Board()
        board.create_and_place_unit(0, 0, "CAVALRY", "NORTH")

        # Should not try to go off board
        assert not can_reach_square(board, 0, 0, -1, 0, "NORTH")
        assert not can_reach_square(board, 0, 0, 0, -1, "NORTH")

    def test_same_square(self):
        """Test that unit cannot move to its own square."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        # Should not be able to move to same square
        assert not can_reach_square(board, 5, 10, 5, 10, "NORTH")


class TestFriendlyUnitPassable:
    """Test various scenarios with friendly units."""

    def test_mixed_friendly_enemy_units(self):
        """Test pathfinding with mixed friendly and enemy units."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create mixed wall
        board.create_and_place_unit(6, 11, "INFANTRY", "NORTH")  # Friendly
        board.create_and_place_unit(6, 12, "INFANTRY", "SOUTH")  # Enemy
        board.create_and_place_unit(6, 13, "INFANTRY", "NORTH")  # Friendly

        # Should not be able to pass through enemy
        assert not can_reach_square(board, 5, 10, 7, 13, "NORTH")

    def test_path_through_multiple_friendly(self):
        """Test path through multiple friendly units."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")

        # Create line of friendly units
        board.create_and_place_unit(6, 11, "INFANTRY", "NORTH")
        board.create_and_place_unit(7, 11, "INFANTRY", "NORTH")

        # Should be able to reach through friendly units
        assert can_reach_square(board, 5, 10, 7, 12, "NORTH")
