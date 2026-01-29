"""Comprehensive test suite for Pykrieg unit type system.

Tests cover all 6 unit types with correct statistics from official rules:
- Infantry: Atk 4 / Def 6 / Move 1 / Range 2
- Cavalry: Atk 4 / Def 5 / Move 2 / Range 2
- Cannon: Atk 5 / Def 8 / Move 1 / Range 3
- Relay: Atk 0 / Def 1 / Move 1 / Range 0
- Swift Cannon: Atk 5 / Def 8 / Move 2 / Range 3
- Swift Relay: Atk 0 / Def 1 / Move 2 / Range 0
"""

import pytest

from pykrieg.board import Board
from pykrieg.pieces import (
    Cannon,
    Cavalry,
    Infantry,
    Relay,
    SwiftCannon,
    SwiftRelay,
    Unit,
    create_piece,
)

# =============================================================================
# Unit Attribute Tests
# =============================================================================

def test_infantry_stats():
    """Test Infantry has correct stats from rules."""
    unit = Infantry("NORTH")
    assert unit.unit_type == "INFANTRY"
    assert unit.attack == 4
    assert unit.defense == 6
    assert unit.movement == 1
    assert unit.range == 2
    assert unit.owner == "NORTH"
    assert unit.is_combat_unit() is True
    assert unit.is_structure() is False


def test_cavalry_stats():
    """Test Cavalry has correct stats from rules."""
    unit = Cavalry("SOUTH")
    assert unit.unit_type == "CAVALRY"
    assert unit.attack == 4
    assert unit.defense == 5
    assert unit.movement == 2
    assert unit.range == 2
    assert unit.owner == "SOUTH"
    assert unit.is_combat_unit() is True
    assert unit.is_structure() is False


def test_cannon_stats():
    """Test Cannon has correct stats from rules."""
    unit = Cannon("NORTH")
    assert unit.unit_type == "CANNON"
    assert unit.attack == 5
    assert unit.defense == 8
    assert unit.movement == 1
    assert unit.range == 3
    assert unit.is_combat_unit() is True
    assert unit.is_structure() is False


def test_relay_stats():
    """Test Relay has correct stats from rules."""
    unit = Relay("NORTH")
    assert unit.unit_type == "RELAY"
    assert unit.attack == 0
    assert unit.defense == 1
    assert unit.movement == 1
    assert unit.range == 0
    assert unit.is_combat_unit() is False
    assert unit.is_structure() is False


def test_swift_cannon_stats():
    """Test Swift Cannon has correct stats from rules."""
    unit = SwiftCannon("SOUTH")
    assert unit.unit_type == "SWIFT_CANNON"
    assert unit.attack == 5
    assert unit.defense == 8
    assert unit.movement == 2
    assert unit.range == 3
    assert unit.is_combat_unit() is True
    assert unit.is_structure() is False


def test_swift_relay_stats():
    """Test Swift Relay has correct stats from rules."""
    unit = SwiftRelay("NORTH")
    assert unit.unit_type == "SWIFT_RELAY"
    assert unit.attack == 0
    assert unit.defense == 1
    assert unit.movement == 2
    assert unit.range == 0
    assert unit.is_combat_unit() is False
    assert unit.is_structure() is False  # Can move, so not a structure


def test_stats_immutability():
    """Test unit stats are class attributes."""
    unit = Infantry("NORTH")
    # Stats are class attributes, not instance attributes
    # Setting an instance attribute creates a shadow, but doesn't affect class
    assert Infantry.attack == 4
    assert unit.attack == 4

    # Setting on instance creates instance attribute
    unit.attack = 99
    assert unit.attack == 99
    assert Infantry.attack == 4  # Class stat unchanged


# =============================================================================
# Unit Creation Tests
# =============================================================================

def test_factory_function_all_types():
    """Test create_piece for all unit types."""
    unit_types = [
        "INFANTRY", "CAVALRY", "CANNON", "RELAY",
        "SWIFT_CANNON", "SWIFT_RELAY"
    ]
    for unit_type in unit_types:
        unit = create_piece(unit_type, "NORTH")
        assert isinstance(unit, Unit)
        assert unit.unit_type == unit_type


