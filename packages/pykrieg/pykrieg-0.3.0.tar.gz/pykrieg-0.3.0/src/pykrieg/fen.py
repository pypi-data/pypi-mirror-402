"""
FEN (Forsyth-Edwards Notation) for Pykrieg board serialization.

This module implements FEN serialization/deserialization for the
0.1.0 version of Pykrieg, supporting basic board state representation.
"""

from typing import TYPE_CHECKING

from . import constants

if TYPE_CHECKING:
    from .board import Board


class Fen:
    """FEN (Forsyth-Edwards Notation) for Pykrieg board serialization.

    This is 0.1.0 basic implementation supporting:
    - Board serialization/deserialization
    - Basic piece representation
    - Turn tracking

    FEN Format (0.1.4 - With Turn State):
    <board_data>/<turn>/<phase>/<actions>/<turn_number>/<retreats>

    Where:
    - board_data: Row-by-row representation of pieces (20 rows separated by '/')
    - turn: Current player ('N' or 'S')
    - phase: Turn phase ('M' for movement, 'B' for battle)
    - actions: Move pairs or attack target (empty list in 0.1.4)
    - turn_number: Current turn number (1, 2, 3, ...)
    - retreats: List of retreat positions [row1,col1,row2,col2,...]

    Note: Retreats are tracked in-memory and may be lost on FEN serialization.

    Board Data Format:
    - Each row separated by '/'
    - Pieces: unit_type (e.g., 'I', 'C', 'K', 'A', 'R', 'W', 'X')
    - Uppercase: North pieces
    - Lowercase: South pieces
    - Empty squares: '_'

    Example FEN:
    ___________________________/.../_________________________/N/M/[]
    """

    # Use piece symbols from constants
    PIECE_SYMBOLS = constants.FEN_SYMBOLS
    SYMBOL_TO_PIECE = constants.SYMBOL_TO_UNIT

    @staticmethod
    def board_to_fen(board: 'Board', include_turn_state: bool = True) -> str:
        """
        Convert Board object to FEN string (0.2.1 with terrain).

        Args:
            board: Board object
            include_turn_state: If False, omit turn/phase/turn_number/retreats (for KFEN embedding)

        Returns:
            FEN string representation

        Note:
            Uses bracket notation for terrain: (unit) on pass, [unit] in fortress
            Empty terrain: p (pass), f (fortress), m (mountain)

        Example:
            Empty board: "_________________________/.../N/M/[]/1/[]"
            With terrain: "_____________________(I)______________/.../N/M/[]/1/[]"
        """
        # Build board data section with terrain and units
        rows_fen = []
        for row in range(board.rows):
            row_fen = []
            for col in range(board.cols):
                piece = board.get_unit(row, col)
                terrain = board.get_terrain(row, col)

                if terrain == 'MOUNTAIN':
                    # Mountain: always empty, represented as 'm'
                    row_fen.append('m')
                elif terrain == 'MOUNTAIN_PASS':
                    # Mountain pass: empty 'p' or unit '(I)'
                    if piece is None:
                        row_fen.append('p')
                    else:
                        # Handle both Unit objects and dict-style pieces
                        if hasattr(piece, 'unit_type'):
                            unit_type = getattr(piece, 'unit_type', None)
                            owner = getattr(piece, 'owner', None)
                        else:
                            unit_type = piece.get('type') if isinstance(piece, dict) else None
                            owner = piece.get('owner') if isinstance(piece, dict) else None

                        if unit_type is None:
                            raise ValueError("Piece has no unit_type attribute")
                        symbol = Fen.PIECE_SYMBOLS[unit_type]
                        if owner == 'SOUTH':
                            symbol = symbol.lower()
                        row_fen.append(f'({symbol})')
                elif terrain == 'FORTRESS':
                    # Fortress: empty 'f' or unit '[I]'
                    if piece is None:
                        row_fen.append('f')
                    else:
                        # Handle both Unit objects and dict-style pieces
                        if hasattr(piece, 'unit_type'):
                            unit_type = getattr(piece, 'unit_type', None)
                            owner = getattr(piece, 'owner', None)
                        else:
                            unit_type = piece.get('type') if isinstance(piece, dict) else None
                            owner = piece.get('owner') if isinstance(piece, dict) else None

                        if unit_type is None:
                            raise ValueError("Piece has no unit_type attribute")
                        symbol = Fen.PIECE_SYMBOLS[unit_type]
                        if owner == 'SOUTH':
                            symbol = symbol.lower()
                        row_fen.append(f'[{symbol}]')
                elif terrain == 'ARSENAL':
                    # Arsenal terrain: 'A' (North), 'a' (South), 'A{I}'
                    # (North with unit), 'a{i}' (South with unit)
                    owner = board.get_arsenal_owner(row, col)
                    if piece is None:
                        # Empty arsenal - encode owner via case
                        row_fen.append('A' if owner == 'NORTH' else 'a')
                    else:
                        # Unit on arsenal - encode owner via case, unit in curly braces
                        # Handle both Unit objects and dict-style pieces
                        if hasattr(piece, 'unit_type'):
                            unit_type = getattr(piece, 'unit_type', None)
                            piece_owner = getattr(piece, 'owner', None)
                        else:
                            unit_type = piece.get('type') if isinstance(piece, dict) else None
                            piece_owner = piece.get('owner') if isinstance(piece, dict) else None

                        if unit_type is None:
                            raise ValueError("Piece has no unit_type attribute")
                        symbol = Fen.PIECE_SYMBOLS[unit_type]
                        if piece_owner == 'SOUTH':
                            symbol = symbol.lower()
                        row_fen.append(f'{"A" if owner == "NORTH" else "a"}{{{symbol}}}')
                else:
                    # Flat terrain: empty '_' or unit 'I'
                    if piece is None:
                        row_fen.append('_')
                    else:
                        # Handle both Unit objects and dict-style pieces
                        if hasattr(piece, 'unit_type'):
                            unit_type = getattr(piece, 'unit_type', None)
                            owner = getattr(piece, 'owner', None)
                        else:
                            # Dict-style pieces use dict access, not getattr
                            unit_type = piece.get('type') if isinstance(piece, dict) else None
                            owner = piece.get('owner') if isinstance(piece, dict) else None

                        if unit_type is None:
                            raise ValueError("Piece has no unit_type attribute")
                        symbol = Fen.PIECE_SYMBOLS[unit_type]
                        # Convert to lowercase for South
                        if owner == 'SOUTH':
                            symbol = symbol.lower()
                        row_fen.append(symbol)
            rows_fen.append(''.join(row_fen))

        board_data = '/'.join(rows_fen)

        # If not including turn state (for KFEN embedding), return just board data
        if not include_turn_state:
            return board_data

        # Build turn info
        turn_char = 'N' if board.turn == constants.PLAYER_NORTH else 'S'
        phase = board.current_phase
        turn_number = str(board.turn_number)

        # Build actions based on current phase (KFEN spec)
        if phase == constants.PHASE_MOVEMENT:
            # Movement phase: [(from,to),(from,to),...] from _moves_made
            moves = []
            for from_row, from_col, to_row, to_col in board._moves_made:
                from_coord = board.tuple_to_spreadsheet(from_row, from_col)
                to_coord = board.tuple_to_spreadsheet(to_row, to_col)
                moves.append((from_coord, to_coord))

            # Only generate list notation if there were actual moves
            # Otherwise use '[]' for no moves
            if moves:
                # Only include non-empty moves in FEN
                moves_with_coords = [(frm, to) for frm, to in moves if frm and to]
                actions_str = ('[' + ','.join([f"({frm},{to})" for frm, to in
                                             moves_with_coords]) + ']')
            else:
                actions_str = '[]'
        elif phase == constants.PHASE_BATTLE:
            # Battle phase: <target> or 'pass'
            attack_target = board.get_attack_target()
            if attack_target:
                target_coord = board.tuple_to_spreadsheet(attack_target[0], attack_target[1])
                actions_str = target_coord
            else:
                actions_str = 'pass'
        else:
            actions_str = '[]'

        # Build retreats list: [row1,col1,row2,col2,...]
        retreats = board.get_pending_retreats()
        retreat_list = []
        for row, col in retreats:
            retreat_list.extend([str(row), str(col)])
        retreats_str = f"[{','.join(retreat_list)}]"

        # Assemble FEN (0.2.1 format)
        fen = f"{board_data}/{turn_char}/{phase}/{actions_str}/{turn_number}/{retreats_str}"
        return fen

    @staticmethod
    def fen_to_board(fen_string: str) -> 'Board':
        """
        Convert FEN string to Board object (0.2.1 with terrain).

        Supports backward compatibility:
        - 0.1.4: 25 parts (no terrain)
        - 0.2.1: 25 parts (terrain with bracket notation)
        - Board-only: 20 parts (used in KFEN board_info section)

        Args:
            fen_string: FEN string

        Returns:
            Board object

        Example:
            "_________________________/.../N/M/[]/1/[]" -> Board
            "_____________________(I)______________/.../N/M/[]/1/[]" -> Board with terrain
            "_________________________/.../..." -> Board (20 parts, board data only)
        """
        if not isinstance(fen_string, str):
            raise TypeError(f"FEN must be string, got {type(fen_string)}")

        # Remove newlines to handle user formatting, but NOT other whitespace
        # (test_fen_whitespace_handling expects leading/trailing spaces to fail)
        fen_string = fen_string.replace('\n', '')

        # Also remove whitespace that appears after "/" characters
        # This handles KFEN files with formatted FEN strings (e.g., newlines + indentation)
        # Format like: "row1/\n        row2/" becomes "row1/row2/"
        import re
        fen_string = re.sub(r'/\s+', '/', fen_string)

        # Fail on leading/trailing whitespace (for test compatibility)
        if fen_string != fen_string.strip():
            raise ValueError("Invalid FEN: has leading/trailing whitespace")

        parts = fen_string.split('/')
        if len(parts) not in [20, 23, 25]:  # 20 parts (board-only), 23 (0.1.0), or 25 (0.1.4/0.2.1)
            raise ValueError(f"Invalid FEN: expected 20, 23, or 25 parts, got {len(parts)}")

        # Parse board data (first 20 parts) - handles terrain with bracket notation
        board_data = parts[:20]

        # Create board
        from .board import Board
        board = Board()

        # Set turn (only if turn state present)
        if len(parts) >= 23:
            turn_char = parts[20]
            if turn_char not in ['N', 'S']:
                raise ValueError(f"Invalid turn character: {turn_char}")
            board._turn = constants.PLAYER_NORTH if turn_char == 'N' else constants.PLAYER_SOUTH

        # Parse board rows with terrain support
        for row, row_data in enumerate(board_data):
            # Validate row length (for backward compatibility with old tests)
            # Note: With terrain bracket notation, rows can be longer than 25 chars
            # so we skip this validation when terrain symbols are present
            terrain_symbols = ['m', 'p', 'f', 'a', '(', '[']
            has_terrain = any(s in row_data for s in terrain_symbols)

            if not has_terrain and len(row_data) != 25:
                raise ValueError(f"Invalid FEN row {row}: expected 25 chars, got {len(row_data)}")

            col = 0
            i = 0
            while i < len(row_data):
                char = row_data[i]

                if char == '_':
                    # Empty flat square
                    board.clear_square(row, col)
                    board.set_terrain(row, col, None)
                    col += 1
                    i += 1
                elif char == 'm':
                    # Mountain (impassable)
                    board.clear_square(row, col)
                    board.set_terrain(row, col, 'MOUNTAIN')
                    col += 1
                    i += 1
                elif char == 'p':
                    # Empty mountain pass
                    board.clear_square(row, col)
                    board.set_terrain(row, col, 'MOUNTAIN_PASS')
                    col += 1
                    i += 1
                elif char == 'f':
                    # Empty fortress
                    board.clear_square(row, col)
                    board.set_terrain(row, col, 'FORTRESS')
                    col += 1
                    i += 1
                elif char == 'A' or char == 'a':
                    # Arsenal terrain: 'A' (North), 'a' (South), 'A{I}'
                    # (North with unit), 'a{i}' (South with unit)
                    arsenal_owner = 'NORTH' if char == 'A' else 'SOUTH'

                    # Check if this is an arsenal with a unit: 'A{I}' or 'a{i}'
                    if i + 3 < len(row_data) and row_data[i + 1] == '{' and row_data[i + 3] == '}':
                        # Arsenal with unit
                        unit_symbol = row_data[i + 2]
                        is_south = unit_symbol.islower()
                        unit_type = Fen.SYMBOL_TO_PIECE[unit_symbol.upper()]
                        unit_owner = constants.PLAYER_SOUTH if is_south else constants.PLAYER_NORTH

                        # Create unit and set terrain with owner
                        from .pieces import create_piece
                        piece = create_piece(unit_type, unit_owner)
                        board.place_unit(row, col, piece)
                        board.set_terrain(row, col, 'ARSENAL')
                        board.set_arsenal(row, col, arsenal_owner)

                        col += 1
                        i += 4
                    else:
                        # Empty arsenal terrain
                        board.clear_square(row, col)
                        board.set_terrain(row, col, 'ARSENAL')
                        board.set_arsenal(row, col, arsenal_owner)
                        col += 1
                        i += 1
                elif char == '(':
                    # Unit on mountain pass: (I) or (i)
                    if i + 2 >= len(row_data) or row_data[i + 2] != ')':
                        raise ValueError(f"Invalid pass notation at ({row}, {col})")

                    unit_symbol = row_data[i + 1]
                    is_south = unit_symbol.islower()
                    unit_type = Fen.SYMBOL_TO_PIECE[unit_symbol.upper()]
                    owner = constants.PLAYER_SOUTH if is_south else constants.PLAYER_NORTH

                    # Create unit and set terrain
                    from .pieces import create_piece
                    piece = create_piece(unit_type, owner)
                    board.place_unit(row, col, piece)
                    board.set_terrain(row, col, 'MOUNTAIN_PASS')

                    col += 1
                    i += 3
                elif char == '[':
                    # Unit in fortress: [I] or [i]
                    if i + 2 >= len(row_data) or row_data[i + 2] != ']':
                        raise ValueError(f"Invalid fortress notation at ({row}, {col})")

                    unit_symbol = row_data[i + 1]
                    is_south = unit_symbol.islower()
                    unit_type = Fen.SYMBOL_TO_PIECE[unit_symbol.upper()]
                    owner = constants.PLAYER_SOUTH if is_south else constants.PLAYER_NORTH

                    # Create unit and set terrain
                    from .pieces import create_piece
                    piece = create_piece(unit_type, owner)
                    board.place_unit(row, col, piece)
                    board.set_terrain(row, col, 'FORTRESS')

                    col += 1
                    i += 3
                else:
                    # Regular unit on flat terrain
                    # Check if symbol is valid (for backward compatibility)
                    if char.upper() not in Fen.SYMBOL_TO_PIECE:
                        raise ValueError(f"Invalid piece symbol: {char}")

                    is_south = char.islower()
                    unit_type = Fen.SYMBOL_TO_PIECE[char.upper()]
                    owner = constants.PLAYER_SOUTH if is_south else constants.PLAYER_NORTH

                    # Create unit
                    from .pieces import create_piece
                    piece = create_piece(unit_type, owner)
                    board.place_unit(row, col, piece)

                    col += 1
                    i += 1

        # Parse 0.1.4 turn state if present
        if len(parts) >= 23:
            phase = parts[21]
            actions = parts[22]  # Parse actions in 0.2.1
            turn_number = parts[23]
            retreats_str = parts[24]

            # Set phase
            if phase in [constants.PHASE_MOVEMENT, constants.PHASE_BATTLE]:
                board._current_phase = phase

            # Set turn number
            try:
                board._turn_number = int(turn_number)
            except ValueError as err:
                raise ValueError(f"Invalid turn number: {turn_number}") from err

            # Parse actions based on phase (KFEN spec 0.2.1)
            if phase == constants.PHASE_MOVEMENT:
                # Movement phase: [(from,to),(from,to),...] from _moves_made
                # Format: [(from,to),(from,to),(from,to),(from,to),(from,to)]
                if actions.startswith('[') and actions.endswith(']'):
                    actions_list_str = actions[1:-1]  # Remove brackets

                    # Parse move pairs by finding (from,to) patterns
                    # Format is like: (6F,7F),(7G,8G)
                    # We need to extract each (from,to) pair
                    i = 0
                    while i < len(actions_list_str):
                        # Find opening parenthesis
                        if actions_list_str[i] == '(':
                            # Find closing parenthesis for this pair
                            j = i + 1
                            while j < len(actions_list_str) and actions_list_str[j] != ')':
                                j += 1

                            if j >= len(actions_list_str):
                                raise ValueError(f"Invalid movement actions format: {actions}")

                            # Extract the move pair (without parentheses)
                            move_pair = actions_list_str[i+1:j]

                            # Split by comma
                            if ',' not in move_pair:
                                raise ValueError(f"Invalid move format: {move_pair}")

                            move_parts = move_pair.split(',')
                            if len(move_parts) != 2:
                                raise ValueError(f"Invalid move format: {move_pair}")

                            frm, to = move_parts

                            # Parse coordinates using spreadsheet_to_tuple which
                            # handles variable-length coordinates
                            from_row, from_col = board.spreadsheet_to_tuple(frm.strip())
                            to_row, to_col = board.spreadsheet_to_tuple(to.strip())

                            # Track move in _moved_units
                            board._moved_units.add((from_row, from_col))

                            # Also track by unit ID
                            unit = board.get_unit(to_row, to_col)
                            if unit:
                                unit_id = id(unit)
                                board._moved_unit_ids.add(unit_id)

                            # Track complete move in _moves_made
                            board._moves_made.append((from_row, from_col, to_row, to_col))

                            # Move past this pair and the comma after it
                            i = j + 1
                            # Skip comma if present
                            if i < len(actions_list_str) and actions_list_str[i] == ',':
                                i += 1
                        else:
                            # Skip non-parenthesis characters (commas between pairs)
                            i += 1
                else:
                    raise ValueError(f"Invalid movement actions format: {actions}")

            elif phase == constants.PHASE_BATTLE:
                # Battle phase: <target> or 'pass'
                if actions == 'pass':
                    # Pass recorded in FEN - track via attack state
                    board._attacks_this_turn = 1
                    board._attack_target = None  # Pass = no target
                else:
                    # Attack target coordinate
                    target_row, target_col = board.spreadsheet_to_tuple(actions)

                    # Track attack state
                    board._attacks_this_turn = 1
                    board._attack_target = (target_row, target_col)
            else:
                raise ValueError(f"Invalid phase: {phase}")

            # Parse retreats: [row1,col1,row2,col2,...]
            if retreats_str != '[]':
                retreats_str = retreats_str.strip('[]')
                if retreats_str:
                    retreat_parts = retreats_str.split(',')
                    if len(retreat_parts) % 2 != 0:
                        raise ValueError(f"Invalid retreats format: {retreats_str}")

                    for i in range(0, len(retreat_parts), 2):
                        try:
                            row = int(retreat_parts[i])
                            col = int(retreat_parts[i + 1])
                            board.add_pending_retreat(row, col)
                        except (ValueError, IndexError) as err:
                            raise ValueError(f"Invalid retreat position: {retreats_str}") from err

        # Network recalculation is now lazy - networks will be calculated on-demand
        # when needed via _ensure_network_calculated()

        return board
