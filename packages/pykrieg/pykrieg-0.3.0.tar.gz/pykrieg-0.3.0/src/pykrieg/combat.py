"""Combat system for Pykrieg.

This module implements vector-based combat calculation for all unit types.
Combat is calculated by comparing power numbers along straight lines
(horizontal, vertical, diagonal).

Combat resolution:
- Attack ≤ Defense: FAIL (nothing happens)
- Attack = Defense + 1: RETREAT (defender must move next turn)
- Attack ≥ Defense + 2: CAPTURE (defender destroyed)

Scope for 0.1.3:
- Vector-based line detection (8 directions)
- Attack power calculation with cavalry charge bonus
- Defense power calculation
- Capture/retreat resolution logic
- Terrain-independent (terrain modifiers added in 0.2.1)
- Range-independent (range validation added in 0.2.0)
- Lines of communication not considered (added in 0.2.0)
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple

from .board import Board


def get_terrain_defense_bonus(terrain: Optional[str]) -> int:
    """Get defense bonus provided by terrain type.

    Args:
        terrain: Terrain type (None, 'MOUNTAIN', 'MOUNTAIN_PASS', 'FORTRESS')

    Returns:
        Defense bonus amount:
        - None: 0
        - MOUNTAIN: 0 (impassable, no combat there)
        - MOUNTAIN_PASS: +2 (passable with defensive bonus)
        - FORTRESS: +4 (passable with strong defensive bonus)
    """
    if terrain == 'MOUNTAIN_PASS':
        return 2
    elif terrain == 'FORTRESS':
        return 4
    return 0  # No terrain or MOUNTAIN (units can't be on mountains)


class CombatOutcome(Enum):
    """Result of a combat calculation."""
    FAIL = "FAIL"
    RETREAT = "RETREAT"
    CAPTURE = "CAPTURE"


def get_directions() -> List[Tuple[int, int]]:
    """Get all 8 cardinal and diagonal directions.

    Returns:
        List of (row_offset, col_offset) tuples for each direction:
        - (-1, 0): Up
        - (1, 0): Down
        - (0, -1): Left
        - (0, 1): Right
        - (-1, -1): Up-Left
        - (-1, 1): Up-Right
        - (1, -1): Down-Left
        - (1, 1): Down-Right
    """
    return [
        (-1, 0),  # Up
        (1, 0),  # Down
        (0, -1),  # Left
        (0, 1),  # Right
        (-1, -1),  # Up-Left
        (-1, 1),  # Up-Right
        (1, -1),  # Down-Left
        (1, 1),  # Down-Right
    ]


def get_line_units(board: Board, target_row: int, target_col: int,
                direction: Tuple[int, int], owner: str) -> List[Tuple[int, int, object]]:
    """Get all units of a given owner in a specific direction from target.

    This function enumerates all squares in a straight line from the target
    in specified direction, collecting all units owned by the specified player.

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        direction: (row_offset, col_offset) tuple
        owner: 'NORTH' or 'SOUTH' - units to collect

    Returns:
        List of (row, col, unit) tuples for matching units in the line
    """
    row_offset, col_offset = direction
    units = []

    # Start from target square and move in direction
    current_row = target_row + row_offset
    current_col = target_col + col_offset

    while board.is_valid_square(current_row, current_col):
        unit = board.get_unit(current_row, current_col)
        if unit is not None:
            if getattr(unit, 'owner', None) == owner:
                units.append((current_row, current_col, unit))

        # Move to next square in line
        current_row += row_offset
        current_col += col_offset

    return units


def calculate_attack_power(board: Board, target_row: int, target_col: int,
                      attacker: str) -> int:
    """Calculate total attack power against a target square.

    Attack power is sum of effective Attack stats of all attacker's units
    in direct lines with target, plus Cavalry charge bonuses.

    Cavalry Charge Rules:
    - Cavalry adjacent to target gets +3 bonus (triggers charge)
    - Cavalry can join charge stack if on same attack vector as charging cavalry
    - Charge stack requires unbroken line, up to 4 squares from target
    - Stacking cavalry also get +3 bonus even if not adjacent
    - Each attack vector calculated separately
    - If first cavalry not adjacent, no charge in that direction
    - Gaps break charge stacking chain
    - Charging cavalry are exempt from range and path blocking checks

    Range and Path Blocking Rules:
    - Units must be within their attack range to participate
    - Enemy units block the path to the target
    - Charging cavalry are exempt from blocking checks
    - Friendly units do NOT block the path

    Note: Effective attack considers online/offline status (0.2.0)
    - Offline units have 0 attack (except relays, which have 0 anyway)
    - Only online units contribute to attack power

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        attacker: 'NORTH' or 'SOUTH' - player making of attack

    Returns:
        Total attack power (integer)
    """
    total_attack = 0

    # Check target terrain for cavalry charge restrictions (0.2.3)
    # Cavalry charge bonus does NOT apply when attacking units in fortress or mountain pass
    target_terrain = board.get_terrain(target_row, target_col)
    charge_restricted = target_terrain in ('FORTRESS', 'MOUNTAIN_PASS')

    for direction in get_directions():
        units = get_line_units(board, target_row, target_col, direction, attacker)

        # Build full list of squares in this direction for gap checking
        row_offset, col_offset = direction
        squares_in_line = []
        current_row = target_row + row_offset
        current_col = target_col + col_offset
        while board.is_valid_square(current_row, current_col):
            squares_in_line.append((current_row, current_col))
            current_row += row_offset
            current_col += col_offset

        # Step 1: Calculate charge stack FIRST (exclusive calculation)
        # Skip charge stack if terrain restricts cavalry charge
        charge_stack_indices = []
        if not charge_restricted:
            # Find first cavalry adjacent to target
            if units:
                first_unit_row, first_unit_col, first_unit = units[0]
                first_unit_type = getattr(first_unit, 'unit_type', None)

                if (first_unit_type == 'CAVALRY' and
                    is_adjacent(first_unit_row, first_unit_col, target_row, target_col)):
                    # First unit is adjacent cavalry - start charge stack
                    charge_stack_indices.append(0)

                    # Look for consecutive cavalry (up to 4 total)
                    max_charge_stack = 4
                    for i in range(1, min(len(units), max_charge_stack)):
                        prev_row, prev_col, prev_unit = units[i - 1]
                        curr_row, curr_col, curr_unit = units[i]

                        # Check if units are consecutive (no gap)
                        prev_index = squares_in_line.index((prev_row, prev_col))
                        curr_index = squares_in_line.index((curr_row, curr_col))

                        if curr_index - prev_index > 1:
                            # Gap found - charge stack ends
                            break

                        # Check for enemy blocker
                        if is_path_blocked_by_enemy(
                            board, curr_row, curr_col, target_row, target_col, attacker
                        ):
                            # Enemy blocker found - charge stack ends
                            break

                        curr_unit_type = getattr(curr_unit, 'unit_type', None)
                        if curr_unit_type == 'CAVALRY':
                            charge_stack_indices.append(i)
                        else:
                            # Non-cavalry unit - charge stack ends
                            break

        # Step 2: Process charge stack (exempt from range and path blocking)
        # Only if charge is not restricted by terrain
        if not charge_restricted:
            for idx in charge_stack_indices:
                row, col, unit = units[idx]

                # Use effective attack (0.2.0) to account for online/offline status
                if hasattr(unit, 'get_effective_attack'):
                    base_attack = unit.get_effective_attack(board)
                else:
                    base_attack = getattr(unit, 'attack', 0)

                # Charge stack cavalry get +3 bonus
                total_attack += base_attack + 3

        # Step 3: Process remaining units with normal rules (after charge stack)
        # Start index depends on whether charge was processed
        start_normal_index = len(charge_stack_indices) if not charge_restricted else 0
        for i in range(start_normal_index, len(units)):
            row, col, unit = units[i]

            # Use effective attack (0.2.0) to account for online/offline status
            if hasattr(unit, 'get_effective_attack'):
                base_attack = unit.get_effective_attack(board)
            else:
                base_attack = getattr(unit, 'attack', 0)

            getattr(unit, 'unit_type', None)

            # Check range
            if not is_unit_in_range(board, row, col, target_row, target_col):
                continue  # Out of range

            # Check path blocking
            if is_path_blocked_by_enemy(board, row, col, target_row, target_col, attacker):
                continue  # Path blocked

            # Add attack power
            total_attack += base_attack

    return total_attack


def calculate_defense_power(board: Board, target_row: int, target_col: int,
                        defender: str) -> int:
    """Calculate total defense power for a target square.

    Defense power is sum of effective Defense stats of all defender's units
    in direct lines supporting the target, including the unit at the target itself,
    plus any terrain defense bonus.

    Range and Path Blocking Rules:
    - The unit at the target square always participates (being attacked)
    - Supporting units must be within their range to participate
    - Enemy units block the path to the target for supporting units
    - Friendly units do NOT block the path

    Terrain Bonus (0.2.1):
    - Mountain pass: +2 defense bonus
    - Fortress: +4 defense bonus
    - Terrain bonus applies to the target square only
    - Terrain bonus applies even if no unit is present

    Note: Effective defense considers online/offline status (0.2.0)
    - Offline units have 0 defense (except relays, which always have defense)
    - Only online units contribute to defense power

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        defender: 'NORTH' or 'SOUTH' - player being attacked

    Returns:
        Total defense power (integer)
    """
    total_defense = 0

    # Add terrain defense bonus for target square (0.2.1)
    target_terrain = board.get_terrain(target_row, target_col)
    terrain_bonus = get_terrain_defense_bonus(target_terrain)
    total_defense += terrain_bonus

    # First, check if there's a unit at target square that belongs to defender
    # The target unit always participates regardless of range or blocking
    target_unit = board.get_unit(target_row, target_col)
    target_unit_processed = False
    if target_unit is not None and getattr(target_unit, 'owner', None) == defender:
        # Use effective defense (0.2.0) to account for online/offline status
        if hasattr(target_unit, 'get_effective_defense'):
            total_defense += target_unit.get_effective_defense(board)
        else:
            total_defense += getattr(target_unit, 'defense', 0)
        target_unit_processed = True

    # Then add defense from units in all 8 directions supporting the target
    # Supporting units must be in range and have clear path
    for direction in get_directions():
        units = get_line_units(board, target_row, target_col, direction, defender)

        for row, col, unit in units:
            # Skip target unit (already counted above)
            if target_unit_processed and (row, col) == (target_row, target_col):
                continue

            # Check range for supporting units
            if not is_unit_in_range(board, row, col, target_row, target_col):
                continue  # Out of range

            # Check path blocking for supporting units
            if is_path_blocked_by_enemy(board, row, col, target_row, target_col, defender):
                continue  # Path blocked by enemy

            # Use effective defense (0.2.0) to account for online/offline status
            if hasattr(unit, 'get_effective_defense'):
                total_defense += unit.get_effective_defense(board)
            else:
                total_defense += getattr(unit, 'defense', 0)

    return total_defense


def get_distance(row1: int, col1: int, row2: int, col2: int) -> int:
    """Calculate Chebyshev distance between two squares.

    Chebyshev distance is the maximum of the absolute differences
    of row and column coordinates. This is appropriate for
    8-directional movement (including diagonals).

    Args:
        row1: First square row
        col1: First square column
        row2: Second square row
        col2: Second square column

    Returns:
        Distance in squares
    """
    return max(abs(row1 - row2), abs(col1 - col2))


def is_adjacent(row1: int, col1: int, row2: int, col2: int) -> bool:
    """Check if two squares are adjacent (Chebyshev distance = 1).

    Adjacent means sharing a side or corner (8-directional adjacency).

    Args:
        row1: First square row
        col1: First square column
        row2: Second square row
        col2: Second square column

    Returns:
        True if adjacent, False otherwise
    """
    distance = get_distance(row1, col1, row2, col2)
    return distance == 1


def is_unit_in_range(board: Board, unit_row: int, unit_col: int,
                    target_row: int, target_col: int) -> bool:
    """Check if a unit is within range of a target square.

    Args:
        board: The game board
        unit_row: Unit row (0-19)
        unit_col: Unit column (0-24)
        target_row: Target row (0-19)
        target_col: Target column (0-24)

    Returns:
        True if unit is within range, False otherwise
    """
    unit = board.get_unit(unit_row, unit_col)
    if unit is None:
        return False

    # Get unit range
    unit_range: Optional[int] = None
    if hasattr(unit, 'get_effective_range'):
        unit_range = unit.get_effective_range(board)
    else:
        unit_range = getattr(unit, 'range', None)

    # Structures with range=None cannot participate in attacks
    if unit_range is None:
        return False

    # Check if within range (including 0 range units)
    distance = get_distance(unit_row, unit_col, target_row, target_col)
    return distance <= unit_range


def is_path_blocked_by_enemy(board: Board, unit_row: int, unit_col: int,
                            target_row: int, target_col: int, owner: str) -> bool:
    """Check if the path from unit to target is blocked by an enemy unit.

    This checks all squares along the direct line between unit and target
    (excluding the start and end squares) for enemy units.

    Args:
        board: The game board
        unit_row: Unit row (0-19)
        unit_col: Unit column (0-24)
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        owner: 'NORTH' or 'SOUTH' - owner of the unit checking path

    Returns:
        True if path is blocked by an enemy unit, False otherwise
    """
    # Calculate direction from unit to target
    row_diff = target_row - unit_row
    col_diff = target_col - unit_col

    # If same position, not blocked
    if row_diff == 0 and col_diff == 0:
        return False

    # Normalize direction to -1, 0, or 1
    if row_diff != 0:
        row_step = 1 if row_diff > 0 else -1
    else:
        row_step = 0

    if col_diff != 0:
        col_step = 1 if col_diff > 0 else -1
    else:
        col_step = 0

    # Walk from unit towards target, stopping before reaching target
    current_row = unit_row + row_step
    current_col = unit_col + col_step

    while (current_row != target_row or current_col != target_col):
        if not board.is_valid_square(current_row, current_col):
            # Should not happen if units are on valid squares
            break

        unit_in_path = board.get_unit(current_row, current_col)
        if unit_in_path is not None:
            unit_owner = getattr(unit_in_path, 'owner', None)
            # Check if this is an enemy unit
            if unit_owner is not None and unit_owner != owner:
                return True  # Path blocked by enemy

        current_row += row_step
        current_col += col_step

    return False  # Path clear


def get_eligible_line_units(board: Board, target_row: int, target_col: int,
                           direction: Tuple[int, int], owner: str,
                           is_attack: bool = False,
                           charging_cavalry_exempt: bool = False) -> List[Tuple[int, int, object]]:
    """Get eligible units of a given owner in a specific direction from target.

    This function filters units based on range and path blocking rules.

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        direction: (row_offset, col_offset) tuple
        owner: 'NORTH' or 'SOUTH' - units to collect
        is_attack: True if checking attacking units, False for defending units
        charging_cavalry_exempt: If True, cavalry in charge stack exempt from blocking/range

    Returns:
        List of (row, col, unit) tuples for eligible units in the line
    """
    # Get all units in the line
    all_units = get_line_units(board, target_row, target_col, direction, owner)

    eligible_units = []

    for row, col, unit in all_units:
        unit_type = getattr(unit, 'unit_type', None)

        # Check if this is a cavalry in charge stack (exempt from checks)
        is_charging_cavalry = False
        if charging_cavalry_exempt and unit_type == 'CAVALRY':
            # Check if adjacent to target (starts charge)
            if is_adjacent(row, col, target_row, target_col):
                is_charging_cavalry = True

        # For attacking cavalry in charge stack, exempt from range and blocking checks
        if is_attack and is_charging_cavalry:
            eligible_units.append((row, col, unit))
            continue

        # Check range
        if not is_unit_in_range(board, row, col, target_row, target_col):
            # Out of range, skip
            continue

        # Check path blocking
        if is_path_blocked_by_enemy(board, row, col, target_row, target_col, owner):
            # Path blocked by enemy, skip
            continue

        # Unit is eligible
        eligible_units.append((row, col, unit))

    return eligible_units


def resolve_combat(attack_power: int, defense_power: int) -> CombatOutcome:
    """Resolve combat based on attack vs defense power.

    Combat outcomes:
    - Attack ≤ Defense: FAIL (nothing happens)
    - Attack = Defense + 1: RETREAT (defender must move next turn)
    - Attack ≥ Defense + 2: CAPTURE (defender destroyed)

    Args:
        attack_power: Total attack power
        defense_power: Total defense power

    Returns:
        CombatOutcome enum (FAIL, RETREAT, or CAPTURE)
    """
    if attack_power <= defense_power:
        return CombatOutcome.FAIL
    elif attack_power == defense_power + 1:
        return CombatOutcome.RETREAT
    else:  # attack_power >= defense_power + 2
        return CombatOutcome.CAPTURE


def calculate_combat(board: Board, target_row: int, target_col: int,
                 attacker: str, defender: str) -> Dict[str, object]:
    """Calculate complete combat scenario.

    This function performs full combat calculation:
    1. Calculate attack power
    2. Calculate defense power
    3. Resolve combat outcome

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        attacker: 'NORTH' or 'SOUTH' - player making of attack
        defender: 'NORTH' or 'SOUTH' - player being attacked

    Returns:
        Dictionary with combat results:
        {
            'attack_power': int,
            'defense_power': int,
            'outcome': CombatOutcome,
            'attack_units': List[Tuple[int, int, object]],
            'defense_units': List[Tuple[int, int, object]],
        }
    """
    # Calculate powers
    attack_power = calculate_attack_power(board, target_row, target_col, attacker)
    defense_power = calculate_defense_power(board, target_row, target_col, defender)

    # Resolve combat
    outcome = resolve_combat(attack_power, defense_power)

    # Collect unit information for debugging/analysis
    attack_units = []
    defense_units = []

    for direction in get_directions():
        attack_units.extend(get_line_units(board, target_row, target_col, direction, attacker))
        defense_units.extend(get_line_units(board, target_row, target_col, direction, defender))

    return {
        'attack_power': attack_power,
        'defense_power': defense_power,
        'outcome': outcome,
        'attack_units': attack_units,
        'defense_units': defense_units,
    }


def preview_combat(board: Board, target_row: int, target_col: int,
                  attacker: str, defender: str) -> Dict[str, object]:
    """Preview a combat scenario with detailed unit information.

    This function calculates battle details without executing the attack,
    providing information for confirmation dialogs and battle planning.

    Returns detailed information including:
    - Attack and defense power
    - Combat outcome
    - List of participating units with their contributions
    - Count of charging cavalry
    - List of blocked units with reasons

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        attacker: 'NORTH' or 'SOUTH' - player making of attack
        defender: 'NORTH' or 'SOUTH' - player being attacked

    Returns:
        Dictionary with detailed combat results:
        {
            'attack_power': int,
            'defense_power': int,
            'outcome': CombatOutcome,
            'attack_units': List[Tuple[int, int, object, int]],  # (row, col, unit, contribution)
            'defense_units': List[Tuple[int, int, object, int]],  # (row, col, unit, contribution)
            'charging_cavalry_count': int,
            'blocked_attack_units': List[Tuple[int, int, object, str]],  # (row, col, unit, reason)
            'blocked_defense_units': List[Tuple[int, int, object, str]],  # (row, col, unit, reason)
        }
    """
    # Calculate powers
    attack_power = calculate_attack_power(board, target_row, target_col, attacker)
    defense_power = calculate_defense_power(board, target_row, target_col, defender)

    # Resolve combat
    outcome = resolve_combat(attack_power, defense_power)

    # Collect detailed unit information
    attack_units = []
    defense_units = []
    blocked_attack_units = []
    blocked_defense_units = []
    charging_cavalry_count = 0

    # Check target terrain for cavalry charge restrictions (0.2.3)
    # Cavalry charge bonus does NOT apply when attacking units in fortress or mountain pass
    target_terrain = board.get_terrain(target_row, target_col)
    charge_restricted = target_terrain in ('FORTRESS', 'MOUNTAIN_PASS')

    # Process attack units
    for direction in get_directions():
        units = get_line_units(board, target_row, target_col, direction, attacker)

        # Track charging state for this direction
        charging = False

        # Build squares list for gap checking
        row_offset, col_offset = direction
        squares_in_line = []
        current_row = target_row + row_offset
        current_col = target_col + col_offset
        while board.is_valid_square(current_row, current_col):
            squares_in_line.append((current_row, current_col))
            current_row += row_offset
            current_col += col_offset

        for i, (row, col, unit) in enumerate(units):
            unit_type = getattr(unit, 'unit_type', None)

            # Check if unit is eligible to participate
            is_eligible = True
            contribution = 0

            # Calculate contribution
            if hasattr(unit, 'get_effective_attack'):
                base_attack = unit.get_effective_attack(board)
            else:
                base_attack = getattr(unit, 'attack', 0)

            # Check for cavalry charge
            # Charge is restricted by terrain (0.2.3)
            if unit_type == 'CAVALRY' and not charge_restricted:
                if i == 0:
                    if is_adjacent(row, col, target_row, target_col):
                        charging = True
                        contribution = base_attack + 3
                        charging_cavalry_count += 1
                    else:
                        # First cavalry not adjacent, check eligibility normally
                        if not is_unit_in_range(board, row, col, target_row, target_col):
                            is_eligible = False
                            blocked_attack_units.append((row, col, unit, "Out of range"))
                        elif is_path_blocked_by_enemy(
                            board, row, col, target_row, target_col, attacker
                        ):
                            is_eligible = False
                            blocked_attack_units.append((row, col, unit, "Path blocked"))
                        else:
                            contribution = base_attack
                elif not charging:
                    # Check eligibility normally
                    if not is_unit_in_range(board, row, col, target_row, target_col):
                        is_eligible = False
                        blocked_attack_units.append((row, col, unit, "Out of range"))
                    elif is_path_blocked_by_enemy(
                        board, row, col, target_row, target_col, attacker
                    ):
                        is_eligible = False
                        blocked_attack_units.append((row, col, unit, "Path blocked"))
                    else:
                        contribution = base_attack
                else:
                    # Check for gap
                    prev_unit = units[i - 1]
                    prev_row, prev_col = prev_unit[0], prev_unit[1]
                    prev_index = squares_in_line.index((prev_row, prev_col))
                    current_index = squares_in_line.index((row, col))

                    if current_index - prev_index > 1:
                        # Gap breaks charge
                        charging = False
                        if not is_unit_in_range(board, row, col, target_row, target_col):
                            is_eligible = False
                            blocked_attack_units.append((row, col, unit, "Out of range"))
                        elif is_path_blocked_by_enemy(
                            board, row, col, target_row, target_col, attacker
                        ):
                            is_eligible = False
                            blocked_attack_units.append((row, col, unit, "Path blocked"))
                        else:
                            contribution = base_attack
                    else:
                        # Continue charge stack
                        contribution = base_attack + 3
                        charging_cavalry_count += 1
            else:
                # Non-cavalry units
                if not is_unit_in_range(board, row, col, target_row, target_col):
                    is_eligible = False
                    blocked_attack_units.append((row, col, unit, "Out of range"))
                elif is_path_blocked_by_enemy(board, row, col, target_row, target_col, attacker):
                    is_eligible = False
                    blocked_attack_units.append((row, col, unit, "Path blocked"))
                else:
                    contribution = base_attack

            if is_eligible:
                attack_units.append((row, col, unit, contribution))

    # Process defense units
    # First, check target unit (always participates)
    target_unit = board.get_unit(target_row, target_col)
    target_unit_processed = False
    if target_unit is not None and getattr(target_unit, 'owner', None) == defender:
        if hasattr(target_unit, 'get_effective_defense'):
            defense_units.append((target_row, target_col, target_unit,
                               target_unit.get_effective_defense(board)))
        else:
            defense_units.append((target_row, target_col, target_unit,
                               getattr(target_unit, 'defense', 0)))
        target_unit_processed = True

    # Then process supporting units
    for direction in get_directions():
        units = get_line_units(board, target_row, target_col, direction, defender)

        for row, col, unit in units:
            # Skip target unit (already counted above)
            if target_unit_processed and (row, col) == (target_row, target_col):
                continue

            # Check range and path blocking
            if not is_unit_in_range(board, row, col, target_row, target_col):
                blocked_defense_units.append((row, col, unit, "Out of range"))
                continue

            if is_path_blocked_by_enemy(board, row, col, target_row, target_col, defender):
                blocked_defense_units.append((row, col, unit, "Path blocked"))
                continue

            # Unit is eligible
            if hasattr(unit, 'get_effective_defense'):
                defense_units.append((row, col, unit, unit.get_effective_defense(board)))
            else:
                defense_units.append((row, col, unit, getattr(unit, 'defense', 0)))

    # Collect charging cavalry positions for display highlighting
    charging_cavalry_positions = []
    for row, col, unit, contribution in attack_units:
        unit_type = getattr(unit, 'unit_type', None)
        if unit_type == 'CAVALRY':
            # Check if this cavalry is charging (has +3 bonus)
            base_attack = (
                unit.get_effective_attack(board)
                if hasattr(unit, 'get_effective_attack')
                else getattr(unit, 'attack', 0)
            )
            if contribution > base_attack:  # Has +3 bonus
                charging_cavalry_positions.append((row, col))

    # Collect defending cavalry positions for display highlighting
    defending_cavalry_positions = []
    for row, col, unit, _contribution in defense_units:
        unit_type = getattr(unit, 'unit_type', None)
        if unit_type == 'CAVALRY':
            defending_cavalry_positions.append((row, col))

    # Get terrain information (0.2.1)
    target_terrain = board.get_terrain(target_row, target_col)
    terrain_bonus = get_terrain_defense_bonus(target_terrain)

    return {
        'attack_power': attack_power,
        'defense_power': defense_power,
        'outcome': outcome,
        'attack_units': attack_units,
        'defense_units': defense_units,
        'charging_cavalry_count': charging_cavalry_count,
        'charging_cavalry_positions': charging_cavalry_positions,
        'defending_cavalry_positions': defending_cavalry_positions,
        'blocked_attack_units': blocked_attack_units,
        'blocked_defense_units': blocked_defense_units,
        'target_terrain': target_terrain,  # Added in 0.2.1
        'terrain_bonus': terrain_bonus,  # Added in 0.2.1
    }


def execute_capture(board: Board, target_row: int, target_col: int) -> object:
    """Execute a capture (remove target unit from board).

    This function removes the unit at target square.
    After capture, networks are recalculated for both players (0.2.0).

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)

    Returns:
        The captured Unit object

    Raises:
        ValueError: If no unit at target position

    Note:
        Retreat execution is handled in turn management (0.1.4).
    """
    unit = board.get_unit(target_row, target_col)
    if unit is None:
        raise ValueError(f"No unit to capture at ({target_row}, {target_col})")

    board.clear_square(target_row, target_col)

    # Network recalculation is now lazy - marked dirty by clear_square()
    # Will be recalculated automatically when needed via _ensure_network_calculated()
    # This ensures backward compatibility for scenarios that don't use network system

    return unit


def can_attack(board: Board, target_row: int, target_col: int,
              attacker: str) -> bool:
    """Check if an attacker can attack the target square.

    In 0.1.3, this checks if there's at least one attacking unit.
    Range validation will be added in 0.2.0.

    Args:
        board: The game board
        target_row: Target row (0-19)
        target_col: Target column (0-24)
        attacker: 'NORTH' or 'SOUTH' - player making of attack

    Returns:
        True if attacker has units in line with target, False otherwise

    Note:
        Range validation NOT checked in 0.1.3 (added in 0.2.0).
    """
    for direction in get_directions():
        units = get_line_units(board, target_row, target_col, direction, attacker)
        if units:
            return True
    return False