def test_factory_function_owners():
    """Test create_piece with both owners."""
    for owner in ["NORTH", "SOUTH"]:
        unit = create_piece("INFANTRY", owner)
        assert unit.owner == owner


def test_factory_function_invalid_type():
    """Test create_piece raises error for invalid type."""
    with pytest.raises(ValueError, match="Invalid unit type"):
        create_piece("DRAGON", "NORTH")


def test_factory_function_invalid_owner():
    """Test create_piece raises error for invalid owner."""
    with pytest.raises(ValueError, match="Invalid owner"):
        create_piece("INFANTRY", "EAST")


def test_direct_instantiation():
    """Test direct instantiation of unit classes."""
    infantry = Infantry("NORTH")
    assert isinstance(infantry, Unit)
    assert infantry.unit_type == "INFANTRY"


def test_invalid_owner_direct():
    """Test direct instantiation accepts any owner (validation in factory)."""
    # Direct instantiation doesn't validate owner
    # This is intentional - factory does validation
    unit = Infantry("DRAGON")
    assert unit.owner == "DRAGON"


# =============================================================================
# Unit Equality and Hashing Tests
# =============================================================================

def test_unit_equality_same_type_owner():
    """Test units are equal when type and owner match."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("NORTH")
    assert unit1 == unit2


def test_unit_equality_different_type():
    """Test units are not equal when types differ."""
    unit1 = Infantry("NORTH")
    unit2 = Cavalry("NORTH")
    assert unit1 != unit2


def test_unit_equality_different_owner():
    """Test units are not equal when owners differ."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("SOUTH")
    assert unit1 != unit2


def test_unit_equality_with_non_unit():
    """Test unit is not equal to non-unit objects."""
    unit = Infantry("NORTH")
    assert unit != "INFANTRY"
    assert unit is not None


def test_unit_hash():
    """Test units are hashable and use correct hash."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("NORTH")
    unit3 = Cavalry("NORTH")

    # Same units should have same hash
    assert hash(unit1) == hash(unit2)

    # Different units should have different hashes (usually)
    # Note: Hash collisions are possible but unlikely
    units_set = {unit1, unit2, unit3}
    assert len(units_set) == 2  # unit1 and unit2 are equal


# =============================================================================
# Unit Representation Tests
# =============================================================================

def test_unit_repr():
    """Test unit string representation."""
    unit = Infantry("NORTH")
    assert repr(unit) == "INFANTRY(NORTH)"

    unit = Cavalry("SOUTH")
    assert repr(unit) == "CAVALRY(SOUTH)"


# =============================================================================
# Unit Placement Tests
# =============================================================================

def test_place_unit_valid_square():
    """Test placing unit on valid square."""
    board = Board()
    unit = Infantry("NORTH")
    board.place_unit(5, 10, unit)
    assert board.get_unit(5, 10) == unit


def test_place_unit_invalid_coordinates():
    """Test placing unit on invalid coordinates raises error."""
    board = Board()
    unit = Infantry("NORTH")
    with pytest.raises(ValueError, match="Invalid coordinates"):
        board.place_unit(-1, 0, unit)


def test_place_unit_overwrite():
    """Test overwriting existing unit."""
    board = Board()
    unit1 = Infantry("NORTH")
    unit2 = Cavalry("NORTH")

    board.place_unit(5, 10, unit1)
    assert board.get_unit(5, 10) == unit1

    board.place_unit(5, 10, unit2)
    assert board.get_unit(5, 10) == unit2


def test_create_and_place_unit():
    """Test create_and_place_unit convenience method."""
    board = Board()
    unit = board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

    assert unit.unit_type == "INFANTRY"
    assert unit.owner == "NORTH"
    assert board.get_unit(5, 10) == unit


def test_create_and_place_invalid_type():
    """Test create_and_place with invalid type."""
    board = Board()
    with pytest.raises(ValueError, match="Invalid unit type"):
        board.create_and_place_unit(5, 10, "DRAGON", "NORTH")


def test_clear_unit():
    """Test clearing unit from square."""
    board = Board()
    unit = Infantry("NORTH")
    board.place_unit(5, 10, unit)
    assert board.get_unit(5, 10) == unit

    board.clear_square(5, 10)
    assert board.get_unit(5, 10) is None


# =============================================================================
# Query Method Tests
# =============================================================================

def test_get_unit():
    """Test get_unit returns Unit object."""
    board = Board()
    unit = Infantry("NORTH")
    board.place_unit(5, 10, unit)

    retrieved_unit = board.get_unit(5, 10)
    assert retrieved_unit == unit
    assert retrieved_unit is not None


def test_get_unit_empty_square():
    """Test get_unit returns None for empty square."""
    board = Board()
    assert board.get_unit(5, 10) is None


def test_get_unit_type():
    """Test get_unit_type returns correct string."""
    board = Board()
    board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

    assert board.get_unit_type(5, 10) == "INFANTRY"
    assert board.get_unit_type(0, 0) is None


def test_get_unit_owner():
    """Test get_unit_owner returns correct owner."""
    board = Board()
    board.create_and_place_unit(5, 10, "CAVALRY", "SOUTH")

    assert board.get_unit_owner(5, 10) == "SOUTH"
    assert board.get_unit_owner(0, 0) is None


def test_count_units_all():
    """Test counting all units."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    assert board.count_units() == 3


