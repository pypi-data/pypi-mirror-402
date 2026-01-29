"""
Pykrieg - A Pythonic wargame engine for Guy Debord's Le Jeu de la Guerre.

This package is currently in early development. Check back soon for updates!
"""

__version__ = "0.3.0"
__author__ = "ssjmarx"
__license__ = "GPL-3.0"

from . import board, combat, constants, fen, kfen, movement, types, victory
from .board import Board
from .combat import (
    CombatOutcome,
    calculate_attack_power,
    calculate_combat,
    calculate_defense_power,
    can_attack,
    execute_capture,
    get_directions,
    get_line_units,
    is_adjacent,
    resolve_combat,
)
from .fen import Fen

# KFEN exports
from .kfen import (
    KFENAttack,
    KFENBoardInfo,
    KFENDocument,
    KFENGameState,
    KFENMetadata,
    KFENMove,
    KFENPhaseChange,
    KFENTurn,
    KFENTurnEnd,
    KFENUndoRedo,
    convert_fen_to_kfen,
    export_kfen_to_fen,
    read_kfen,
    reconstruct_board_from_history,
    validate_history,
    write_kfen,
)
from .movement import (
    can_move,
    execute_move,
    generate_moves,
    get_movement_range,
    is_valid_move,
)
from .pieces import (
    Cannon,
    Cavalry,
    Infantry,
    Relay,
    SwiftCannon,
    SwiftRelay,
    Unit,
    create_piece,
)
from .turn import (
    TurnState,
    TurnValidationError,
    can_end_turn,
    get_turn_state,
    get_turn_summary,
    validate_turn_action,
)
from .victory import (
    GameState,
    VictoryCondition,
    VictoryResult,
    check_network_collapse,
    check_total_annihilation,
    check_victory_conditions,
)

__all__ = [
    'board',
    'combat',
    'constants',
    'fen',
    'kfen',
    'types',
    'movement',
    'turn',
    'victory',
    'Board',
    'Fen',
    'Unit',
    'Infantry',
    'Cavalry',
    'Cannon',
    'Relay',
    'SwiftCannon',
    'SwiftRelay',
    'create_piece',
    'generate_moves',
    'is_valid_move',
    'execute_move',
    'get_movement_range',
    'can_move',
    'CombatOutcome',
    'calculate_attack_power',
    'calculate_defense_power',
    'calculate_combat',
    'resolve_combat',
    'execute_capture',
    'can_attack',
    'get_directions',
    'get_line_units',
    'is_adjacent',
    'TurnState',
    'TurnValidationError',
    'get_turn_state',
    'validate_turn_action',
    'can_end_turn',
    'get_turn_summary',
    'GameState',
    'VictoryCondition',
    'VictoryResult',
    'check_total_annihilation',
    'check_network_collapse',
    'check_victory_conditions',
    # KFEN exports
    'KFENMetadata',
    'KFENBoardInfo',
    'KFENGameState',
    'KFENMove',
    'KFENPhaseChange',
    'KFENAttack',
    'KFENTurnEnd',
    'KFENTurn',
    'KFENUndoRedo',
    'KFENDocument',
    'write_kfen',
    'read_kfen',
    'validate_history',
    'reconstruct_board_from_history',
    'convert_fen_to_kfen',
    'export_kfen_to_fen',
]
