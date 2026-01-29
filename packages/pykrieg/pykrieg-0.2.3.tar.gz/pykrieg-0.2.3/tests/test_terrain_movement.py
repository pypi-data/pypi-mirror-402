"""Tests for terrain movement restrictions."""


from pykrieg.board import Board
from pykrieg.constants import PLAYER_NORTH, PLAYER_SOUTH
from pykrieg.movement import is_valid_move


class TestMountainBlocking:
    """Test that mountains block movement."""

    def test_cannot_move_into_mountain(self):
        """Unit cannot move into mountain square."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "MOUNTAIN")

        # Cannot move into mountain
        assert not is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_cannot_move_through_mountain(self):
        """Mountain blocks path when it blocks all routes."""
        board = Board()
        board.create_and_place_unit(10, 10, "CAVALRY", PLAYER_NORTH)

        # Create a wall of mountains blocking all paths to destination
        board.set_terrain(10, 11, "MOUNTAIN")
        board.set_terrain(11, 11, "MOUNTAIN")
        board.set_terrain(9, 11, "MOUNTAIN")

        # Cannot move through mountain wall
        assert not is_valid_move(board, 10, 10, 10, 12, PLAYER_NORTH)

    def test_cannot_move_diagonal_through_mountain(self):
        """Mountain blocks diagonal paths."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", PLAYER_NORTH)
        board.set_terrain(6, 11, "MOUNTAIN")

        # Cannot move diagonally through mountain
        assert not is_valid_move(board, 5, 10, 7, 12, PLAYER_NORTH)

    def test_all_unit_types_blocked_by_mountain(self):
        """All unit types are blocked by mountains."""
        board = Board()

        for unit_type in ["INFANTRY", "CAVALRY", "CANNON", "RELAY"]:
            board.create_and_place_unit(5, 10, unit_type, PLAYER_NORTH)
            board.set_terrain(5, 11, "MOUNTAIN")

            # Cannot move into mountain
            assert not is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

            board.clear_square(5, 10)
            board.set_terrain(5, 11, None)


class TestMountainPassMovement:
    """Test that mountain passes allow movement."""

    def test_can_move_into_mountain_pass(self):
        """Unit can move into mountain pass."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "MOUNTAIN_PASS")

        # Can move into pass
        assert is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_can_move_through_mountain_pass(self):
        """Mountain pass allows path for movement range 2+."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "MOUNTAIN_PASS")

        # Can move through pass
        assert is_valid_move(board, 5, 10, 5, 12, PLAYER_NORTH)

    def test_all_unit_types_can_use_pass(self):
        """All mobile unit types can use mountain pass."""
        board = Board()

        for unit_type in ["INFANTRY", "CAVALRY", "CANNON", "RELAY"]:
            board.create_and_place_unit(5, 10, unit_type, PLAYER_NORTH)
            board.set_terrain(5, 11, "MOUNTAIN_PASS")

            # Can move into pass
            assert is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

            board.clear_square(5, 10)
            board.set_terrain(5, 11, None)


class TestFortressMovement:
    """Test that fortresses allow movement."""

    def test_can_move_into_fortress(self):
        """Unit can move into fortress."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "FORTRESS")

        # Can move into fortress
        assert is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_can_move_through_fortress(self):
        """Fortress allows path for movement range 2+."""
        board = Board()
        board.create_and_place_unit(5, 10, "CAVALRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "FORTRESS")

        # Can move through fortress
        assert is_valid_move(board, 5, 10, 5, 12, PLAYER_NORTH)

    def test_all_unit_types_can_enter_fortress(self):
        """All mobile unit types can enter fortress."""
        board = Board()

        for unit_type in ["INFANTRY", "CAVALRY", "CANNON", "RELAY"]:
            board.create_and_place_unit(5, 10, unit_type, PLAYER_NORTH)
            board.set_terrain(5, 11, "FORTRESS")

            # Can move into fortress
            assert is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

            board.clear_square(5, 10)
            board.set_terrain(5, 11, None)


class TestComplexTerrainPaths:
    """Test movement through complex terrain layouts."""

    def test_path_around_mountain(self):
        """Pathfinding finds route around single mountain."""
        board = Board()
        board.create_and_place_unit(10, 10, "CAVALRY", PLAYER_NORTH)

        # Mountain blocks direct path but allows going around
        board.set_terrain(10, 11, "MOUNTAIN")

        # Can move around mountain (via (11,11) or (9,11))
        assert is_valid_move(board, 10, 10, 10, 12, PLAYER_NORTH)

    def test_pass_through_mountain_range(self):
        """Moving through mountain range via passes."""
        board = Board()
        board.create_and_place_unit(5, 8, "CAVALRY", PLAYER_NORTH)

        # Create mountain range with pass at the middle
        # Mountains blocking direct horizontal path
        board.set_terrain(5, 9, "MOUNTAIN")
        board.set_terrain(4, 9, "MOUNTAIN")
        board.set_terrain(6, 9, "MOUNTAIN")

        # Pass at (5, 9)
        board.set_terrain(5, 9, "MOUNTAIN_PASS")

        # Can move through pass (distance is 1)
        assert is_valid_move(board, 5, 8, 5, 9, PLAYER_NORTH)


class TestUnitTerrainCoexistence:
    """Test units and terrain coexistence during movement."""

    def test_cannot_move_onto_enemy_in_pass(self):
        """Cannot move onto enemy unit on mountain pass."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(5, 11, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(5, 11, "MOUNTAIN_PASS")

        # Cannot move onto enemy even in pass
        assert not is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_cannot_move_onto_friendly_in_pass(self):
        """Cannot move onto friendly unit in mountain pass."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(5, 11, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "MOUNTAIN_PASS")

        # Cannot move onto friendly even in pass
        assert not is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_cannot_move_onto_enemy_in_fortress(self):
        """Cannot move onto enemy unit in fortress."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", PLAYER_NORTH)
        board.create_and_place_unit(5, 11, "INFANTRY", PLAYER_SOUTH)
        board.set_terrain(5, 11, "FORTRESS")

        # Cannot move onto enemy even in fortress
        assert not is_valid_move(board, 5, 10, 5, 11, PLAYER_NORTH)

    def test_can_move_out_of_pass(self):
        """Unit can move out of mountain pass."""
        board = Board()
        board.create_and_place_unit(5, 11, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "MOUNTAIN_PASS")

        # Can move out of pass
        assert is_valid_move(board, 5, 11, 5, 10, PLAYER_NORTH)
        assert is_valid_move(board, 5, 11, 5, 12, PLAYER_NORTH)

    def test_can_move_out_of_fortress(self):
        """Unit can move out of fortress."""
        board = Board()
        board.create_and_place_unit(5, 11, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 11, "FORTRESS")

        # Can move out of fortress
        assert is_valid_move(board, 5, 11, 5, 10, PLAYER_NORTH)
        assert is_valid_move(board, 5, 11, 5, 12, PLAYER_NORTH)