def test_count_units_by_type():
    """Test counting units by type."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    assert board.count_units(unit_type="INFANTRY") == 2
    assert board.count_units(unit_type="CAVALRY") == 1
    assert board.count_units(unit_type="CANNON") == 0


def test_count_units_by_owner():
    """Test counting units by owner."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    assert board.count_units(owner="NORTH") == 2
    assert board.count_units(owner="SOUTH") == 1


def test_count_units_by_type_and_owner():
    """Test counting units by both type and owner."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    assert board.count_units(unit_type="INFANTRY", owner="NORTH") == 1
    assert board.count_units(unit_type="INFANTRY", owner="SOUTH") == 1
    assert board.count_units(unit_type="CAVALRY", owner="NORTH") == 1


def test_get_units_by_type():
    """Test getting all units of a specific type."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    infantry = board.get_units_by_type("INFANTRY")
    assert set(infantry) == {(0, 0), (1, 0)}

    cavalry = board.get_units_by_type("CAVALRY")
    assert cavalry == [(0, 1)]


def test_get_units_by_owner():
    """Test getting all units of a specific owner."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    north_units = board.get_units_by_owner("NORTH")
    assert set(north_units) == {(0, 0), (0, 1)}

    south_units = board.get_units_by_owner("SOUTH")
    assert south_units == [(1, 0)]


def test_get_all_units():
    """Test getting all units on board."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(0, 1, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "SOUTH")

    all_units = board.get_all_units()
    assert len(all_units) == 3
    assert (0, 0) in all_units
    assert (0, 1) in all_units
    assert (1, 0) in all_units

    assert all_units[(0, 0)].unit_type == "INFANTRY"
    assert all_units[(0, 1)].unit_type == "CAVALRY"


# =============================================================================
# Validation Method Tests
# =============================================================================

def test_is_valid_unit_type():
    """Test unit type validation."""
    board = Board()

    assert board.is_valid_unit_type("INFANTRY") is True
    assert board.is_valid_unit_type("CAVALRY") is True
    assert board.is_valid_unit_type("CANNON") is True
    assert board.is_valid_unit_type("RELAY") is True
    assert board.is_valid_unit_type("SWIFT_CANNON") is True
    assert board.is_valid_unit_type("SWIFT_RELAY") is True
    assert board.is_valid_unit_type("ARSENAL") is False  # Now a terrain type, not a unit
    assert board.is_valid_unit_type("DRAGON") is False


