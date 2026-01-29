"""
Board class for Pykrieg - representing 20x25 game board.

This module implements Board class with territory divisions,
coordinate validation, piece management, and Lines of Communication (LOC) network system.
"""

import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from . import constants

if TYPE_CHECKING:
    from .undo_redo import UndoRedoManager


class Board:
    """
    Represents 20x25 game board with territory divisions.

    The board has:
    - 20 rows (0-19)
    - 25 columns (0-24)
    - Total 500 squares
    - Territory division at row 10 (North: 0-9, South: 10-19)
    """

    TERRITORY_BOUNDARY = constants.TERRITORY_BOUNDARY  # Row 10 is the boundary

    def __init__(self, enable_adjacency_relay_propagation: bool = True) -> None:
        """Initialize empty board with territory boundaries.

        Args:
            enable_adjacency_relay_propagation: When True (default), relays activated
                by proximity to an online unit propagate their LOC rays. When False,
                relays only propagate via arsenal rays and other relay rays
                (original Debord behavior).
        """
        from .undo_redo import UndoRedoManager

        self._rows = constants.BOARD_ROWS
        self._cols = constants.BOARD_COLS
        self._undo_redo_manager = UndoRedoManager(max_history=100)  # Undo/redo support
        # Use Any to handle both None and Unit objects due to circular imports
        self._board: List[List[Any]] = [[None for _ in range(self._cols)]
                                        for _ in range(self._rows)]
        self._turn = constants.PLAYER_NORTH  # Starting player
        self._turn_number = 1  # Track turn number
        self._current_phase = constants.PHASE_MOVEMENT  # Track current phase
        # Track pending retreats (persisted in FEN)
        self._pending_retreats: List[Tuple[int, int]] = []

        # New for 0.1.5: Retreat enforcement
        self._units_must_retreat: Set[Tuple[int, int]] = set()  # Units forced to retreat this turn

        # New for 0.1.4: Per-turn tracking
        self._moved_units: Set[Tuple[int, int]] = set()  # Positions units moved FROM this turn
        self._moved_unit_ids: Set[int] = set()  # IDs of units that moved this turn
        # Complete moves: [(from_row, from_col, to_row, to_col), ...]
        self._moves_made: List[Tuple[int, int, int, int]] = []
        self._attacks_this_turn: int = 0  # Attacks made this turn
        self._attack_target: Optional[Tuple[int, int]] = None  # Target square attacked this turn

        # New for 0.2.0: Lines of Communication (LOC) network tracking
        self._terrain: List[List[Optional[str]]] = [[None for _ in range(self._cols)]
                                                     for _ in range(self._rows)]
        self._active_north: Set[Tuple[int, int]] = set()  # Active units for North
        self._active_south: Set[Tuple[int, int]] = set()  # Active units for South
        # New for 0.2.1: Arsenals are terrain, not units
        self._arsenal_owners: Dict[Tuple[int, int], str] = {}  # Maps (row, col) -> player
        self._relay_online_status: Dict[Tuple[int, int], bool] = {}  # Track relay online status
        self._proximity_checked: Set[
            Tuple[int, int]
        ] = set()  # Track squares proximity-checked this cycle
        self._network_coverage_north: Set[
            Tuple[int, int]
        ] = set()  # All squares covered by North's network (rays + proximity)
        self._network_coverage_south: Set[
            Tuple[int, int]
        ] = set()  # All squares covered by South's network (rays + proximity)
        self._ray_coverage_north: Set[
            Tuple[int, int]
        ] = set()  # Squares covered by North's arsenal/relay rays only (for display)
        self._ray_coverage_south: Set[
            Tuple[int, int]
        ] = set()  # Squares covered by South's arsenal/relay rays only (for display)
        self._network_calculated: bool = False  # Flag if calculate_network() was called
        self._network_dirty: bool = True  # Flag for lazy recalculation - network needs update

        # Configuration for network rules
        self._enable_adjacency_relay_propagation: bool = enable_adjacency_relay_propagation

        # New for 0.2.2: Game state tracking
        self._game_state: str = "ONGOING"  # Track game state
        self._victory_result: Optional[Dict[str, object]] = None  # Store victory details

        # KFEN metadata storage
        self._kfen_metadata: Optional[Dict[str, object]] = None

    @property
    def rows(self) -> int:
        """Return number of rows."""
        return self._rows

    @property
    def cols(self) -> int:
        """Return number of columns."""
        return self._cols

    @property
    def undo_redo_manager(self) -> 'UndoRedoManager':
        """Return the undo/redo manager."""
        return self._undo_redo_manager

    # KFEN metadata methods

    def get_kfen_metadata(self) -> Optional[Dict[str, object]]:
        """Get KFEN metadata for this board.

        Returns:
            Dictionary with KFEN metadata or None if not set

        Note:
            This is used when saving games to include metadata like
            game name, player names, event, etc.
        """
        return self._kfen_metadata

    def set_kfen_metadata(self, metadata: Dict[str, object]) -> None:
        """Set KFEN metadata for this board.

        Args:
            metadata: Dictionary with KFEN metadata fields

        Example:
            >>> board.set_kfen_metadata({
            ...     "game_name": "Tournament Final",
            ...     "players": {"north": "Alice", "south": "Bob"},
            ...     "event": "World Championship 2026"
            ... })
        """
        self._kfen_metadata = metadata

    @property
    def turn(self) -> str:
        """Return current player."""
        return self._turn

    def turn_side(self) -> str:
        """Return current turn side (NORTH/SOUTH)."""
        return self._turn

    @property
    def territory_boundary(self) -> int:
        """Return row number that separates territories."""
        return self.TERRITORY_BOUNDARY

    def is_valid_square(self, row: int, col: int) -> bool:
        """Check if coordinates are within board bounds."""
        return (0 <= row < self._rows) and (0 <= col < self._cols)

    def get_piece(self, row: int, col: int) -> Optional[object]:
        """Get piece at given coordinates.

        .. deprecated:: 0.1.2
            Use :meth:`get_unit` instead. Will be removed in version 0.3.0.
        """
        warnings.warn(
            "get_piece() is deprecated and will be removed in version 0.3.0. "
            "Use get_unit() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        return self._board[row][col]  # type: ignore[no-any-return]

    def set_piece(self, row: int, col: int, piece: object) -> None:
        """Set piece at given coordinates.

        .. deprecated:: 0.1.2
            Use :meth:`place_unit` instead. Will be removed in version 0.3.0.
        """
        warnings.warn(
            "set_piece() is deprecated and will be removed in version 0.3.0. "
            "Use place_unit() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        self._board[row][col] = piece

    def clear_square(self, row: int, col: int) -> None:
        """Remove piece from square."""
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        self._board[row][col] = None
        self._network_dirty = True  # Mark network as needing recalculation

    # Unit placement methods

    def place_unit(self, row: int, col: int, unit: object) -> None:
        """Place a Unit object on the board.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            unit: Unit object to place

        Raises:
            ValueError: If coordinates are invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        self._board[row][col] = unit
        self._network_dirty = True  # Mark network as needing recalculation

    def create_and_place_unit(self, row: int, col: int,
                             unit_type: str, owner: str) -> object:
        """Create and place a unit on board in one step.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            unit_type: Unit type string
            owner: 'NORTH' or 'SOUTH'

        Returns:
            The created Unit object

        Raises:
            ValueError: If coordinates, unit_type, or owner are invalid
        """
        from .pieces import create_piece
        unit = create_piece(unit_type, owner)
        self.place_unit(row, col, unit)
        return unit

    # Unit query methods

    def get_unit(self, row: int, col: int) -> Optional[object]:
        """Get Unit object at given coordinates.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Returns:
            Unit object or None if square is empty

        Raises:
            ValueError: If coordinates are invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        return self._board[row][col]  # type: ignore[no-any-return]

    def get_unit_type(self, row: int, col: int) -> Optional[str]:
        """Get unit type string at given coordinates.

        Returns unit type string or None if square is empty.
        """
        unit = self.get_unit(row, col)
        if unit is None:
            return None
        # Use getattr to avoid circular imports with Unit type
        return getattr(unit, 'unit_type', None)

    def get_unit_owner(self, row: int, col: int) -> Optional[str]:
        """Get unit owner at given coordinates.

        Returns 'NORTH', 'SOUTH', or None if square is empty.
        """
        unit = self.get_unit(row, col)
        if unit is None:
            return None
        # Use getattr to avoid circular imports with Unit type
        return getattr(unit, 'owner', None)

    def count_units(self, unit_type: Optional[str] = None,
                   owner: Optional[str] = None) -> int:
        """Count units on the board with optional filters.

        Args:
            unit_type: Unit type to count, or None for all types
            owner: Owner to count, or None for all owners

        Returns:
            Number of matching units
        """
        count = 0
        for row in range(self._rows):
            for col in range(self._cols):
                unit = self._board[row][col]
                if unit:
                    if unit_type is None or unit.unit_type == unit_type:
                        if owner is None or unit.owner == owner:
                            count += 1
        return count

    def get_units_by_type(self, unit_type: str) -> List[Tuple[int, int]]:
        """Get all coordinates containing a specific unit type.

        Args:
            unit_type: Unit type string

        Returns:
            List of (row, col) tuples containing unit type
        """
        units: List[Tuple[int, int]] = []
        for row in range(self._rows):
            for col in range(self._cols):
                unit = self._board[row][col]
                if unit and unit.unit_type == unit_type:
                    units.append((row, col))
        return units

    def get_units_by_owner(self, owner: str) -> List[Tuple[int, int]]:
        """Get all coordinates containing units owned by a player.

        Args:
            owner: 'NORTH' or 'SOUTH'

        Returns:
            List of (row, col) tuples containing player's units
        """
        units: List[Tuple[int, int]] = []
        for row in range(self._rows):
            for col in range(self._cols):
                unit = self._board[row][col]
                if unit and unit.owner == owner:
                    units.append((row, col))
        return units

    def get_all_units(self) -> Dict[Tuple[int, int], object]:
        """Get all units on the board.

        Returns:
            Dictionary mapping (row, col) tuples to Unit objects
        """
        units: Dict[Tuple[int, int], object] = {}
        for row in range(self._rows):
            for col in range(self._cols):
                unit = self._board[row][col]
                if unit:
                    units[(row, col)] = unit
        return units

    # Validation methods

    def is_valid_unit_type(self, unit_type: str) -> bool:
        """Check if unit type is valid.

        Returns True if unit_type is in ALL_UNIT_TYPES.
        """
        return unit_type in constants.ALL_UNIT_TYPES

    def is_valid_owner(self, owner: str) -> bool:
        """Check if owner is valid.

        Returns True if owner is NORTH or SOUTH.
        """
        return owner in (constants.PLAYER_NORTH, constants.PLAYER_SOUTH)

    def get_territory(self, row: int, col: int) -> str:
        """
        Determine which territory a square belongs to.

        Returns:
            'NORTH' if row < TERRITORY_BOUNDARY
            'SOUTH' if row >= TERRITORY_BOUNDARY
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        return constants.PLAYER_NORTH if row < self.TERRITORY_BOUNDARY else constants.PLAYER_SOUTH

    def is_north_territory(self, row: int, col: int) -> bool:
        """Check if square is in North territory."""
        return self.get_territory(row, col) == constants.PLAYER_NORTH

    def is_south_territory(self, row: int, col: int) -> bool:
        """Check if square is in South territory."""
        return self.get_territory(row, col) == constants.PLAYER_SOUTH

    def get_territory_squares(self, territory: str) -> List[Tuple[int, int]]:
        """
        Get all squares belonging to a territory.

        Args:
            territory: 'NORTH' or 'SOUTH'

        Returns:
            List of (row, col) tuples
        """
        if territory not in [constants.PLAYER_NORTH, constants.PLAYER_SOUTH]:
            raise ValueError(f"Invalid territory: {territory}")

        squares = []
        for row in range(self._rows):
            for col in range(self._cols):
                if self.get_territory(row, col) == territory:
                    squares.append((row, col))
        return squares

    @staticmethod
    def spreadsheet_to_tuple(coord: str) -> Tuple[int, int]:
        """
        Convert spreadsheet-style coordinate to internal (row, col) tuple.

        Args:
            coord: String in spreadsheet format (e.g., "1A", "10AA", "25Y")

        Returns:
            Tuple (row, col) where:
            - row: 0-based from top
            - col: 0-based from left

        Note: Coordinate origin is top-left (1A = top-left corner)
              Format: NUMBERS (column) + LETTERS (row)
              Debord's original convention: columns as numbers, rows as letters

        Example:
            "1A" -> (0, 0)      (top-left corner)
            "25T" -> (19, 24)   (bottom-right on 25-col board)
            "10AA" -> (26, 9)    (27th column, 10th row)
            "27A" -> (0, 26)     (top row, 28th column)
        """
        if not isinstance(coord, str):
            raise TypeError(f"Coord must be string, got {type(coord)}")

        # Check for empty or whitespace-only string
        if not coord or coord.isspace():
            raise ValueError(f"Invalid coord format: {coord}")

        # Check for spaces in string
        if ' ' in coord:
            raise ValueError(f"Invalid coord format: {coord}")

        # Separate numbers (column) and letters (row) - NUMBERS FIRST
        i = 0
        while i < len(coord) and coord[i].isdigit():
            i += 1

        col_number = coord[:i]
        row_letters = coord[i:]

        if not col_number or not row_letters:
            raise ValueError(f"Invalid coord format: {coord}")

        # Parse column (direct conversion from number)
        col_index = int(col_number) - 1  # Convert 1-based to 0-based

        # Validate column index (must be >= 0 after conversion)
        if col_index < 0:
            raise ValueError(f"Invalid coord format: {coord} (column must be >= 1)")

        # Parse row (A=0, Z=25, AA=26, AZ=51, BA=52, etc.)
        row_index = 0
        for char in row_letters:
            row_index = row_index * 26 + (ord(char.upper()) - ord('A') + 1)
        row_index -= 1  # Convert to 0-based

        return (row_index, col_index)

    @staticmethod
    def tuple_to_spreadsheet(row: int, col: int) -> str:
        """
        Convert internal (row, col) tuple to spreadsheet-style coordinate.

        Args:
            row: Row number (0-19, 0-based from top)
            col: Column number (0-24, 0-based from left)

        Returns:
            String in spreadsheet format (e.g., "1A", "10AA", "25Y")

        Note: Coordinate origin is top-left (1A = top-left corner)
              Format: NUMBERS (column) + LETTERS (row)
              Debord's original convention: columns as numbers, rows as letters

        Example:
            (0, 0) -> "1A"      (top-left corner)
            (19, 24) -> "25T"   (bottom-right on 25-col board)
            (9, 26) -> "27J"    (10th row, 27th column)
            (0, 27) -> "28A"     (top row, 28th column)
        """
        if not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("Row and col must be integers")

        # Format column (direct number conversion)
        col_number = col + 1  # Convert to 1-based

        # Format row (0=A, 1=B, 19=T, 20=U, etc.)
        row_index = row + 1  # Convert to 1-based
        row_letters: List[str] = []
        while row_index > 0:
            row_index -= 1
            row_letters.insert(0, chr(ord('A') + row_index % 26))
            row_index //= 26

        return f"{col_number}{''.join(row_letters)}"

    @staticmethod
    def tuple_to_index(row: int, col: int, board_cols: int = 25) -> int:
        """
        Convert row, col to square index (row-major order).

        Args:
            row: Row number (0-19)
            col: Column number (0-24)
            board_cols: Number of columns (default 25)

        Returns:
            Integer index (0-499)

        Example:
            (0, 0) -> 0
            (0, 1) -> 1
            (1, 0) -> 25
        """
        if row < 0 or col < 0:
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        return row * board_cols + col

    @staticmethod
    def index_to_tuple(index: int, board_cols: int = 25, board_rows: int = 20) -> Tuple[int, int]:
        """
        Convert square index to row, col tuple.

        Args:
            index: Integer index (0-499)
            board_cols: Number of columns (default 25)
            board_rows: Number of rows (default 20)

        Returns:
            Tuple (row, col)

        Example:
            0 -> (0, 0)
            1 -> (0, 1)
            25 -> (1, 0)
        """
        if not isinstance(index, int):
            raise TypeError(f"Index must be integer, got {type(index)}")

        max_index = board_cols * board_rows - 1
        if not (0 <= index <= max_index):
            raise ValueError(f"Invalid index: {index} (max: {max_index})")

        row = index // board_cols
        col = index % board_cols
        return (row, col)

    # Movement convenience methods

    def get_legal_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all legal moves for unit at given position.

        Convenience method that wraps movement.generate_moves.

        Args:
            row: Row of unit (0-19)
            col: Column of unit (0-24)

        Returns:
            List of (to_row, to_col) tuples

        Raises:
            ValueError: If no unit at position
        """
        from .movement import generate_moves
        return generate_moves(self, row, col)

    def is_legal_move(self, from_row: int, from_col: int,
                      to_row: int, to_col: int) -> bool:
        """Check if a move is legal.

        Convenience method that wraps movement.is_valid_move.

        Args:
            from_row: Source row (0-19)
            from_col: Source column (0-24)
            to_row: Target row (0-19)
            to_col: Target column (0-24)

        Returns:
            True if move is legal, False otherwise
        """
        from .movement import is_valid_move
        unit = self.get_unit(from_row, from_col)
        if unit is None:
            return False
        player = getattr(unit, 'owner', None)
        if player is None:
            return False
        return is_valid_move(self, from_row, from_col, to_row, to_col, player)

    def make_move(self, from_row: int, from_col: int,
                  to_row: int, to_col: int) -> object:
        """Make a move on the board.

        Convenience method that wraps movement.execute_move.

        Args:
            from_row: Source row (0-19)
            from_col: Source column (0-24)
            to_row: Target row (0-19)
            to_col: Target column (0-24)

        Returns:
            The Unit object that was moved

        Raises:
            ValueError: If move is invalid
        """
        from .movement import execute_move
        return execute_move(self, from_row, from_col, to_row, to_col)

    # Combat convenience methods

    def calculate_combat(self, target_row: int, target_col: int,
                        attacker: str, defender: str) -> Dict[str, object]:
        """Calculate complete combat scenario.

        Convenience method that wraps combat.calculate_combat.

        Args:
            target_row: Target row (0-19)
            target_col: Target column (0-24)
            attacker: 'NORTH' or 'SOUTH'
            defender: 'NORTH' or 'SOUTH'

        Returns:
            Dictionary with combat results
        """
        from .combat import calculate_combat
        return calculate_combat(self, target_row, target_col, attacker, defender)

    def execute_capture(self, target_row: int, target_col: int) -> object:
        """Execute a capture (remove target unit from board).

        Convenience method that wraps combat.execute_capture.

        Args:
            target_row: Target row (0-19)
            target_col: Target column (0-24)

        Returns:
            The captured Unit object
        """
        from .combat import execute_capture
        return execute_capture(self, target_row, target_col)

    # Retreat tracking methods

    def add_pending_retreat(self, row: int, col: int) -> None:
        """Add unit to pending retreats.

        This is called when combat resolves to RETREAT outcome.
        The actual retreat execution happens at the start of the defender's
        next turn (enforced by turn management in 0.1.4).

        Note: Retreats are tracked in-memory and not persisted in KFEN format.
        They are resolved each turn by turn management system.

        Args:
            row: Row of unit that must retreat
            col: Column of unit that must retreat

        Raises:
            ValueError: If no unit at position
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        unit = self.get_unit(row, col)
        if unit is None:
            raise ValueError(f"No unit at ({row}, {col}) to mark for retreat")

        # Check if already in retreat list to avoid duplicates
        if (row, col) not in self._pending_retreats:
            self._pending_retreats.append((row, col))

    def get_pending_retreats(self) -> List[Tuple[int, int]]:
        """Get all pending retreats.

        Returns:
            List of (row, col) tuples for units that must retreat
        """
        return list(self._pending_retreats)

    def clear_pending_retreats(self) -> None:
        """Clear all pending retreats after resolution.

        This should be called after all retreats have been processed
        at the start of a turn.
        """
        self._pending_retreats.clear()

    def has_pending_retreat(self, row: int, col: int) -> bool:
        """Check if unit at position must retreat.

        Args:
            row: Row of unit to check
            col: Column of unit to check

        Returns:
            True if unit at (row, col) must retreat, False otherwise
        """
        return (row, col) in self._pending_retreats

    # Retreat enforcement methods for 0.1.5

    def get_units_must_retreat(self) -> List[Tuple[int, int]]:
        """Get all units that must retreat this turn.

        Returns:
            List of (row, col) tuples for units that must retreat
            before making other moves
        """
        return list(self._units_must_retreat)

    def is_unit_in_retreat(self, row: int, col: int) -> bool:
        """Check if unit is currently in retreat mode.

        Args:
            row: Row of unit to check
            col: Column of unit to check

        Returns:
            True if unit at (row, col) is in retreat mode, False otherwise
        """
        return (row, col) in self._units_must_retreat

    def get_valid_retreat_positions(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid retreat positions for a unit.

        Args:
            row: Row of unit to check
            col: Column of unit to check

        Returns:
            List of (to_row, to_col) tuples representing valid retreat destinations

        Note:
            This uses same movement rules as normal moves (terrain-independent in 0.1.4)
        """
        from .movement import generate_moves
        return generate_moves(self, row, col)

    # Turn management methods for 0.1.4

    def has_moved_this_turn(self, row: int, col: int) -> bool:
        """Check if a move originated from this position this turn.

        Args:
            row: Row of position to check
            col: Column of position to check

        Returns:
            True if a unit moved FROM this position this turn, False otherwise
        """
        return (row, col) in self._moved_units

    def get_moves_this_turn(self) -> int:
        """Get number of units moved this turn.

        Returns:
            Number of units moved (0-5)
        """
        return len(self._moved_units)

    def can_move_more(self) -> bool:
        """Check if player can move more units this turn.

        Returns:
            True if fewer than 5 units have been moved, False otherwise
        """
        return len(self._moved_units) < constants.MAX_MOVES_PER_TURN

    def get_attacks_this_turn(self) -> int:
        """Get number of attacks made this turn.

        Returns:
            Number of attacks made (0 or 1)
        """
        return self._attacks_this_turn

    def get_attack_target(self) -> Optional[Tuple[int, int]]:
        """Get attack target square for current turn.

        Returns:
            Tuple (row, col) of target, or None if no attack/pass yet
        """
        return self._attack_target

    def can_attack_more(self) -> bool:
        """Check if player can attack more this turn.

        Returns:
            True if 0 attacks have been made, False otherwise
        """
        return self._attacks_this_turn < constants.MAX_ATTACKS_PER_TURN

    def validate_move(self, from_row: int, from_col: int,
                     to_row: int, to_col: int) -> bool:
        """Validate a move according to turn rules.

        Checks:
        1. Game is not over
        2. It's the movement phase
        3. The unit belongs to the current player
        4. The unit hasn't moved yet this turn
        5. The player hasn't moved 5 units yet
        6. If retreats are pending, only allow retreat moves
        7. The move is legally valid (pseudo-legal check)

        Args:
            from_row: Source row (0-19)
            from_col: Source column (0-24)
            to_row: Target row (0-19)
            to_col: Target column (0-24)

        Returns:
            True if move is valid according to turn rules, False otherwise
        """
        # NEW: Check if game is over
        if self.is_game_over():
            return False

        # Ensure network is up-to-date before checking movement
        self._ensure_network_calculated()

        # Check phase
        if self._current_phase != constants.PHASE_MOVEMENT:
            return False

        # Check unit ownership
        unit = self.get_unit(from_row, from_col)
        if unit is None:
            return False
        if unit and unit.owner != self._turn:  # type: ignore[attr-defined]
            return False

        # Check if unit already moved (by checking unit ID)
        unit_id = id(unit)
        if unit_id in self._moved_unit_ids:
            return False

        # NEW: If units must retreat, only allow those to move
        if self._units_must_retreat:
            if (from_row, from_col) not in self._units_must_retreat:
                return False

        # Check move limit
        if len(self._moved_units) >= constants.MAX_MOVES_PER_TURN:
            return False

        # Check move legality
        from .movement import is_valid_move
        unit = self.get_unit(from_row, from_col)
        if unit is None:
            return False
        player = getattr(unit, 'owner', None)
        if player is None:
            return False
        return is_valid_move(self, from_row, from_col, to_row, to_col, player)

    def make_turn_move(self, from_row: int, from_col: int,
                       to_row: int, to_col: int) -> Tuple[object, bool]:
        """Make a move with turn validation and tracking.

        Modified for 0.2.2: Check for enemy arsenal destruction.

        This method:
        1. Validates the move according to turn rules
        2. Executes the move
        3. Checks if destination is enemy arsenal and destroys it
        4. Tracks that the unit has moved this turn
        5. Clears the retreat flag if this was a retreat move

        Args:
            from_row: Source row (0-19)
            from_col: Source column (0-24)
            to_row: Target row (0-19)
            to_col: Target column (0-24)

        Returns:
            Tuple of (unit that moved, arsenal_destroyed flag)

        Raises:
            ValueError: If move is invalid according to turn rules
        """
        # Validate move
        if not self.validate_move(from_row, from_col, to_row, to_col):
            raise ValueError(
                f"Invalid turn move from ({from_row}, {from_col}) to ({to_row}, {to_col})"
            )

        # Get unit before move to track its ID
        unit = self.get_unit(from_row, from_col)
        unit_id = id(unit)

        # Check if destination is enemy arsenal before moving
        arsenal_destroyed = False
        destroyed_arsenal_info: Optional[Tuple[int, int, str]] = None
        if self._terrain[to_row][to_col] == constants.TERRAIN_ARSENAL:
            arsenal_owner = self._arsenal_owners.get((to_row, to_col))
            if arsenal_owner and arsenal_owner != unit.owner:  # type: ignore[attr-defined]
                # Capture arsenal info before destruction
                destroyed_arsenal_info = (to_row, to_col, arsenal_owner)
                # Destroy enemy arsenal
                self.destroy_arsenal(to_row, to_col)
                arsenal_destroyed = True

        # Execute move
        from .movement import execute_move
        moved_unit = execute_move(self, from_row, from_col, to_row, to_col)

        # Track move - both position and unit ID, plus complete move tuple
        self._moved_units.add((from_row, from_col))
        self._moved_unit_ids.add(unit_id)
        self._moves_made.append((from_row, from_col, to_row, to_col))

        # Clear retreat flag if this was a retreat move
        was_retreat = (from_row, from_col) in self._units_must_retreat
        if was_retreat:
            self._units_must_retreat.remove((from_row, from_col))


        # Record the move action
        self._record_move_action(
            from_pos=(from_row, from_col),
            to_pos=(to_row, to_col),
            unit_id=unit_id,
            unit_type=moved_unit.unit_type,  # type: ignore[attr-defined]
            owner=moved_unit.owner,  # type: ignore[attr-defined]
            was_retreat=was_retreat,
            destroyed_arsenal=destroyed_arsenal_info
        )

        return (moved_unit, arsenal_destroyed)

    def validate_attack(self, target_row: int, target_col: int) -> bool:
        """Validate an attack according to turn rules.

        Checks:
        1. Game is not over
        2. It's the battle phase
        3. The current player hasn't attacked yet
        4. There's at least one attacking unit
        5. No units must retreat (retreat enforcement)

        Args:
            target_row: Target row (0-19)
            target_col: Target column (0-24)

        Returns:
            True if attack is valid according to turn rules, False otherwise
        """
        # NEW: Check if game is over
        if self.is_game_over():
            return False

        # Ensure network is up-to-date before checking attack
        self._ensure_network_calculated()

        # Check phase
        if self._current_phase != constants.PHASE_BATTLE:
            return False

        # Check attack limit
        if self._attacks_this_turn >= constants.MAX_ATTACKS_PER_TURN:
            return False

        # NEW: Check if units must retreat - block attack until retreats resolved
        if self._units_must_retreat:
            return False

        # Check if attacker has units (can_attack will check this)
        from .combat import can_attack
        return can_attack(self, target_row, target_col, self._turn)

    def make_turn_attack(self, target_row: int, target_col: int) -> Dict[str, object]:
        """Make an attack with turn validation and tracking.

        This method:
        1. Validates the attack according to turn rules
        2. Calculates the combat result
        3. Executes capture if applicable
        4. Marks defender for retreat if applicable
        5. Tracks that an attack has been made

        Args:
            target_row: Target row (0-19)
            target_col: Target column (0-24)

        Returns:
            Dictionary with combat results

        Raises:
            ValueError: If attack is invalid according to turn rules
        """
        # Validate attack
        if not self.validate_attack(target_row, target_col):
            raise ValueError(
                f"Invalid turn attack at ({target_row}, {target_col})"
            )

        # Calculate combat
        defender = (
            constants.PLAYER_SOUTH
            if self._turn == constants.PLAYER_NORTH
            else constants.PLAYER_NORTH
        )
        result = self.calculate_combat(target_row, target_col, self._turn, defender)

        # Handle outcome
        from .combat import CombatOutcome
        outcome = result['outcome']
        captured_unit_info = None
        retreat_positions_to_record = []

        if outcome == CombatOutcome.CAPTURE:
            # Get captured unit info before executing capture
            target_unit = self.get_unit(target_row, target_col)
            if target_unit:
                captured_unit_info = {
                    'unit_type': target_unit.unit_type,  # type: ignore[attr-defined]
                    'owner': target_unit.owner  # type: ignore[attr-defined]
                }
            # Execute capture
            self.execute_capture(target_row, target_col)
        elif outcome == CombatOutcome.RETREAT:
            # Mark defender for retreat
            self.add_pending_retreat(target_row, target_col)
            # Track which units must retreat due to this attack
            # This includes the target and any nearby units in retreat mode
            retreat_positions_to_record = list(self._units_must_retreat)

        # Track attack and target
        self._attacks_this_turn += 1
        self._attack_target = (target_row, target_col)

        # Record attack action for undo/redo
        self._record_attack_action(
            target_pos=(target_row, target_col),
            outcome=str(outcome.value) if hasattr(outcome, 'value') else str(outcome),
            attacker=self._turn,
            captured_unit=captured_unit_info,
            retreat_positions=retreat_positions_to_record
        )

        return result

    def pass_attack(self) -> None:
        """Pass attack phase.

        This method:
        1. Validates it's battle phase
        2. Marks that an attack has been made (pass counts)
        3. Records pass state for KFEN serialization (attack_target = None)

        Raises:
            ValueError: If not in battle phase or already attacked
        """
        if self._current_phase != constants.PHASE_BATTLE:
            raise ValueError("Cannot pass attack: not in battle phase")

        if self._attacks_this_turn >= constants.MAX_ATTACKS_PER_TURN:
            raise ValueError("Cannot pass attack: already attacked")

        self._attacks_this_turn += 1
        self._attack_target = None  # Pass = no target

    def switch_to_battle_phase(self) -> None:
        """Switch from movement phase to battle phase.

        Raises:
            ValueError: If not in movement phase or units must retreat
        """
        if self._current_phase != constants.PHASE_MOVEMENT:
            raise ValueError("Cannot switch to battle phase: not in movement phase")

        # NEW: Prevent switching to battle phase if units must retreat
        if self._units_must_retreat:
            raise ValueError("Cannot switch to battle phase: units must retreat first")

        self._current_phase = constants.PHASE_BATTLE

    def resolve_retreats(self) -> List[Tuple[int, int, object, str]]:
        """Resolve pending retreats at the start of a turn.

        This method checks for pending retreats and enforces retreat rules:
        1. For each unit that must retreat, find valid retreat squares
        2. If valid retreat exists, mark unit as "must retreat" (player must choose destination)
        3. If no valid retreat exists, capture (destroy) the unit
        4. Clear pending retreats after resolution

        Returns:
            List of tuples (row, col, unit, reason) for captured units:
            - row, col: Position where unit was captured
            - unit: The captured unit object
            - reason: String explaining why unit was captured (e.g., "no valid retreat")

        Note:
            - This is called at the start of the defender's turn
            - Retreating units must move before other units can move
            - Units in retreat are tracked in _units_must_retreat

        TODO:
            - In 0.2.0, add terrain validation to retreat moves
            - In 0.2.0, check online/offline status for retreat
        """
        captured_units: List[Tuple[int, int, object, str]] = []
        # Only resolve retreats for current player's units
        retreat_positions = list(self._pending_retreats)

        for row, col in retreat_positions:
            unit = self.get_unit(row, col)
            if unit is None:
                # Unit already captured, skip
                continue

            # Only resolve retreats for current player
            if unit and getattr(unit, 'owner', None) != self._turn:
                continue

            # Find valid retreat squares
            # In 0.1.4, we use basic movement rules (terrain-independent)
            from .movement import generate_moves
            valid_moves = generate_moves(self, row, col)

            if valid_moves:
                # Mark unit as must retreat (player must choose destination)
                self._units_must_retreat.add((row, col))
            else:
                # No valid retreat: capture the unit and record info
                captured_unit = self.execute_capture(row, col)
                captured_units.append((row, col, captured_unit, "no valid retreat"))

        # Clear pending retreats for current player
        self._pending_retreats = [
            pos for pos in self._pending_retreats
            if pos not in retreat_positions
        ]

        return captured_units

    def end_turn(self) -> List[Tuple[int, int, object, str]]:
        """End current turn and switch to next player.

        This method:
        1. Clears moved unit tracking
        2. Clears attack counter
        3. Switches to other player
        4. Resets phase to movement
        5. Increments turn number
        6. Resolves any pending retreats for new player
        7. Recalculates networks to ensure victory checks have current state
        8. Checks victory conditions (new for 0.2.2)

        Returns:
            List of tuples (row, col, unit, reason) for captured units during retreat resolution

        Note:
            - Retreat resolution happens at the start of the new player's turn
            - Turn number increments on each player switch
            - Retreat state (_units_must_retreat) is NOT cleared automatically
            - It persists until the NEXT end_turn() call
            - This allows retreat state to persist during a player's turn
        """
        # Store old state before turn changes
        old_turn = (self._turn, self._turn_number)
        old_phase = self._current_phase
        old_moves_made = list(self._moves_made)
        old_attacks_this_turn = self._attacks_this_turn
        old_attack_target = self._attack_target
        old_units_must_retreat = set(self._units_must_retreat)

        # Switch player and increment turn
        self.increment_turn()

        # Clear per-turn state for new player
        self._moved_units.clear()
        self._moved_unit_ids.clear()
        self._moves_made.clear()  # Clear complete move history
        self._attacks_this_turn = 0
        self._attack_target = None  # Clear attack target

        # Resolve retreats for new player and capture any that have no valid retreat
        captured = self.resolve_retreats()

        # Recalculate networks before checking victory conditions
        # This ensures network collapse victory is detected after arsenal destruction
        if self._network_calculated:
            self._relay_online_status.clear()
            self.calculate_network(constants.PLAYER_NORTH)
            self.calculate_network(constants.PLAYER_SOUTH)
            self._network_dirty = False

        # NEW: Check victory conditions after turn
        self.check_victory()

        # Record turn boundary action for undo/redo
        new_turn = (self._turn, self._turn_number)
        self._record_turn_boundary(
            old_turn=old_turn,
            new_turn=new_turn,
            old_phase=old_phase,
            old_moves_made=old_moves_made,
            old_attacks_this_turn=old_attacks_this_turn,
            old_attack_target=old_attack_target,
            old_units_must_retreat=old_units_must_retreat
        )

        return captured

    def reset_turn_state(self) -> None:
        """Reset turn state without changing turn number or player.

        This method is useful for:
        - Undo functionality
        - Testing scenarios
        - Loading from FEN

        Resets:
        - Moved units tracking
        - Attack counter
        - Current phase (to movement)

        Does NOT reset:
        - Turn number
        - Current player
        - Pending retreats
        - Board position
        """
        self._moved_units.clear()
        self._moved_unit_ids.clear()
        self._moves_made.clear()  # Clear complete move history
        self._attacks_this_turn = 0
        self._attack_target = None  # Clear attack target
        self._current_phase = constants.PHASE_MOVEMENT

    # Turn tracking methods

    @property
    def turn_number(self) -> int:
        """Return current turn number."""
        return self._turn_number

    @turn_number.setter
    def turn_number(self, value: int) -> None:
        """Set turn number."""
        self._turn_number = value

    @property
    def current_phase(self) -> str:
        """Return current turn phase."""
        return self._current_phase

    @current_phase.setter
    def current_phase(self, value: str) -> None:
        """Set current turn phase."""
        self._current_phase = value

    def increment_turn(self) -> None:
        """Increment turn number and switch player."""
        self._turn_number += 1
        self._turn = (
            constants.PLAYER_SOUTH
            if self._turn == constants.PLAYER_NORTH
            else constants.PLAYER_NORTH
        )
        self._current_phase = constants.PHASE_MOVEMENT  # Reset to movement phase

    # =====================================================================
    # Undo/Redo Support
    # =====================================================================

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if undo is available, False otherwise
        """
        return self._undo_redo_manager.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if redo is available, False otherwise
        """
        return self._undo_redo_manager.can_redo()

    def undo(self, count: int = 1) -> None:
        """Undo one or more actions.

        Args:
            count: Number of actions to undo (default: 1)

        Raises:
            ValueError: If count exceeds available actions
        """
        if count == 1:
            self._undo_redo_manager.undo(self)
        else:
            self._undo_redo_manager.undo_multiple(self, count)

    def redo(self, count: int = 1) -> None:
        """Redo one or more actions.

        Args:
            count: Number of actions to redo (default: 1)

        Raises:
            ValueError: If count exceeds available actions
        """
        if count == 1:
            self._undo_redo_manager.redo(self)
        else:
            self._undo_redo_manager.redo_multiple(self, count)

    def set_max_undo_history(self, max_size: int) -> None:
        """Set maximum undo history size.

        Args:
            max_size: Maximum number of actions to keep. Set to 0 for unlimited.
        """
        self._undo_redo_manager.set_max_history(max_size)

    def _record_move_action(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        unit_id: int,
        unit_type: str,
        owner: str,
        was_retreat: bool,
        destroyed_arsenal: Optional[Tuple[int, int, str]] = None,
    ) -> None:
        """Record a move action for undo/redo.

        Args:
            from_pos: Source position (row, col)
            to_pos: Destination position (row, col)
            unit_id: Python ID of the unit
            unit_type: Type of unit (e.g., 'INFANTRY')
            owner: 'NORTH' or 'SOUTH'
            was_retreat: True if this was a retreat move
            destroyed_arsenal: Optional (row, col, owner) if arsenal was destroyed
        """
        from .undo_redo import MoveAction
        action = MoveAction(
            from_pos=from_pos,
            to_pos=to_pos,
            unit_id=unit_id,
            unit_type=unit_type,
            owner=owner,
            was_retreat=was_retreat,
            destroyed_arsenal=destroyed_arsenal
        )
        self._undo_redo_manager.record_action(action)

    def _record_attack_action(self, target_pos: Tuple[int, int], outcome: str,
                           attacker: str, captured_unit: Optional[Dict[str, Any]] = None,
                           retreat_positions: Optional[List[Tuple[int, int]]] = None) -> None:
        """Record an attack action for undo/redo.

        Args:
            target_pos: Target position (row, col)
            outcome: 'CAPTURE', 'RETREAT', or 'FAIL'
            attacker: 'NORTH' or 'SOUTH'
            captured_unit: Optional dict with 'unit_type' and 'owner' if captured
            retreat_positions: Optional list of positions marked for retreat
        """
        from .undo_redo import AttackAction
        action = AttackAction(
            target_pos=target_pos,
            outcome=outcome,
            attacker=attacker,
            captured_unit=captured_unit,
            retreat_positions=retreat_positions if retreat_positions is not None else []
        )
        self._undo_redo_manager.record_action(action)

    def _record_turn_boundary(self, old_turn: Tuple[str, int], new_turn: Tuple[str, int],
                           old_phase: str, old_moves_made: List[Tuple[int, int, int, int]],
                           old_attacks_this_turn: int, old_attack_target: Optional[Tuple[int, int]],
                           old_units_must_retreat: Set[Tuple[int, int]]) -> None:
        """Record a turn boundary action for undo/redo.

        Args:
            old_turn: (player, turn_number) before turn end
            new_turn: (player, turn_number) after turn end
            old_phase: Phase before turn end
            old_moves_made: List of moves made before turn end
            old_attacks_this_turn: Attack count before turn end
            old_attack_target: Attack target before turn end
            old_units_must_retreat: Set of units that must retreat before turn end
        """
        from .undo_redo import TurnBoundary
        action = TurnBoundary(
            from_turn=old_turn,
            to_turn=new_turn,
            from_phase=old_phase,
            from_moves_made=old_moves_made,
            from_attacks_this_turn=old_attacks_this_turn,
            from_attack_target=old_attack_target,
            from_units_must_retreat=old_units_must_retreat
        )
        self._undo_redo_manager.record_action(action)

    # =====================================================================
    # 0.2.0: Lines of Communication (LOC) Network System
    # =====================================================================

    # Terrain management methods

    def set_terrain(self, row: int, col: int, terrain: Optional[str]) -> None:
        """Set terrain type for a square.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            terrain: Terrain type (None, 'MOUNTAIN', 'MOUNTAIN_PASS', 'FORTRESS', 'ARSENAL')

        Raises:
            ValueError: If coordinates are invalid or terrain type is invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        if terrain is not None and terrain not in constants.ALL_TERRAIN_TYPES:
            raise ValueError(f"Invalid terrain type: {terrain}")

        self._terrain[row][col] = terrain

    def get_terrain(self, row: int, col: int) -> Optional[str]:
        """Get terrain type for a square.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Returns:
            Terrain type or None if no terrain

        Raises:
            ValueError: If coordinates are invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        return self._terrain[row][col]

    # Network state helper methods

    def _mark_square_covered(self, row: int, col: int, player: str) -> None:
        """Mark a square as covered by a player's network.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            player: 'NORTH' or 'SOUTH'
        """
        if player == constants.PLAYER_NORTH:
            self._network_coverage_north.add((row, col))
        else:
            self._network_coverage_south.add((row, col))

    def _mark_unit_active(self, row: int, col: int, player: str) -> None:
        """Mark a unit as active in the network.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            player: 'NORTH' or 'SOUTH'
        """
        if player == constants.PLAYER_NORTH:
            self._active_north.add((row, col))
        else:
            self._active_south.add((row, col))

        # Also mark the square as covered by the network
        self._mark_square_covered(row, col, player)

        # For relays/swift relays, also track online status
        unit = self.get_unit(row, col)
        if unit:
            unit_type = getattr(unit, 'unit_type', None)
            if unit_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                if (row, col) not in self._relay_online_status:
                    self._relay_online_status[(row, col)] = True
            else:
                # For combat units, also track in relay_online_status for consistency
                # This ensures is_unit_online works correctly for all units
                if (row, col) not in self._relay_online_status:
                    self._relay_online_status[(row, col)] = True

    def _is_unit_active(self, row: int, col: int, player: str) -> bool:
        """Check if a unit is active in the network.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            player: 'NORTH' or 'SOUTH'

        Returns:
            True if unit is active, False otherwise
        """
        if player == constants.PLAYER_NORTH:
            return (row, col) in self._active_north
        else:
            return (row, col) in self._active_south

    def _is_relay_online(self, row: int, col: int) -> bool:
        """Check if a relay/swift relay is online.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Returns:
            True if relay is online, False otherwise
        """
        return self._relay_online_status.get((row, col), False)

    def _set_relay_online(self, row: int, col: int, online: bool) -> None:
        """Set a relay/swift relay's online status.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            online: True if online, False otherwise
        """
        self._relay_online_status[(row, col)] = online

    def _get_active_units(self, player: str) -> Set[Tuple[int, int]]:
        """Get all active units for a player.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            Set of (row, col) tuples
        """
        if player == constants.PLAYER_NORTH:
            return self._active_north.copy()
        else:
            return self._active_south.copy()

    def _get_arsenals(self, player: str) -> List[Tuple[int, int]]:
        """Get all arsenal squares for a player.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            List of (row, col) tuples
        """
        arsenals = []
        for (row, col), owner in self._arsenal_owners.items():
            if owner == player:
                arsenals.append((row, col))
        return arsenals

    def set_arsenal(self, row: int, col: int, owner: str) -> None:
        """Set arsenal terrain with owner.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            owner: 'NORTH' or 'SOUTH'

        Raises:
            ValueError: If coordinates are invalid or owner is invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        if owner not in (constants.PLAYER_NORTH, constants.PLAYER_SOUTH):
            raise ValueError(f"Invalid owner: {owner}")

        self._terrain[row][col] = constants.TERRAIN_ARSENAL
        self._arsenal_owners[(row, col)] = owner
        self._network_dirty = True  # Mark network as needing recalculation

    def get_arsenal_owner(self, row: int, col: int) -> Optional[str]:
        """Get owner of arsenal at given coordinates.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Returns:
            'NORTH', 'SOUTH', or None if no arsenal

        Raises:
            ValueError: If coordinates are invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        terrain = self._terrain[row][col]
        if terrain == constants.TERRAIN_ARSENAL:
            return self._arsenal_owners.get((row, col))
        return None

    def remove_arsenal(self, row: int, col: int) -> None:
        """Remove arsenal from square.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Raises:
            ValueError: If coordinates are invalid
        """
        if not self.is_valid_square(row, col):
            raise ValueError(f"Invalid coordinates: ({row}, {col})")

        self._terrain[row][col] = None
        if (row, col) in self._arsenal_owners:
            del self._arsenal_owners[(row, col)]
        self._network_dirty = True  # Mark network as needing recalculation

    def _get_unpropagated_relays(self, player: str) -> List[Tuple[int, int]]:
        """Get all online relays/swift relays that haven't propagated yet.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            List of (row, col) tuples
        """
        relays = []
        active_units = self._get_active_units(player)

        for row, col in active_units:
            unit = self.get_unit(row, col)
            if unit:
                unit_type = getattr(unit, 'unit_type', None)
                if unit_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                    # Only return relays that are online AND haven't propagated yet
                    if (
                        self._is_relay_online(row, col)
                        and (row, col) not in self._proximity_checked
                    ):
                        relays.append((row, col))

        return relays

    def _get_newly_activated_relays(self, player: str) -> List[Tuple[int, int]]:
        """Get relays/swift relays activated in the most recent proximity check.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            List of (row, col) tuples
        """
        relays = []
        active_units = self._get_active_units(player)

        for row, col in active_units:
            # If it's a relay/swift relay that's online but hasn't propagated yet
            unit = self.get_unit(row, col)
            if unit:
                unit_type = getattr(unit, 'unit_type', None)
                if unit_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                    if (
                        self._is_relay_online(row, col)
                        and (row, col) not in self._proximity_checked
                    ):
                        relays.append((row, col))

        return relays

    def _reset_network_state(self, player: str) -> None:
        """Reset tracking state for a new network calculation.

        Args:
            player: 'NORTH' or 'SOUTH'
        """
        if player == constants.PLAYER_NORTH:
            self._active_north.clear()
            self._network_coverage_north.clear()
            self._ray_coverage_north.clear()
        else:
            self._active_south.clear()
            self._network_coverage_south.clear()
            self._ray_coverage_south.clear()

        # Only clear relay_online_status when recalculating for both players
        # This is handled in _ensure_network_calculated()
        # Don't clear it here to preserve other player's relay status
        self._proximity_checked.clear()

    # Ray-casting algorithm

    def _cast_ray(self, origin_row: int, origin_col: int, dx: int, dy: int,
                  player: str, source_is_arsenal: bool) -> bool:
        """Cast a ray from origin in direction (dx, dy) until hitting a blocking obstacle.

        Args:
            origin_row: Starting row (0-19)
            origin_col: Starting column (0-24)
            dx, dy: Direction vector
            player: The player whose network we're calculating
            source_is_arsenal: True if ray originates from an arsenal, False if from relay

        Returns:
            True if any relay/swift relay was activated along this ray
        """
        x, y = origin_col, origin_row
        relay_activated = False

        # Extend ray to board edge
        while True:
            x += dx
            y += dy

            # Check board bounds
            if not self.is_valid_square(y, x):
                break

            current_unit = self.get_unit(y, x)
            current_terrain = self._terrain[y][x]

            # Case 1: Empty square - continue ray
            if current_unit is None:
                # Check terrain at empty square
                if current_terrain == constants.TERRAIN_MOUNTAIN:
                    break  # Mountains block the ray
                # Mountain passes and fortresses don't block
                # Mark empty square as covered by network
                self._mark_square_covered(y, x, player)
                # Also mark in ray coverage for display purposes
                if player == constants.PLAYER_NORTH:
                    self._ray_coverage_north.add((y, x))
                else:
                    self._ray_coverage_south.add((y, x))
                continue

            # Case 2: Friendly unit - activate and continue (except relays may stop)
            current_owner = getattr(current_unit, 'owner', None)
            current_type = getattr(current_unit, 'unit_type', None)

            if current_owner == player:
                self._mark_unit_active(y, x, player)

                # Also mark the square as ray-covered for display purposes
                # This ensures occupied terrain squares (fortresses, passes) show correct colors
                if player == constants.PLAYER_NORTH:
                    self._ray_coverage_north.add((y, x))
                else:
                    self._ray_coverage_south.add((y, x))

                # If it's a relay/swift relay, activate it and continue
                if current_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                    if not self._is_relay_online(y, x):
                        self._set_relay_online(y, x, True)
                        relay_activated = True

                # Friendly non-relay units don't block the ray (they're transparent)
                continue

            # Case 3: Enemy unit
            # All enemy units block the ray (including relays)
            break

        return relay_activated

    # Network calculation steps

    def _step1_arsenal_propagation(self, player: str) -> None:
        """Step 1: Ray-based propagation from arsenals.

        Arsenals radiate lines of communication in all 8 directions to the board edge.

        Args:
            player: 'NORTH' or 'SOUTH'
        """
        arsenals = self._get_arsenals(player)

        for arsenal_row, arsenal_col in arsenals:
            # Mark arsenal as active
            self._mark_unit_active(arsenal_row, arsenal_col, player)

            # Ray-cast in all 8 directions
            for dx, dy in constants.DIRECTIONS:
                self._cast_ray(arsenal_row, arsenal_col, dx, dy, player, source_is_arsenal=True)

    def _step2_relay_propagation(self, player: str) -> None:
        """Step 2: Ray-based propagation from activated relays/swift relays.

        This step repeats until no more valid relays are activated.

        Args:
            player: 'NORTH' or 'SOUTH'
        """
        while True:
            new_relays_activated = False

            # Get all online relays/swift relays that haven't propagated yet
            active_relays = self._get_unpropagated_relays(player)

            for relay_row, relay_col in active_relays:
                # Ray-cast in all 8 directions
                for dx, dy in constants.DIRECTIONS:
                    did_activate = self._cast_ray(
                        relay_row, relay_col, dx, dy, player, source_is_arsenal=False
                    )
                    if did_activate:
                        new_relays_activated = True

                # Mark this relay as propagated
                self._proximity_checked.add((relay_row, relay_col))

            # If no new relays were activated AND all relays have propagated, we're done
            if not new_relays_activated and not self._get_unpropagated_relays(player):
                break

    def _step3_proximity_propagation(self, player: str) -> bool:
        """Step 3: Proximity-based propagation from active units.

        This step repeats until all active units have been proximity-checked.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            True if new units were activated, False otherwise
        """
        new_units_activated = False
        units_to_check = list(
            self._get_active_units(player)
        )  # Copy to avoid modification during iteration

        for unit_row, unit_col in units_to_check:
            if (unit_row, unit_col) in self._proximity_checked:
                continue

            # Mark this unit as proximity-checked
            self._proximity_checked.add((unit_row, unit_col))

            # Check all 8 adjacent squares
            for dx, dy in constants.DIRECTIONS:
                adj_row = unit_row + dy
                adj_col = unit_col + dx

                if not self.is_valid_square(adj_row, adj_col):
                    continue

                adj_unit = self.get_unit(adj_row, adj_col)

                # Case 1: Empty square - mark as covered by network
                # This allows units with movement range 2+ to move through empty squares
                # adjacent to friendly units (fixes path validation bug)
                # BUT mountains block proximity propagation too
                if adj_unit is None:
                    # Check terrain before marking as covered
                    adj_terrain = self._terrain[adj_row][adj_col]
                    if adj_terrain == constants.TERRAIN_MOUNTAIN:
                        # Mountain terrain - not covered by proximity
                        continue
                    # Passable terrain (None, MOUNTAIN_PASS, FORTRESS, ARSENAL)
                    self._mark_square_covered(adj_row, adj_col, player)
                    continue

                # Case 2: Square has a unit
                adj_owner = getattr(adj_unit, 'owner', None)
                if adj_owner != player:
                    # Enemy unit - skip
                    continue

                if self._is_unit_active(adj_row, adj_col, player):
                    # Already active - skip
                    continue

                # Activate adjacent friendly unit
                self._mark_unit_active(adj_row, adj_col, player)
                new_units_activated = True

        return new_units_activated

    def _step4_relay_propagation_from_proximity(self, player: str) -> None:
        """Step 4: Ray-based propagation from relays/swift relays activated by proximity.

        This step is optional and defaults to True.

        Args:
            player: 'NORTH' or 'SOUTH'
        """
        # Get relays that were just activated by proximity but haven't propagated yet
        newly_activated_relays = self._get_newly_activated_relays(player)

        for relay_row, relay_col in newly_activated_relays:
            # Mark as propagated
            if (relay_row, relay_col) not in self._proximity_checked:
                self._proximity_checked.add((relay_row, relay_col))

                # Ray-cast in all 8 directions
                for dx, dy in constants.DIRECTIONS:
                    self._cast_ray(relay_row, relay_col, dx, dy, player, source_is_arsenal=False)

    # Main network calculation method

    def calculate_network(self, player: str, enable_step4: bool = True) -> None:
        """Calculate lines of communication network for specified player.

        This must be called after any board state change.

        Args:
            player: The player to calculate network for ('NORTH' or 'SOUTH')
            enable_step4: Whether to enable step 4 (ray propagation from proximity-activated relays)
        """
        # Note: _network_calculated is NOT set here. It is set by enable_networks()
        # to maintain backward compatibility - networks are disabled by default.

        # Reset state for this calculation cycle
        self._reset_network_state(player)

        # Step 1: Initial ray-based propagation from arsenals
        self._step1_arsenal_propagation(player)

        # Step 2: Ray-based propagation from activated relays/swift relays
        # Repeat until no more relays are activated
        self._step2_relay_propagation(player)

        # Step 3: Proximity-based propagation from all active units
        # Repeat until all active units have been proximity-checked
        self._step3_proximity_propagation(player)

        # Step 4: Optional ray-based propagation from proximity-activated relays
        if enable_step4:
            self._step4_relay_propagation_from_proximity(player)

            # Step 5: Return to step 3 if any units were activated in step 4
            # This loop continues until no new units are activated
            while True:
                new_units_activated = self._step3_proximity_propagation(player)
                if not new_units_activated:
                    break
                self._step4_relay_propagation_from_proximity(player)

    # Helper for lazy network calculation

    def _ensure_network_calculated(self) -> None:
        """Ensure network is up-to-date before querying network state.

        This lazy calculation approach recalculates networks only when needed,
        avoiding unnecessary recalculations during batch operations like
        test setup or FEN loading.
        """
        # Only recalculate if network has been calculated before and is now dirty
        # This ensures backward compatibility: if network has never been calculated,
        # we don't force calculation (optimistic default applies)
        if self._network_calculated and self._network_dirty:
            # Clear relay status before recalculating both players
            self._relay_online_status.clear()

            # Recalculate when dirty (ensures online/offline status is correct)
            from .constants import PLAYER_NORTH, PLAYER_SOUTH
            self.calculate_network(PLAYER_NORTH)
            self.calculate_network(PLAYER_SOUTH)
            self._network_dirty = False

    # Network configuration methods

    def set_adjacency_relay_propagation(self, enable: bool) -> None:
        """Enable/disable adjacency-based relay propagation (Step 4).

        When enabled (default): Relays activated by proximity to an online unit
        will propagate their own LOC rays in all 8 directions.

        When disabled: Relays only propagate LOC rays when activated via
        arsenal rays or other relay rays (original Debord behavior).

        Args:
            enable: True to enable, False to disable
        """
        self._enable_adjacency_relay_propagation = enable
        # Mark network as dirty so recalculation uses new setting
        self._network_dirty = True

    def get_adjacency_relay_propagation(self) -> bool:
        """Check if adjacency-based relay propagation is enabled.

        Returns:
            True if Step 4 is enabled, False otherwise
        """
        return self._enable_adjacency_relay_propagation

    # Public API for network queries

    def enable_networks(self) -> None:
        """Enable network rules for both players.

        This method activates Lines of Communication system, after which
        units must be connected to arsenals through to network to function.

        Once enabled, network system enforces:
        - Units not connected to network have 0 attack/defense/range (except relays)
        - Units not connected to network have 0 movement (except relays/swift relays)

        Note: This should be called explicitly when network rules are desired.
        The default behavior is that networks are disabled (all units online).

        The optional Step 4 (adjacency-based relay propagation) is controlled
        by Board constructor's enable_adjacency_relay_propagation parameter.

        Example:
            >>> board = Board()  # Step 4 enabled (default)
            >>> board.create_and_place_unit(5, 10, 'ARSENAL', 'NORTH')
            >>> board.create_and_place_unit(5, 12, 'INFANTRY', 'NORTH')
            >>> # Enable network rules
            >>> board.enable_networks()
            >>> board = Board(enable_adjacency_relay_propagation=False)  # Step 4 disabled
        """
        self._network_calculated = True
        self.calculate_network(constants.PLAYER_NORTH,
                          enable_step4=self._enable_adjacency_relay_propagation)
        self.calculate_network(constants.PLAYER_SOUTH,
                          enable_step4=self._enable_adjacency_relay_propagation)
        # Clear dirty flag after manual network calculation
        self._network_dirty = False

    def is_unit_online(self, row: int, col: int, player: str) -> bool:
        """Check if a square is covered by network for a player.

        This checks if the square is within network coverage,
        which includes both units and empty squares covered by rays.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            player: 'NORTH' or 'SOUTH'

        Returns:
            True if square is covered by network, False otherwise

        Note:
            If network has never been calculated (_network_calculated == False),
            returns True for all squares (optimistic default). This ensures backward
            compatibility and allows normal movement before network system is invoked.
        """
        # Optimistic default: assume online if network hasn't been calculated
        if not self._network_calculated:
            return True

        self._ensure_network_calculated()  # Lazy recalculation if needed
        if player == constants.PLAYER_NORTH:
            return (row, col) in self._network_coverage_north
        else:
            return (row, col) in self._network_coverage_south

    def is_relay_online(self, row: int, col: int) -> bool:
        """Check if a relay/swift relay is online.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Returns:
            True if relay is online, False otherwise

        Note:
            If network has never been calculated (_network_calculated == False),
            returns True for all relays (optimistic default). This ensures backward
            compatibility and allows normal movement before network system is invoked.
        """
        # Optimistic default: assume online if network hasn't been calculated
        if not self._network_calculated:
            return True

        self._ensure_network_calculated()  # Lazy recalculation if needed
        unit = self.get_unit(row, col)
        if unit:
            unit_type = getattr(unit, 'unit_type', None)
            if unit_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                return self._is_relay_online(row, col)
        return False

    def get_online_units(self, player: str) -> Set[Tuple[int, int]]:
        """Get all online units for a player.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            Set of (row, col) tuples

        Note:
            If network has never been calculated (_network_calculated == False),
            returns all units for the player (optimistic default). This ensures
            backward compatibility and allows normal movement before network system is invoked.
        """
        # Optimistic default: return all units if network hasn't been calculated
        if not self._network_calculated:
            return set(self.get_units_by_owner(player))

        self._ensure_network_calculated()  # Lazy recalculation if needed
        return self._get_active_units(player)

    def get_offline_units(self, player: str) -> Set[Tuple[int, int]]:
        """Get all offline units for a player.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            Set of (row, col) tuples

        Note:
            If network has never been calculated (_network_calculated == False),
            returns empty set (optimistic default - no units are offline).
        """
        # Optimistic default: no offline units if network hasn't been calculated
        if not self._network_calculated:
            return set()

        self._ensure_network_calculated()  # Lazy recalculation if needed
        all_units = set(self.get_units_by_owner(player))
        online_units = self.get_online_units(player)
        return all_units - online_units

    def get_network_active_relays(self, player: str) -> Set[Tuple[int, int]]:
        """Get all relays/swift relays that are online and can propagate.

        Args:
            player: 'NORTH' or 'SOUTH'

        Returns:
            Set of (row, col) tuples
        """
        self._ensure_network_calculated()  # Lazy recalculation if needed
        online_units = self.get_online_units(player)
        active_relays = set()

        for row, col in online_units:
            unit = self.get_unit(row, col)
            if unit:
                unit_type = getattr(unit, 'unit_type', None)
                if unit_type in (constants.UNIT_RELAY, constants.UNIT_SWIFT_RELAY):
                    if self._is_relay_online(row, col):
                        active_relays.add((row, col))

        return active_relays

    def is_ray_covered(self, row: int, col: int, player: str) -> bool:
        """Check if a square is covered by arsenal/relay rays only (for display).

        This method is used by display code to determine which squares should be
        shown as green (online via rays) vs grey (online only via proximity).

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)
            player: 'NORTH' or 'SOUTH'

        Returns:
            True if square is covered by arsenal/relay rays, False otherwise

        Note:
            - This is purely for visual representation purposes
            - Does not affect game mechanics (movement, combat, etc.)
            - Use is_unit_online() for game mechanic queries
            - Returns True for squares covered by ray propagation (steps 1 and 2)
            - Returns False for squares only covered by proximity propagation (step 3)

        Example:
            >>> board = Board()
            >>> board.set_arsenal(10, 10, 'NORTH')
            >>> board.enable_networks()
            >>> # Square covered by arsenal ray will be ray_covered
            >>> board.is_ray_covered(10, 15, 'NORTH')  # True
            >>> # Square covered only by proximity won't be ray_covered
            >>> board.is_ray_covered(11, 14, 'NORTH')  # False
            >>> # But it's still online for game mechanics
            >>> board.is_unit_online(11, 14, 'NORTH')  # True
        """
        self._ensure_network_calculated()  # Lazy recalculation if needed
        if player == constants.PLAYER_NORTH:
            return (row, col) in self._ray_coverage_north
        else:
            return (row, col) in self._ray_coverage_south

    # =====================================================================
    # 0.2.2: Victory Condition Detection
    # =====================================================================

    @property
    def game_state(self) -> str:
        """Return current game state.

        Returns:
            'ONGOING', 'NORTH_WINS', 'SOUTH_WINS', or 'DRAW'
        """
        return self._game_state

    @property
    def victory_result(self) -> Optional[Dict[str, object]]:
        """Return victory result if game has ended, None otherwise.

        Returns:
            Dictionary with victory details or None if game is ongoing.
            Keys: 'game_state', 'winner', 'victory_condition', 'details'
        """
        return self._victory_result

    def is_game_over(self) -> bool:
        """Check if game has ended.

        Returns:
            True if game is over (winner determined or draw), False otherwise
        """
        return self._game_state != "ONGOING"

    def check_victory(self) -> Dict[str, object]:
        """Check victory conditions and update game state.

        This method should be called after each turn to detect victory conditions.

        Returns:
            Dictionary with victory details:
            - 'game_state': Current game state
            - 'winner': Winning player or None
            - 'victory_condition': Specific condition met or None
            - 'details': Human-readable explanation
        """
        from .victory import check_victory_conditions

        result = check_victory_conditions(self)
        self._game_state = result.game_state.value
        self._victory_result = {
            'game_state': result.game_state.value,
            'winner': result.winner,
            'victory_condition': (
                result.victory_condition.value
                if result.victory_condition
                else None
            ),
            'details': result.details
        }

        return self._victory_result

    def handle_surrender(self, player: str) -> None:
        """Handle a player's surrender.

        This method sets the game state to indicate the surrendering player has lost.

        Args:
            player: 'NORTH' or 'SOUTH' - the player who is surrendering

        Raises:
            ValueError: If game is already over or player is invalid
        """
        # Check if game is already over
        if self.is_game_over():
            raise ValueError("Cannot surrender: game is already over")

        # Validate player
        if player not in (constants.PLAYER_NORTH, constants.PLAYER_SOUTH):
            raise ValueError(f"Invalid player: {player}")

        # Determine winner (opponent of surrendering player)
        winner = (
            constants.PLAYER_SOUTH
            if player == constants.PLAYER_NORTH
            else constants.PLAYER_NORTH
        )

        # Update game state
        self._game_state = f"{winner}_WINS"
        self._victory_result = {
            'game_state': self._game_state,
            'winner': winner,
            'victory_condition': 'SURRENDER',
            'details': f"{winner} wins: {player} has surrendered"
        }

    def destroy_arsenal(self, row: int, col: int) -> None:
        """Destroy an arsenal at the specified position.

        This is called when a unit moves onto an enemy arsenal.
        The arsenal is removed from the board and the terrain becomes empty.

        Args:
            row: Row coordinate (0-19)
            col: Column coordinate (0-24)

        Raises:
            ValueError: If position doesn't contain an arsenal
        """
        if self._terrain[row][col] != constants.TERRAIN_ARSENAL:
            raise ValueError(f"No arsenal at position ({row}, {col})")

        # Remove arsenal terrain (set to None for empty terrain)
        self._terrain[row][col] = None

        # Remove from arsenal owners dict
        if (row, col) in self._arsenal_owners:
            del self._arsenal_owners[(row, col)]

        # Mark network as dirty for recalculation
        self._network_dirty = True

        # NOTE: Victory checking is deferred until end_turn() is called
        # This ensures the turn state is properly updated (turn number, captured units, etc.)
        # before determining victory conditions. The network will be recalculated
        # as part of end_turn() -> resolve_retreats() -> check_victory() sequence.
