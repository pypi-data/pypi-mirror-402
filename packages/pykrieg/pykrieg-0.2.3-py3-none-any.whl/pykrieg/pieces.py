"""Unit type system for Pykrieg.

This module implements complete unit type system with 6 unit types
(Infantry, Cavalry, Cannon, Relay, Swift Cannon, Swift Relay),
each with their specific combat statistics from official rules.

Note: Arsenals are terrain structures (not units) as of version 0.2.1.
See Board.set_arsenal() for arsenal placement.

Unit Statistics:
- Infantry: Atk 4 / Def 6 / Move 1 / Range 2
- Cavalry: Atk 4 / Def 5 / Move 2 / Range 2
- Cannon: Atk 5 / Def 8 / Move 1 / Range 3
- Relay: Atk 0 / Def 1 / Move 1 / Range 0
- Swift Cannon: Atk 5 / Def 8 / Move 2 / Range 3
- Swift Relay: Atk 0 / Def 1 / Move 2 / Range 0
"""

from typing import TYPE_CHECKING, Optional

from . import constants

if TYPE_CHECKING:
    from .board import Board


class Unit:
    """Base class for all unit types.

    This class provides the foundation for all unit types in the game.
    Each unit type has specific combat statistics (attack, defense,
    movement, range) and belongs to a player (NORTH or SOUTH).
    """

    def __init__(self, owner: str):
        """Initialize a unit with an owner.

        Args:
            owner: The player who owns this unit ('NORTH' or 'SOUTH')
        """
        self._owner = owner

    @property
    def owner(self) -> str:
        """Return unit owner (NORTH or SOUTH)."""
        return self._owner

    @property
    def unit_type(self) -> str:
        """Return unit type string."""
        raise NotImplementedError

    @property
    def attack(self) -> int:
        """Return attack value."""
        raise NotImplementedError

    @property
    def defense(self) -> int:
        """Return defense value."""
        raise NotImplementedError

    @property
    def movement(self) -> int:
        """Return movement range in squares."""
        raise NotImplementedError

    @property
    def range(self) -> Optional[int]:
        """Return attack range in squares, or None for structures."""
        raise NotImplementedError

    def is_combat_unit(self) -> bool:
        """Check if this is a combat unit (can attack).

        Returns:
            True if the unit has an attack value > 0
        """
        return self.attack > 0

    def is_structure(self) -> bool:
        """Check if this is a structure (cannot move).

        Returns:
            True if the unit has movement = 0
        """
        return self.movement == 0

    def __repr__(self) -> str:
        """Return string representation of the unit."""
        return f"{self.unit_type}({self.owner})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on unit type and owner."""
        if not isinstance(other, Unit):
            return False
        return (self.unit_type == other.unit_type and
                self.owner == other.owner)

    def __hash__(self) -> int:
        """Return hash based on unit type and owner."""
        return hash((self.unit_type, self.owner))

    # =====================================================================
    # 0.2.0: Effective Stats Methods (Lines of Communication)
    # =====================================================================

    def get_effective_attack(self, board: "Board") -> int:
        """Get effective attack value, considering online/offline status.

        Args:
            board: The Board object to check online status

        Returns:
            Effective attack value (0 if offline and not a relay)
        """
        # Import here to avoid circular import
        from .constants import UNIT_RELAY, UNIT_SWIFT_RELAY

        # Relays/swift relays can have non-zero attack even when offline
        # (but actually they have 0 attack always)
        if self.unit_type in (UNIT_RELAY, UNIT_SWIFT_RELAY):
            return self.attack

        # Check if network has been calculated
        # If network was never calculated, assume all units are online (use base stats)
        if hasattr(board, '_network_calculated') and board._network_calculated:
            # Other units need to be online to have attack
            # Check if unit is active in the network
            if hasattr(board, '_is_unit_active'):
                # Find unit's position on board
                for row in range(board.rows):
                    for col in range(board.cols):
                        unit = board.get_unit(row, col)
                        if unit is self:
                            if board._is_unit_active(row, col, self.owner):
                                return self.attack
                            return 0

        # Fallback: return base attack if network not calculated
        return self.attack

    def get_effective_defense(self, board: "Board") -> int:
        """Get effective defense value, considering online/offline status.

        Args:
            board: The Board object to check online status

        Returns:
            Effective defense value (0 if offline and not a relay)
        """
        # Import here to avoid circular import
        from .constants import UNIT_RELAY, UNIT_SWIFT_RELAY

        # Relays/swift relays always have their defense value
        if self.unit_type in (UNIT_RELAY, UNIT_SWIFT_RELAY):
            return self.defense

        # Check if network has been calculated
        # If network was never calculated, assume all units are online (use base stats)
        if hasattr(board, '_network_calculated') and board._network_calculated:
            # Other units need to be online to have defense
            # Check if unit is active in the network
            if hasattr(board, '_is_unit_active'):
                # Find unit's position on board
                for row in range(board.rows):
                    for col in range(board.cols):
                        unit = board.get_unit(row, col)
                        if unit is self:
                            if board._is_unit_active(row, col, self.owner):
                                return self.defense
                            return 0

        # Fallback: return base defense if network not calculated
        return self.defense

    def get_effective_range(self, board: "Board") -> Optional[int]:
        """Get effective range value, considering online/offline status.

        Args:
            board: The Board object to check online status

        Returns:
            Effective range value (0 if offline and not a relay, None for structures)
        """
        # Import here to avoid circular import
        from .constants import UNIT_RELAY, UNIT_SWIFT_RELAY

        # Relays/swift relays have 0 range always
        if self.unit_type in (UNIT_RELAY, UNIT_SWIFT_RELAY):
            return self.range

        # Check if network has been calculated
        # If network was never calculated, assume all units are online (use base stats)
        if hasattr(board, '_network_calculated') and board._network_calculated:
            # Other units need to be online to have range
            # Check if unit is active in the network
            if hasattr(board, '_is_unit_active'):
                # Find unit's position on board
                for row in range(board.rows):
                    for col in range(board.cols):
                        unit = board.get_unit(row, col)
                        if unit is self:
                            if board._is_unit_active(row, col, self.owner):
                                return self.range
                            return 0

        # Fallback: return base range if network not calculated
        return self.range

    def get_effective_movement(self, board: "Board") -> int:
        """Get effective movement value, considering online/offline status.

        Args:
            board: The Board object to check online status

        Returns:
            Effective movement value (0 if offline and not a relay)
        """
        # Import here to avoid circular import
        from .constants import UNIT_RELAY, UNIT_SWIFT_RELAY

        # Relays/swift relays can move even when offline
        if self.unit_type in (UNIT_RELAY, UNIT_SWIFT_RELAY):
            return self.movement

        # Check if network has been calculated
        # If network was never calculated, assume all units are online (use base stats)
        if hasattr(board, '_network_calculated') and board._network_calculated:
            # Other units need to be online to move
            # Check if unit is active in the network
            if hasattr(board, '_is_unit_active'):
                # Find unit's position on board
                for row in range(board.rows):
                    for col in range(board.cols):
                        unit = board.get_unit(row, col)
                        if unit is self:
                            if board._is_unit_active(row, col, self.owner):
                                return self.movement
                            return 0

        # Fallback: return base movement if network not calculated
        return self.movement