def test_is_valid_owner():
    """Test owner validation."""
    board = Board()

    assert board.is_valid_owner("NORTH") is True
    assert board.is_valid_owner("SOUTH") is True
    assert board.is_valid_owner("EAST") is False
    assert board.is_valid_owner("WEST") is False


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_board_setup():
    """Test setting up a board with multiple units."""
    board = Board()

    # Place various units (arsenals as terrain)
    board.set_arsenal(0, 0, "NORTH")
    board.create_and_place_unit(0, 5, "RELAY", "NORTH")
    board.create_and_place_unit(1, 0, "INFANTRY", "NORTH")
    board.create_and_place_unit(1, 1, "INFANTRY", "NORTH")
    board.create_and_place_unit(1, 2, "CAVALRY", "NORTH")
    board.create_and_place_unit(1, 3, "CANNON", "NORTH")

    board.set_arsenal(19, 0, "SOUTH")
    board.create_and_place_unit(19, 5, "RELAY", "SOUTH")
    board.create_and_place_unit(18, 0, "INFANTRY", "SOUTH")
    board.create_and_place_unit(18, 1, "INFANTRY", "SOUTH")
    board.create_and_place_unit(18, 2, "CAVALRY", "SOUTH")
    board.create_and_place_unit(18, 3, "CANNON", "SOUTH")

    # Verify counts (arsenals are terrain, not units)
    assert board.count_units(owner="NORTH") == 5
    assert board.count_units(owner="SOUTH") == 5
    assert board.count_units(unit_type="RELAY") == 2
    assert board.count_units(unit_type="INFANTRY") == 4
    assert board.count_units(unit_type="CAVALRY") == 2
    assert board.count_units(unit_type="CANNON") == 2


def test_swift_units_integration():
    """Test swift units in board setup."""
    board = Board()

    board.create_and_place_unit(0, 10, "SWIFT_CANNON", "NORTH")
    board.create_and_place_unit(1, 10, "SWIFT_RELAY", "NORTH")

    # Verify swift units are correctly placed
    swift_cannon = board.get_unit(0, 10)
    assert swift_cannon.unit_type == "SWIFT_CANNON"
    assert swift_cannon.movement == 2

    swift_relay = board.get_unit(1, 10)
    assert swift_relay.unit_type == "SWIFT_RELAY"
    assert swift_relay.movement == 2
    assert swift_relay.is_structure() is False


# =============================================================================
# Boundary and Extremity Tests
# =============================================================================

def test_units_at_board_corners():
    """Test units placed at all four corners of the board."""
    board = Board()

    # Place units at all corners
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")      # Top-left
    board.create_and_place_unit(0, 24, "CAVALRY", "NORTH")      # Top-right
    board.create_and_place_unit(19, 0, "INFANTRY", "SOUTH")     # Bottom-left
    board.create_and_place_unit(19, 24, "CAVALRY", "SOUTH")     # Bottom-right

    # Verify all units are placed correctly
    assert board.get_unit(0, 0).unit_type == "INFANTRY"
    assert board.get_unit(0, 24).unit_type == "CAVALRY"
    assert board.get_unit(19, 0).unit_type == "INFANTRY"
    assert board.get_unit(19, 24).unit_type == "CAVALRY"


def test_units_at_territory_boundary():
    """Test units placed at territory boundary rows."""
    board = Board()

    # Place units at boundary rows (9 and 10)
    board.create_and_place_unit(9, 0, "INFANTRY", "NORTH")      # Last row of North
    board.create_and_place_unit(10, 0, "INFANTRY", "SOUTH")     # First row of South

    # Verify territory classification
    assert board.get_territory(9, 0) == "NORTH"
    assert board.get_territory(10, 0) == "SOUTH"


def test_place_unit_full_row():
    """Test placing units on every square of a row."""
    board = Board()

    # Fill an entire row with units
    for col in range(board.cols):
        board.create_and_place_unit(5, col, "INFANTRY", "NORTH")

    # Verify all squares in row 5 have units
    for col in range(board.cols):
        assert board.get_unit(5, col) is not None
        assert board.get_unit_type(5, col) == "INFANTRY"


def test_place_unit_full_column():
    """Test placing units on every square of a column."""
    board = Board()

    # Fill an entire column with units
    for row in range(board.rows):
        board.create_and_place_unit(row, 10, "CAVALRY", "SOUTH")

    # Verify all squares in column 10 have units
    for row in range(board.rows):
        assert board.get_unit(row, 10) is not None
        assert board.get_unit_type(row, 10) == "CAVALRY"


def test_board_with_maximum_units():
    """Test board with maximum number of units (500 units)."""
    board = Board()

    # Fill entire board with units
    for row in range(board.rows):
        for col in range(board.cols):
            board.create_and_place_unit(row, col, "INFANTRY", "NORTH")

    # Verify all squares have units
    assert board.count_units() == 500
    assert board.count_units(unit_type="INFANTRY") == 500


