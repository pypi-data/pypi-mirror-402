"""Test suite for movement system (patch 0.1.2)."""

import warnings

import pytest

from pykrieg import Board, create_piece
from pykrieg.movement import (
    can_move,
    execute_move,
    generate_moves,
    get_movement_range,
    is_valid_move,
)


class TestMovementGeneration:
    """Test move generation for all unit types."""

    def test_infantry_movement_center(self):
        """Test Infantry has 8 moves from center position."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 8

        # Check all adjacent squares are included
        expected_moves = [
            (9, 11), (9, 12), (9, 13),
            (10, 11), (10, 13),
            (11, 11), (11, 12), (11, 13)
        ]
        assert set(moves) == set(expected_moves)

    def test_infantry_movement_corner(self):
        """Test Infantry has 3 moves from corner."""
        board = Board()
        board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

        moves = generate_moves(board, 0, 0)
        assert len(moves) == 3

        expected_moves = [(0, 1), (1, 0), (1, 1)]
        assert set(moves) == set(expected_moves)

    def test_infantry_movement_edge(self):
        """Test Infantry has 5 moves from edge."""
        board = Board()
        board.create_and_place_unit(0, 12, "INFANTRY", "NORTH")

        moves = generate_moves(board, 0, 12)
        assert len(moves) == 5

        expected_moves = [(0, 11), (0, 13), (1, 11), (1, 12), (1, 13)]
        assert set(moves) == set(expected_moves)

    def test_cavalry_movement_center(self):
        """Test Cavalry has 24 moves from center position."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 24

        # Check corners of movement area are included
        assert (8, 10) in moves  # Top-left corner
        assert (8, 14) in moves  # Top-right corner
        assert (12, 10) in moves  # Bottom-left corner
        assert (12, 14) in moves  # Bottom-right corner

    def test_cavalry_movement_corner(self):
        """Test Cavalry has fewer moves from corner due to boundaries."""
        board = Board()
        board.create_and_place_unit(0, 0, "CAVALRY", "NORTH")

        moves = generate_moves(board, 0, 0)
        # Maximum possible moves from corner with range 2
        assert len(moves) == 8

    def test_cannon_movement(self):
        """Test Cannon has same movement as Infantry."""
        board = Board()
        board.create_and_place_unit(10, 12, "CANNON", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 8

    def test_swift_cannon_movement(self):
        """Test Swift Cannon has same movement as Cavalry."""
        board = Board()
        board.create_and_place_unit(10, 12, "SWIFT_CANNON", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 24

    def test_relay_movement(self):
        """Test Relay has movement (not immobile)."""
        board = Board()
        board.create_and_place_unit(10, 12, "RELAY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 8

    def test_swift_relay_movement(self):
        """Test Swift Relay has extended movement."""
        board = Board()
        board.create_and_place_unit(10, 12, "SWIFT_RELAY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 24

    def test_terrain_no_movement(self):
        """Test terrain (arsenal) has no legal moves - units are required."""
        board = Board()
        board.set_arsenal(10, 12, "NORTH")

        # No unit at arsenal square
        with pytest.raises(ValueError, match="No unit at position"):
            generate_moves(board, 10, 12)


class TestMoveValidation:
    """Test move validation logic."""

    def test_valid_move_adjacent(self):
        """Test adjacent move is valid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        assert is_valid_move(board, 10, 12, 11, 13, "NORTH") is True

    def test_valid_move_diagonal(self):
        """Test diagonal move is valid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        assert is_valid_move(board, 10, 12, 9, 11, "NORTH") is True

    def test_valid_move_same_square_invalid(self):
        """Test moving to same square is invalid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        assert is_valid_move(board, 10, 12, 10, 12, "NORTH") is False

    def test_invalid_move_out_of_bounds(self):
        """Test move out of bounds is invalid."""
        board = Board()
        board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

        assert is_valid_move(board, 0, 0, -1, 0, "NORTH") is False
        assert is_valid_move(board, 0, 0, 0, -1, "NORTH") is False

    def test_invalid_move_beyond_range(self):
        """Test move beyond range is invalid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Infantry has range 1, cannot move 2 squares
        assert is_valid_move(board, 10, 12, 8, 12, "NORTH") is False

    def test_invalid_move_occupied_friendly(self):
        """Test move to occupied square (friendly) is invalid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")

        assert is_valid_move(board, 10, 12, 11, 13, "NORTH") is False

    def test_invalid_move_occupied_enemy(self):
        """Test move to occupied square (enemy) is invalid."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(11, 13, "CAVALRY", "SOUTH")

        assert is_valid_move(board, 10, 12, 11, 13, "NORTH") is False

    def test_invalid_no_unit_at_source(self):
        """Test move from empty square is invalid."""
        board = Board()

        assert is_valid_move(board, 10, 12, 11, 13, "NORTH") is False

    def test_cavalry_range_2_valid(self):
        """Test Cavalry can move 2 squares."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        assert is_valid_move(board, 10, 12, 8, 12, "NORTH") is True  # Up 2
        assert is_valid_move(board, 10, 12, 12, 12, "NORTH") is True  # Down 2
        assert is_valid_move(board, 10, 12, 10, 10, "NORTH") is True  # Left 2
        assert is_valid_move(board, 10, 12, 10, 14, "NORTH") is True  # Right 2



class TestMoveExecution:
    """Test move execution logic."""

    def test_execute_move_updates_board(self):
        """Test execute_move updates board correctly."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        moved_unit = execute_move(board, 10, 12, 11, 13)

        # Unit moved
        assert board.get_unit(10, 12) is None
        assert board.get_unit(11, 13) == moved_unit
        assert moved_unit.unit_type == "INFANTRY"

    def test_execute_move_returns_unit(self):
        """Test execute_move returns the moved unit."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        moved_unit = execute_move(board, 10, 12, 12, 14)

        assert moved_unit.unit_type == "CAVALRY"
        assert moved_unit.owner == "NORTH"

    def test_execute_move_invalid_raises_error(self):
        """Test execute_move raises error for invalid move."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Invalid move (occupied)
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")

        with pytest.raises(ValueError, match="Invalid move"):
            execute_move(board, 10, 12, 11, 13)

    def test_execute_move_sequence(self):
        """Test executing multiple moves in sequence."""
        board = Board()
        # Add arsenal so units are online (0.2.0 network system)
        board.set_arsenal(9, 12, "NORTH")
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        # Place cavalry close enough to be connected via infantry's network coverage
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")

        # First move
        execute_move(board, 10, 12, 10, 13)
        assert board.get_unit(10, 13) is not None
        assert board.get_unit(10, 12) is None

        # Second move
        execute_move(board, 11, 13, 12, 14)
        assert board.get_unit(12, 14) is not None
        assert board.get_unit(11, 13) is None


class TestUnitMovementRange:
    """Test movement range properties of units."""

    def test_infantry_range(self):
        """Test Infantry has range 1."""
        unit = create_piece("INFANTRY", "NORTH")
        assert get_movement_range(unit) == 1
        assert can_move(unit) is True

    def test_cavalry_range(self):
        """Test Cavalry has range 2."""
        unit = create_piece("CAVALRY", "NORTH")
        assert get_movement_range(unit) == 2
        assert can_move(unit) is True

    def test_cannon_range(self):
        """Test Cannon has range 1."""
        unit = create_piece("CANNON", "NORTH")
        assert get_movement_range(unit) == 1
        assert can_move(unit) is True

    def test_swift_cannon_range(self):
        """Test Swift Cannon has range 2."""
        unit = create_piece("SWIFT_CANNON", "NORTH")
        assert get_movement_range(unit) == 2
        assert can_move(unit) is True

    def test_relay_range(self):
        """Test Relay has range 1."""
        unit = create_piece("RELAY", "NORTH")
        assert get_movement_range(unit) == 1
        assert can_move(unit) is True

    def test_swift_relay_range(self):
        """Test Swift Relay has range 2."""
        unit = create_piece("SWIFT_RELAY", "NORTH")
        assert get_movement_range(unit) == 2
        assert can_move(unit) is True

    def test_terrain_no_unit(self):
        """Test that terrain (arsenal) doesn't have a unit to test."""
        # Arsenals are terrain now, not units
        # This test is removed since create_piece("ARSENAL") is invalid
        pass


class TestBoardEdgeCases:
    """Test movement at board boundaries."""

    def test_top_left_corner(self):
        """Test movement from top-left corner."""
        board = Board()
        board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

        moves = generate_moves(board, 0, 0)
        assert len(moves) == 3
        assert (0, 1) in moves
        assert (1, 0) in moves
        assert (1, 1) in moves

    def test_top_right_corner(self):
        """Test movement from top-right corner."""
        board = Board()
        board.create_and_place_unit(0, 24, "INFANTRY", "NORTH")

        moves = generate_moves(board, 0, 24)
        assert len(moves) == 3

    def test_bottom_left_corner(self):
        """Test movement from bottom-left corner."""
        board = Board()
        board.create_and_place_unit(19, 0, "INFANTRY", "SOUTH")

        moves = generate_moves(board, 19, 0)
        assert len(moves) == 3

    def test_bottom_right_corner(self):
        """Test movement from bottom-right corner."""
        board = Board()
        board.create_and_place_unit(19, 24, "INFANTRY", "SOUTH")

        moves = generate_moves(board, 19, 24)
        assert len(moves) == 3

    def test_top_edge(self):
        """Test movement from top edge."""
        board = Board()
        board.create_and_place_unit(0, 12, "CAVALRY", "NORTH")

        moves = generate_moves(board, 0, 12)
        # More moves than corner, fewer than center
        assert len(moves) > 3
        assert len(moves) < 24

    def test_bottom_edge(self):
        """Test movement from bottom edge."""
        board = Board()
        board.create_and_place_unit(19, 12, "CAVALRY", "SOUTH")

        moves = generate_moves(board, 19, 12)
        assert len(moves) > 3
        assert len(moves) < 24

    def test_left_edge(self):
        """Test movement from left edge."""
        board = Board()
        board.create_and_place_unit(10, 0, "CAVALRY", "NORTH")

        moves = generate_moves(board, 10, 0)
        assert len(moves) > 3
        assert len(moves) < 24

    def test_right_edge(self):
        """Test movement from right edge."""
        board = Board()
        board.create_and_place_unit(10, 24, "CAVALRY", "NORTH")

        moves = generate_moves(board, 10, 24)
        assert len(moves) > 3
        assert len(moves) < 24


class TestBlockedMovement:
    """Test movement with blocked squares."""

    def test_single_blocked_square(self):
        """Test movement with one blocked square."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 7  # 8 total - 1 blocked
        assert (11, 13) not in moves

    def test_multiple_blocked_squares(self):
        """Test movement with multiple blocked squares."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Block 3 adjacent squares
        board.create_and_place_unit(9, 12, "CAVALRY", "NORTH")
        board.create_and_place_unit(11, 12, "CAVALRY", "NORTH")
        board.create_and_place_unit(10, 13, "CAVALRY", "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 5  # 8 total - 3 blocked

    def test_friendly_and_enemy_blocks(self):
        """Test both friendly and enemy units block movement."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Block with friendly
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")
        # Block with enemy
        board.create_and_place_unit(9, 11, "CAVALRY", "SOUTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 6  # 8 total - 2 blocked


class TestMovementIntegration:
    """Test movement in realistic scenarios."""

    def test_full_board_movement(self):
        """Test movement with units across the board."""
        board = Board()

        # Place units in various positions
        board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
        board.create_and_place_unit(0, 24, "CAVALRY", "NORTH")
        board.create_and_place_unit(10, 12, "CANNON", "NORTH")
        board.create_and_place_unit(19, 0, "INFANTRY", "SOUTH")
        board.create_and_place_unit(19, 24, "CAVALRY", "SOUTH")

        # Test each unit can move
        assert len(generate_moves(board, 0, 0)) == 3
        assert len(generate_moves(board, 0, 24)) == 8  # Cavalry range 2 from corner
        assert len(generate_moves(board, 10, 12)) == 8
        assert len(generate_moves(board, 19, 0)) == 3
        assert len(generate_moves(board, 19, 24)) == 8  # Cavalry range 2 from corner

    def test_movement_sequence(self):
        """Test sequence of moves on same unit."""
        board = Board()
        # Add arsenal and multiple relays to ensure continuous network coverage (0.2.0 network system)
        # Relays create a network path for cavalry to move through
        board.set_arsenal(9, 12, "NORTH")
        board.create_and_place_unit(10, 13, "RELAY", "NORTH")
        board.create_and_place_unit(11, 14, "RELAY", "NORTH")
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        # Move step by step - cavalry stays connected via relay network
        execute_move(board, 10, 12, 11, 13)
        assert board.get_unit(11, 13) is not None

        execute_move(board, 11, 13, 12, 14)
        assert board.get_unit(12, 14) is not None

        execute_move(board, 12, 14, 13, 15)
        assert board.get_unit(13, 15) is not None

    def test_crowded_area(self):
        """Test movement in crowded area with many units."""
        board = Board()

        # Create a cluster of units (arsenal as terrain)
        board.set_arsenal(11, 13, "NORTH")
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")
        board.create_and_place_unit(10, 13, "CAVALRY", "NORTH")
        board.create_and_place_unit(11, 12, "CANNON", "NORTH")

        # Center unit has limited moves
        moves = generate_moves(board, 10, 12)
        assert len(moves) < 8  # Some squares blocked


class TestBoardConvenienceMethods:
    """Test Board convenience methods for movement."""

    def test_board_get_legal_moves(self):
        """Test Board.get_legal_moves wrapper."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        moves = board.get_legal_moves(10, 12)
        assert len(moves) == 8

    def test_board_is_legal_move(self):
        """Test Board.is_legal_move wrapper."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        assert board.is_legal_move(10, 12, 11, 13) is True
        assert board.is_legal_move(10, 12, 10, 12) is False

    def test_board_make_move(self):
        """Test Board.make_move wrapper."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        moved_unit = board.make_move(10, 12, 11, 13)
        assert moved_unit.unit_type == "INFANTRY"
        assert board.get_unit(11, 13) is not None


class TestErrorHandling:
    """Test error messages and edge cases."""

    def test_generate_moves_no_unit_at_position(self):
        """Test generate_moves raises error when no unit at position."""
        board = Board()

        with pytest.raises(ValueError, match="No unit at position"):
            generate_moves(board, 10, 12)

    def test_generate_moves_invalid_coordinates(self):
        """Test generate_moves handles invalid coordinates."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Should raise when trying to get unit from invalid coordinates
        with pytest.raises(ValueError, match="Invalid coordinates"):
            generate_moves(board, -1, 12)

    def test_execute_move_invalid_error_message(self):
        """Test execute_move provides descriptive error message."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        with pytest.raises(ValueError, match="Invalid move from \\(10, 12\\) to \\(20, 12\\)"):
            execute_move(board, 10, 12, 20, 12)

    def test_is_valid_move_empty_source(self):
        """Test is_valid_move returns False for empty source."""
        board = Board()

        assert is_valid_move(board, 10, 12, 11, 13, "NORTH") is False


class TestBoundaryValues:
    """Systematic testing of boundary values."""

    def test_movement_range_0(self):
        """Test movement range 0 (Arsenal as terrain, no unit)."""
        board = Board()
        board.set_arsenal(10, 12, "NORTH")

        # No unit at arsenal position (it's terrain now)
        assert board.get_unit(10, 12) is None

    def test_movement_range_1(self):
        """Test movement range 1 (Infantry)."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        assert get_movement_range(board.get_unit(10, 12)) == 1
        assert can_move(board.get_unit(10, 12)) is True
        assert len(generate_moves(board, 10, 12)) == 8

    def test_movement_range_2(self):
        """Test movement range 2 (Cavalry)."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        assert get_movement_range(board.get_unit(10, 12)) == 2
        assert can_move(board.get_unit(10, 12)) is True
        assert len(generate_moves(board, 10, 12)) == 24

    @pytest.mark.parametrize("position,expected_moves", [
        ((0, 0), 3),      # Top-left corner
        ((0, 12), 5),     # Top edge
        ((0, 24), 3),     # Top-right corner
        ((10, 0), 5),     # Left edge
        ((10, 12), 8),    # Center
        ((10, 24), 5),    # Right edge
        ((19, 0), 3),     # Bottom-left corner
        ((19, 12), 5),    # Bottom edge
        ((19, 24), 3),    # Bottom-right corner
    ])
    def test_infantry_boundary_positions(self, position, expected_moves):
        """Test Infantry movement at various boundary positions."""
        row, col = position
        board = Board()
        board.create_and_place_unit(row, col, "INFANTRY", "NORTH")

        moves = generate_moves(board, row, col)
        assert len(moves) == expected_moves


class TestAllUnitTypesParametrized:
    """Parametrized tests for all unit types."""

    @pytest.mark.parametrize("unit_type,expected_range,expected_max_moves", [
        ("INFANTRY", 1, 8),
        ("CAVALRY", 2, 24),
        ("CANNON", 1, 8),
        ("SWIFT_CANNON", 2, 24),
        ("RELAY", 1, 8),
        ("SWIFT_RELAY", 2, 24),
    ])
    def test_unit_movement_range_and_max_moves(self, unit_type, expected_range, expected_max_moves):
        """Test all unit types have correct movement range and max moves from center."""
        board = Board()
        board.create_and_place_unit(10, 12, unit_type, "NORTH")

        unit = board.get_unit(10, 12)
        assert get_movement_range(unit) == expected_range
        assert can_move(unit) == (expected_range > 0)

        moves = generate_moves(board, 10, 12)
        assert len(moves) == expected_max_moves

    @pytest.mark.parametrize("unit_type", [
        "INFANTRY", "CAVALRY", "CANNON", "SWIFT_CANNON", "RELAY", "SWIFT_RELAY"
    ])
    def test_unit_cannot_move_to_same_square(self, unit_type):
        """Test all unit types cannot move to same square."""
        board = Board()
        board.create_and_place_unit(10, 12, unit_type, "NORTH")

        assert is_valid_move(board, 10, 12, 10, 12, "NORTH") is False

    @pytest.mark.parametrize("unit_type", [
        "INFANTRY", "CAVALRY", "CANNON", "SWIFT_CANNON", "RELAY", "SWIFT_RELAY"
    ])
    def test_mobile_units_have_legal_moves(self, unit_type):
        """Test all mobile units have at least some legal moves from center."""
        board = Board()
        board.create_and_place_unit(10, 12, unit_type, "NORTH")

        moves = generate_moves(board, 10, 12)
        assert len(moves) > 0

    @pytest.mark.parametrize("owner", ["NORTH", "SOUTH"])
    def test_movement_independent_of_owner(self, owner):
        """Test movement is same for both owners."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", owner)

        moves = generate_moves(board, 10, 12)
        assert len(moves) == 24  # Cavalry always has 24 moves from center


class TestDeprecatedMethods:
    """Test deprecated methods still work but warn."""

    def test_get_piece_deprecation_warning(self):
        """Test get_piece shows deprecation warning."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            board.get_piece(10, 12)

            # Should have raised DeprecationWarning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_piece() is deprecated" in str(w[0].message)

    def test_set_piece_deprecation_warning(self):
        """Test set_piece shows deprecation warning."""
        board = Board()

        unit = create_piece("INFANTRY", "NORTH")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            board.set_piece(10, 12, unit)

            # Should have raised DeprecationWarning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "set_piece() is deprecated" in str(w[0].message)

    def test_deprecated_methods_still_functional(self):
        """Test deprecated methods still work correctly."""
        board = Board()

        from pykrieg.pieces import Infantry
        unit = Infantry("NORTH")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress warnings

            board.set_piece(10, 12, unit)
            retrieved = board.get_piece(10, 12)

            assert retrieved == unit
            assert retrieved.unit_type == "INFANTRY"


class TestRegression:
    """Regression tests to prevent future bugs."""

    def test_mixed_owners_block_movement(self):
        """Regression: Both friendly and enemy units should block movement."""
        board = Board()
        board.create_and_place_unit(10, 12, "INFANTRY", "NORTH")

        # Block with friendly
        board.create_and_place_unit(11, 13, "CAVALRY", "NORTH")
        moves_with_friendly = len(generate_moves(board, 10, 12))

        # Move blocking unit
        board.clear_square(11, 13)

        # Block with enemy
        board.create_and_place_unit(11, 13, "CAVALRY", "SOUTH")
        moves_with_enemy = len(generate_moves(board, 10, 12))

        # Both should block equally
        assert moves_with_friendly == moves_with_enemy

    def test_unit_properties_unchanged_after_move(self):
        """Regression: Unit properties should not change after moving."""
        board = Board()
        board.create_and_place_unit(10, 12, "CAVALRY", "NORTH")

        unit_before = board.get_unit(10, 12)
        execute_move(board, 10, 12, 12, 14)
        unit_after = board.get_unit(12, 14)

        # Properties should be identical
        assert unit_after.unit_type == unit_before.unit_type
        assert unit_after.owner == unit_before.owner
        assert unit_after.attack == unit_before.attack
        assert unit_after.defense == unit_before.defense
        assert unit_after.movement == unit_before.movement
        assert unit_after.range == unit_before.range