class Infantry(Unit):
    """Infantry unit: attack=4, defense=6, movement=1, range=2"""
    unit_type = constants.UNIT_INFANTRY
    attack = 4
    defense = 6
    movement = 1
    range = 2


class Cavalry(Unit):
    """Cavalry unit: attack=4, defense=5, movement=2, range=2"""
    unit_type = constants.UNIT_CAVALRY
    attack = 4
    defense = 5
    movement = 2
    range = 2


class Cannon(Unit):
    """Cannon unit: attack=5, defense=8, movement=1, range=3"""
    unit_type = constants.UNIT_CANNON
    attack = 5
    defense = 8
    movement = 1
    range = 3


class Relay(Unit):
    """Relay unit: attack=0, defense=1, movement=1, range=0"""
    unit_type = constants.UNIT_RELAY
    attack = 0
    defense = 1
    movement = 1
    range = 0


class SwiftCannon(Unit):
    """Swift Cannon unit: attack=5, defense=8, movement=2, range=3"""
    unit_type = constants.UNIT_SWIFT_CANNON
    attack = 5
    defense = 8
    movement = 2
    range = 3


class SwiftRelay(Unit):
    """Swift Relay unit: attack=0, defense=1, movement=2, range=0"""
    unit_type = constants.UNIT_SWIFT_RELAY
    attack = 0
    defense = 1
    movement = 2
    range = 0


def create_piece(unit_type: str, owner: str) -> Unit:
    """Factory function to create unit instances from type strings.

    This is the recommended way to create units, as it validates
    unit_type and owner parameters.

    Args:
        unit_type: String representing unit type
        owner: 'NORTH' or 'SOUTH'

    Returns:
        Unit subclass instance

    Raises:
        ValueError: If unit_type or owner is invalid

    Note:
        Arsenal is no longer a unit type. Arsenals are now terrain structures.
        Use Board.set_arsenal() to place an arsenal.

    Examples:
        >>> unit = create_piece("INFANTRY", "NORTH")
        >>> unit.unit_type
        'INFANTRY'
        >>> unit.owner
        'NORTH'
    """
    unit_classes = {
        constants.UNIT_INFANTRY: Infantry,
        constants.UNIT_CAVALRY: Cavalry,
        constants.UNIT_CANNON: Cannon,
        constants.UNIT_RELAY: Relay,
        constants.UNIT_SWIFT_CANNON: SwiftCannon,
        constants.UNIT_SWIFT_RELAY: SwiftRelay,
    }

    if owner not in (constants.PLAYER_NORTH, constants.PLAYER_SOUTH):
        raise ValueError(f"Invalid owner: {owner}")

    if unit_type not in unit_classes:
        raise ValueError(f"Invalid unit type: {unit_type}")

    return unit_classes[unit_type](owner)