def test_board_with_all_unit_types():
    """Test board with all 6 unit types placed simultaneously."""
    board = Board()

    unit_types = ["INFANTRY", "CAVALRY", "CANNON",
                  "RELAY", "SWIFT_CANNON", "SWIFT_RELAY"]

    # Place one of each unit type
    for i, unit_type in enumerate(unit_types):
        board.create_and_place_unit(0, i, unit_type, "NORTH")

    # Verify all unit types are present
    for unit_type in unit_types:
        assert board.count_units(unit_type=unit_type) == 1


def test_empty_board_queries():
    """Test query methods on empty board."""
    board = Board()

    # All query methods should return empty/None on empty board
    assert board.count_units() == 0
    assert board.get_units_by_type("INFANTRY") == []
    assert board.get_units_by_owner("NORTH") == []
    assert board.get_all_units() == {}
    assert board.get_unit(0, 0) is None
    assert board.get_unit_type(0, 0) is None
    assert board.get_unit_owner(0, 0) is None


def test_board_with_single_unit_type():
    """Test board with units of only one type."""
    board = Board()

    # Place multiple units of same type
    for i in range(10):
        board.create_and_place_unit(0, i, "INFANTRY", "NORTH")

    # Verify counts
    assert board.count_units() == 10
    assert board.count_units(unit_type="INFANTRY") == 10
    assert board.count_units(unit_type="CAVALRY") == 0


def test_board_with_single_owner():
    """Test board with units owned by only one player."""
    board = Board()

    # Place units for only North player
    for i in range(10):
        board.create_and_place_unit(0, i, "INFANTRY", "NORTH")

    # Verify counts
    assert board.count_units() == 10
    assert board.count_units(owner="NORTH") == 10
    assert board.count_units(owner="SOUTH") == 0


# =============================================================================
# Type System Edge Cases
# =============================================================================

def test_unit_with_invalid_values():
    """Test unit accepts invalid values in direct instantiation."""
    # Direct instantiation doesn't validate (intentional)
    unit = Infantry("DRAGON")
    assert unit.owner == "DRAGON"

    unit = Cavalry("")
    assert unit.owner == ""


def test_factory_case_sensitivity():
    """Test factory function is case-sensitive for unit types."""
    # Valid uppercase should work
    unit = create_piece("INFANTRY", "NORTH")
    assert unit.unit_type == "INFANTRY"

    # Lowercase should fail
    with pytest.raises(ValueError, match="Invalid unit type"):
        create_piece("infantry", "NORTH")

    # Mixed case should fail
    with pytest.raises(ValueError, match="Invalid unit type"):
        create_piece("Infantry", "NORTH")


def test_factory_case_sensitivity_owner():
    """Test factory function is case-sensitive for owners."""
    # Valid uppercase should work
    unit = create_piece("INFANTRY", "NORTH")
    assert unit.owner == "NORTH"

    # Lowercase should fail
    with pytest.raises(ValueError, match="Invalid owner"):
        create_piece("INFANTRY", "north")

    # Mixed case should fail
    with pytest.raises(ValueError, match="Invalid owner"):
        create_piece("INFANTRY", "North")


def test_units_with_same_stats_equal():
    """Test units with same stats and owner are equal."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("NORTH")
    assert unit1 == unit2
    assert hash(unit1) == hash(unit2)


def test_units_different_instances_equal():
    """Test different instances with same type/owner are equal."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("NORTH")
    assert unit1 is not unit2  # Different instances
    assert unit1 == unit2  # But equal


# =============================================================================
# Query Method Edge Cases
# =============================================================================

def test_get_units_by_type_nonexistent():
    """Test get_units_by_type returns empty list for non-existent type."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

    # Non-existent type should return empty list, not error
    dragons = board.get_units_by_type("DRAGON")
    assert dragons == []


def test_get_units_by_owner_invalid():
    """Test get_units_by_owner returns empty list for invalid owner."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

    # Invalid owner should return empty list, not error
    dragons = board.get_units_by_owner("EAST")
    assert dragons == []


def test_count_units_empty_string_filters():
    """Test count_units handles empty string as filter."""
    board = Board()
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")

    # Empty string should match nothing (not count all)
    assert board.count_units(unit_type="") == 0
    assert board.count_units(owner="") == 0


