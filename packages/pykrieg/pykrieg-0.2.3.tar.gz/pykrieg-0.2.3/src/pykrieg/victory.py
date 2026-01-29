"""Victory condition detection for Pykrieg.

This module provides the victory condition system that determines when
a player has won the game according to the three defined victory conditions:
Total Annihilation, Network Collapse, and Surrender.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .board import Board


class GameState(Enum):
    """Game state representing win/lose/draw conditions."""
    ONGOING = "ONGOING"
    NORTH_WINS = "NORTH_WINS"
    SOUTH_WINS = "SOUTH_WINS"
    DRAW = "DRAW"


class VictoryCondition(Enum):
    """Specific victory condition that was triggered."""
    TOTAL_ANNIHILATION = "TOTAL_ANNIHILATION"
    NETWORK_COLLAPSE = "NETWORK_COLLAPSE"
    SURRENDER = "SURRENDER"


@dataclass
class VictoryResult:
    """Result of victory condition check.

    Attributes:
        game_state: The current state of the game
        winner: The winning player ('NORTH', 'SOUTH', or None for draw)
        victory_condition: The specific victory condition that was met
        details: Human-readable explanation of the result
    """
    game_state: GameState
    winner: Optional[str]
    victory_condition: Optional[VictoryCondition]
    details: str


def check_total_annihilation(board: Board, player: str) -> bool:
    """Check if player has been totally annihilated (no units remaining).

    Args:
        board: The game board
        player: 'NORTH' or 'SOUTH'

    Returns:
        True if player has no units (any type), False otherwise
    """
    total_units = len(board.get_units_by_owner(player))
    return total_units == 0


def check_network_collapse(board: Board, player: str) -> bool:
    """Check if player's network has collapsed.

    Network collapse occurs when:
    - Player has units
    - AND network system is enabled (was ever calculated)
    - AND None of player's units are online
    - OR All arsenals are destroyed

    Args:
        board: The game board
        player: 'NORTH' or 'SOUTH'

    Returns:
        True if network collapse condition met, False otherwise
    """
    # Check if network system is enabled
    # If never enabled, can't have network collapse
    if not board._network_calculated:
        return False

    # If player has no units, this is total annihilation, not network collapse
    total_units = len(board.get_units_by_owner(player))
    if total_units == 0:
        return False

    # Check arsenals destroyed
    arsenals = board._get_arsenals(player)
    if len(arsenals) == 0:
        return True

    # Check if any units are online
    online_units = board.get_online_units(player)

    # Network collapse if has units but none are online
    return len(online_units) == 0


def check_victory_conditions(board: Board) -> VictoryResult:
    """Check all victory conditions and return game state.

    This function checks all three victory conditions for both players.
    Multiple conditions can trigger simultaneously (edge case).

    Priority order for simultaneous conditions:
    1. Total Annihilation (most direct)
    2. Network Collapse

    Note: Surrender is handled separately by player action.

    Args:
        board: The game board

    Returns:
        VictoryResult with game state and details
    """
    # Check North's defeat conditions
    north_annihilated = check_total_annihilation(board, 'NORTH')
    north_network_collapse = check_network_collapse(board, 'NORTH')

    # Check South's defeat conditions
    south_annihilated = check_total_annihilation(board, 'SOUTH')
    south_network_collapse = check_network_collapse(board, 'SOUTH')

    # Determine winner
    north_defeated = north_annihilated or north_network_collapse
    south_defeated = south_annihilated or south_network_collapse

    if not north_defeated and not south_defeated:
        return VictoryResult(
            game_state=GameState.ONGOING,
            winner=None,
            victory_condition=None,
            details="Game is ongoing"
        )

    if north_defeated and not south_defeated:
        # Determine which condition defeated North
        if north_annihilated:
            condition = VictoryCondition.TOTAL_ANNIHILATION
            details = "South wins: North's forces have been totally annihilated"
        else:  # north_network_collapse
            condition = VictoryCondition.NETWORK_COLLAPSE
            details = (
                "South wins: North's network has collapsed "
                "(all units offline or arsenals destroyed)"
            )

        return VictoryResult(
            game_state=GameState.SOUTH_WINS,
            winner='SOUTH',
            victory_condition=condition,
            details=details
        )

    if south_defeated and not north_defeated:
        # Determine which condition defeated South
        if south_annihilated:
            condition = VictoryCondition.TOTAL_ANNIHILATION
            details = "North wins: South's forces have been totally annihilated"
        else:  # south_network_collapse
            condition = VictoryCondition.NETWORK_COLLAPSE
            details = (
                "North wins: South's network has collapsed "
                "(all units offline or arsenals destroyed)"
            )

        return VictoryResult(
            game_state=GameState.NORTH_WINS,
            winner='NORTH',
            victory_condition=condition,
            details=details
        )

    # Both defeated - draw (extremely rare edge case)
    return VictoryResult(
        game_state=GameState.DRAW,
        winner=None,
        victory_condition=None,
        details="Draw: Both players have lost (simultaneous victory conditions)"
    )