# =============================================================================
# Overwrite and Collision Edge Cases
# =============================================================================

def test_overwrite_same_type_different_owner():
    """Test overwriting unit with same type but different owner."""
    board = Board()

    # Place North infantry
    board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
    assert board.get_unit_owner(5, 10) == "NORTH"

    # Overwrite with South infantry
    board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
    assert board.get_unit_owner(5, 10) == "SOUTH"


def test_overwrite_structure_with_mobile():
    """Test overwriting structure with mobile unit."""
    board = Board()

    # Place structure (relay has 0 attack and can be considered structure-like)
    board.create_and_place_unit(5, 10, "RELAY", "NORTH")
    assert board.get_unit(5, 10).is_structure() is False  # Relay can move

    # Overwrite with mobile unit
    board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")
    assert board.get_unit(5, 10).is_structure() is False


def test_multiple_overwrites_sequence():
    """Test multiple overwrites in sequence."""
    board = Board()

    unit_types = ["INFANTRY", "CAVALRY", "CANNON", "RELAY"]

    for unit_type in unit_types:
        board.create_and_place_unit(5, 10, unit_type, "NORTH")
        assert board.get_unit_type(5, 10) == unit_type


def test_overwrite_updates_counts():
    """Test that overwriting updates unit counts correctly."""
    board = Board()

    # Place infantry
    board.create_and_place_unit(0, 0, "INFANTRY", "NORTH")
    assert board.count_units(unit_type="INFANTRY") == 1

    # Overwrite with cavalry
    board.create_and_place_unit(0, 0, "CAVALRY", "NORTH")
    assert board.count_units(unit_type="INFANTRY") == 0
    assert board.count_units(unit_type="CAVALRY") == 1


# =============================================================================
# Immutability and Class Attribute Tests
# =============================================================================

def test_stats_are_class_attributes():
    """Test that stats are class attributes, not instance attributes."""
    unit1 = Infantry("NORTH")
    unit2 = Infantry("SOUTH")

    # Stats should be shared across instances
    assert unit1.attack is Infantry.attack
    assert unit2.attack is Infantry.attack


def test_unit_stats_independent_per_class():
    """Test that stats are independent per unit class."""
    infantry = Infantry("NORTH")
    cavalry = Cavalry("NORTH")

    # Stats should be different between classes (defense differs)
    assert infantry.attack == cavalry.attack  # Both have attack 4
    assert infantry.defense != cavalry.defense  # Infantry 6, Cavalry 5
    assert infantry.movement != cavalry.movement  # Infantry 1, Cavalry 2


# =============================================================================
# Property-Based Tests (Hypothesis)
# =============================================================================

hypothesis = pytest.importorskip("hypothesis", reason="requires hypothesis>=6.0.0")
from hypothesis import given
from hypothesis import strategies as st


@given(st.integers(0, 19), st.integers(0, 24))
def test_place_and_retrieve(row, col):
    """Test that placed units can be retrieved correctly."""
    board = Board()
    unit = Infantry("NORTH")

    board.place_unit(row, col, unit)
    retrieved = board.get_unit(row, col)

    assert retrieved == unit
    assert retrieved.unit_type == "INFANTRY"


@given(st.lists(st.tuples(
    st.integers(0, 19),
    st.integers(0, 24),
    st.sampled_from(["INFANTRY", "CAVALRY", "CANNON", "RELAY",
                    "SWIFT_CANNON", "SWIFT_RELAY"]),
    st.sampled_from(["NORTH", "SOUTH"])
), max_size=50))
def test_count_units_invariant(units_to_place):
    """Test that count_units invariant holds for random placements."""
    board = Board()

    # Place units (handle collisions - later placements overwrite earlier)
    for row, col, unit_type, owner in units_to_place:
        board.create_and_place_unit(row, col, unit_type, owner)

    # Verify total count matches all individual type counts
    total = board.count_units()
    type_counts = sum(
        board.count_units(unit_type=ut)
        for ut in ["INFANTRY", "CAVALRY", "CANNON", "RELAY",
                  "SWIFT_CANNON", "SWIFT_RELAY"]
    )

    assert total == type_counts


@given(st.integers(0, 19), st.integers(0, 24),
        st.sampled_from(["NORTH", "SOUTH"]))
def test_unit_territory_placement(row, col, owner):
    """Test that territory classification works correctly."""
    board = Board()

    # Place unit and check territory classification
    board.create_and_place_unit(row, col, "INFANTRY", owner)
    unit = board.get_unit(row, col)
    territory = board.get_territory(row, col)

    # Verify territory is either NORTH or SOUTH
    assert territory in ["NORTH", "SOUTH"]

    # Verify unit was placed
    assert unit is not None
    assert unit.owner == owner

    # Verify territory boundary is at row 10
    if row < 10:
        assert territory == "NORTH"
        assert board.is_north_territory(row, col) is True
        assert board.is_south_territory(row, col) is False
    else:
        assert territory == "SOUTH"
        assert board.is_north_territory(row, col) is False
        assert board.is_south_territory(row, col) is True


@given(st.sampled_from(["INFANTRY", "CAVALRY", "CANNON", "RELAY",
                        "SWIFT_CANNON", "SWIFT_RELAY"]),
        st.sampled_from(["NORTH", "SOUTH"]))
def test_unit_creation_and_properties(unit_type, owner):
    """Test that units created via factory have correct properties."""
    unit = create_piece(unit_type, owner)

    # Verify basic properties
    assert unit.unit_type == unit_type
    assert unit.owner == owner

    # Verify stats are integers (or None for range)
    assert isinstance(unit.attack, int)
    assert isinstance(unit.defense, int)
    assert isinstance(unit.movement, int)
    assert unit.range is None or isinstance(unit.range, int)

    # Verify combat vs structure classification
    if unit.attack > 0:
        assert unit.is_combat_unit() is True
    else:
        assert unit.is_combat_unit() is False

    if unit.movement == 0:
        assert unit.is_structure() is True
    else:
        assert unit.is_structure() is False


@given(st.integers(0, 19), st.integers(0, 24))
def test_clear_and_place_invariant(row, col):
    """Test that clearing and placing units maintains invariants."""
    board = Board()

    # Initially empty
    assert board.get_unit(row, col) is None

    # Place unit
    board.create_and_place_unit(row, col, "INFANTRY", "NORTH")
    assert board.get_unit(row, col) is not None
    assert board.get_unit_type(row, col) == "INFANTRY"

    # Clear unit
    board.clear_square(row, col)
    assert board.get_unit(row, col) is None
    assert board.get_unit_type(row, col) is None

    # Place again
    board.create_and_place_unit(row, col, "CAVALRY", "SOUTH")
    assert board.get_unit(row, col) is not None
    assert board.get_unit_type(row, col) == "CAVALRY"


@given(st.lists(st.tuples(
    st.integers(0, 19),
    st.integers(0, 24)
), max_size=100))
def test_get_all_units_accuracy(coordinates):
    """Test that get_all_units returns accurate mapping."""
    board = Board()

    # Place units at specified coordinates
    for i, (row, col) in enumerate(coordinates):
        unit_type = ["INFANTRY", "CAVALRY", "CANNON"][i % 3]
        board.create_and_place_unit(row, col, unit_type, "NORTH")

    # Get all units
    all_units = board.get_all_units()

    # Verify each returned unit
    for (row, col), unit in all_units.items():
        retrieved = board.get_unit(row, col)
        assert retrieved == unit
        assert retrieved.unit_type == unit.unit_type
        assert retrieved.owner == unit.owner


@given(st.integers(0, 19), st.integers(0, 24))
def test_overwrite_invariant(row, col):
    """Test that overwriting units maintains correct state."""
    board = Board()

    # Place first unit
    board.create_and_place_unit(row, col, "INFANTRY", "NORTH")
    assert board.count_units(unit_type="INFANTRY") == 1
    assert board.count_units(unit_type="CAVALRY") == 0

    # Overwrite with different unit type
    board.create_and_place_unit(row, col, "CAVALRY", "SOUTH")
    assert board.count_units(unit_type="INFANTRY") == 0
    assert board.count_units(unit_type="CAVALRY") == 1

    # Overwrite with same type, different owner
    board.create_and_place_unit(row, col, "CAVALRY", "NORTH")
    assert board.get_unit_owner(row, col) == "NORTH"
