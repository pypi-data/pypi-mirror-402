"""Test suite for parser edge cases.

Tests parsing and validation with various edge conditions.
"""

from pykrieg import Board
from pykrieg.console.parser import (
    Command,
    CommandType,
    _parse_coordinates,
    parse_command,
    validate_command,
)

# ============================================================================
# Parser Edge Cases
# ============================================================================

class TestParserEdgeCases:
    """Test parser with edge cases and error conditions."""

    def test_parse_move_with_invalid_coords(self):
        """Test parsing move with invalid coordinates."""
        result = parse_command("move Z99 to AA100")

        assert result.command_type == CommandType.INVALID
        assert "error" in result.args

    def test_parse_attack_with_empty_coords(self):
        """Test parsing attack without coordinates."""
        result = parse_command("attack")

        assert result.command_type == CommandType.INVALID
        assert "error" in result.args

    def test_parse_save_with_spaces_in_filename(self):
        """Test parsing save with spaces in filename."""
        result = parse_command("save my_game.fen")

        # Should take filename as is
        assert result.command_type == CommandType.SAVE
        assert "game" in result.args['filename']

    def test_parse_mode_invalid_option(self):
        """Test parsing mode with invalid option."""
        result = parse_command("mode invalid")

        assert result.command_type == CommandType.INVALID
        assert "error" in result.args

    def test_parse_phase_invalid_option(self):
        """Test parsing phase with invalid option."""
        result = parse_command("phase invalid")

        assert result.command_type == CommandType.INVALID
        assert "error" in result.args

    def test_parse_coordinates_out_of_bounds(self):
        """Test parsing coordinates out of board bounds."""
        # Row out of bounds
        result = _parse_coordinates("25,10")
        assert result is None

        # Column out of bounds
        result = _parse_coordinates("10,30")
        assert result is None

    def test_parse_coordinates_negative(self):
        """Test parsing negative coordinates."""
        result = _parse_coordinates("-1,10")
        assert result is None

    def test_parse_coordinates_extra_spaces(self):
        """Test parsing coordinates with extra spaces."""
        result = _parse_coordinates(" 5 , 10 ")

        # Should handle extra spaces
        assert result == (5, 10)

    def test_parse_shorthand_coordinates_mixed_case(self):
        """Test shorthand coordinates with mixed case."""
        result = parse_command("1A 2B")

        # Should handle mixed case
        assert result.command_type == CommandType.MOVE
        assert result.args['from_row'] == 0
        assert result.args['from_col'] == 0
        assert result.args['to_row'] == 1
        assert result.args['to_col'] == 1

    def test_parse_save_default_filename(self):
        """Test parsing save without filename uses default."""
        result = parse_command("save")

        assert result.command_type == CommandType.SAVE
        # Should have default filename (now KFEN format)
        assert result.args['filename'] is not None
        assert ".kfen" in result.args['filename']

    def test_parse_load_default_filename(self):
        """Test parsing load without filename uses default."""
        result = parse_command("load")

        assert result.command_type == CommandType.LOAD
        # Should have default filename (now KFEN format)
        assert result.args['filename'] == "pykrieg_save.kfen"

    def test_parse_move_to_format(self):
        """Test parsing move with 'to' keyword."""
        result = parse_command("move 5,10 to 6,10")

        assert result.command_type == CommandType.MOVE
        assert result.args['from_row'] == 5
        assert result.args['from_col'] == 10
        assert result.args['to_row'] == 6
        assert result.args['to_col'] == 10

    def test_parse_move_without_to_keyword(self):
        """Test parsing move without 'to' keyword."""
        result = parse_command("move 5,10 6,10")

        assert result.command_type == CommandType.MOVE
        assert result.args['from_row'] == 5
        assert result.args['from_col'] == 10
        assert result.args['to_row'] == 6
        assert result.args['to_col'] == 10


# ============================================================================
# Validation Edge Cases
# ============================================================================

class TestValidationEdgeCases:
    """Test validation with edge cases."""

    def test_validate_attack_no_target_unit(self):
        """Test validating attack with no target unit."""
        board = Board()
        board.switch_to_battle_phase()

        command = Command(CommandType.ATTACK, {
            'target_row': 5,
            'target_col': 10,
        })

        is_valid, error = validate_command(board, command)

        assert is_valid is False
        assert "No unit" in error

    def test_validate_move_same_source_dest(self):
        """Test validating move with same source and destination."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        command = Command(CommandType.MOVE, {
            'from_row': 5,
            'from_col': 10,
            'to_row': 5,
            'to_col': 10,
        })

        is_valid, error = validate_command(board, command)

        # Move to same square should be invalid
        assert is_valid is False

    def test_validate_move_no_unit_at_source(self):
        """Test validating move with no unit at source."""
        board = Board()

        command = Command(CommandType.MOVE, {
            'from_row': 5,
            'from_col': 10,
            'to_row': 6,
            'to_col': 10,
        })

        is_valid, error = validate_command(board, command)

        # Should be invalid
        assert is_valid is False
        assert "Invalid move" in error

    def test_validate_phase_switch_to_movement(self):
        """Test validating switch to movement phase."""
        board = Board()
        board.switch_to_battle_phase()

        command = Command(CommandType.PHASE, {'phase': 'movement'})

        is_valid, error = validate_command(board, command)

        # Should require attack or pass first
        assert is_valid is False
        assert "attack or pass" in error.lower()

    def test_validate_phase_switch_to_battle(self):
        """Test validating switch to battle phase."""
        board = Board()

        command = Command(CommandType.PHASE, {'phase': 'battle'})

        is_valid, error = validate_command(board, command)

        # Should allow switching to battle
        assert is_valid is True
        assert error is None

    def test_validate_end_turn_without_action(self):
        """Test validating end turn without action in battle."""
        board = Board()
        board.switch_to_battle_phase()

        command = Command(CommandType.END_TURN)

        is_valid, error = validate_command(board, command)

        # Should require action
        assert is_valid is False
        assert "attack or pass" in error.lower()

    def test_validate_pass_in_movement_phase(self):
        """Test validating pass in movement phase."""
        board = Board()

        command = Command(CommandType.PASS)

        is_valid, error = validate_command(board, command)

        # Can only pass in battle phase
        assert is_valid is False
        assert "battle phase" in error

    def test_validate_attack_own_unit(self):
        """Test validating attack on own unit."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.switch_to_battle_phase()

        command = Command(CommandType.ATTACK, {
            'target_row': 5,
            'target_col': 10,
        })

        is_valid, error = validate_command(board, command)

        # Can't attack own units
        assert is_valid is False
        assert "your own" in error.lower() or "own units" in error.lower()

    def test_validate_pass_already_attacked(self):
        """Test validating pass after already attacking."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 10, "CAVALRY", "SOUTH")
        board.switch_to_battle_phase()

        # Simulate attack by setting attacks made
        board._attacks_this_turn = 1

        command = Command(CommandType.PASS)

        is_valid, error = validate_command(board, command)

        # Can't pass after attacking
        assert is_valid is False
        assert "Already attacked" in error or "already attacked" in error


# ============================================================================
# Coordinate Parsing Edge Cases
# ============================================================================

class TestCoordinateParsing:
    """Test coordinate parsing with edge cases."""

    def test_parse_spreadsheet_single_digit(self):
        """Test parsing single-digit spreadsheet coordinates."""
        result = _parse_coordinates("1A")

        assert result == (0, 0)

    def test_parse_spreadsheet_valid_range(self):
        """Test parsing valid spreadsheet coordinates at edge."""
        result = _parse_coordinates("25S")

        # Column Y (index 24), Row 19 (0-indexed as 18)
        assert result == (18, 24)

    def test_parse_spreadsheet_mixed_case(self):
        """Test parsing spreadsheet with mixed case."""
        result_upper = _parse_coordinates("1A")
        result_lower = _parse_coordinates("1a")

        # Should be case-insensitive
        assert result_upper == result_lower
        assert result_upper == (0, 0)

    def test_parse_numeric_comma(self):
        """Test parsing numeric coordinates with comma."""
        result = _parse_coordinates("5,10")

        assert result == (5, 10)

    def test_parse_numeric_space(self):
        """Test parsing numeric coordinates with space."""
        result = _parse_coordinates("5 10")

        assert result == (5, 10)

    def test_parse_numeric_multiple_spaces(self):
        """Test parsing numeric with multiple spaces."""
        result = _parse_coordinates("5  10")

        assert result == (5, 10)

    def test_parse_invalid_spreadsheet(self):
        """Test parsing invalid spreadsheet coordinates."""
        result = _parse_coordinates("26CU")

        assert result is None

    def test_parse_invalid_numeric(self):
        """Test parsing invalid numeric coordinates."""
        result = _parse_coordinates("abc,def")

        assert result is None

    def test_parse_empty_coordinates(self):
        """Test parsing empty coordinates."""
        result = _parse_coordinates("")

        assert result is None


# ============================================================================
# Undo/Redo Command Tests
# ============================================================================

class TestUndoRedoCommands:
    """Test undo/redo command parsing."""

    def test_parse_undo_command(self):
        """Test parsing undo command."""
        command = parse_command("undo")
        assert command.command_type.name == "UNDO"
        assert command.args.get('count') == 1

    def test_parse_undo_command_abbreviated(self):
        """Test parsing abbreviated undo command."""
        command = parse_command("u")
        assert command.command_type.name == "UNDO"
        assert command.args.get('count') == 1

    def test_parse_undo_with_count(self):
        """Test parsing undo command with count."""
        command = parse_command("undo 5")
        assert command.command_type.name == "UNDO"
        assert command.args.get('count') == 5

    def test_parse_undo_invalid_count_negative(self):
        """Test parsing undo with negative count."""
        command = parse_command("undo -1")
        assert command.command_type.name == "INVALID"
        assert "at least 1" in command.args.get('error', '')

    def test_parse_undo_invalid_count_zero(self):
        """Test parsing undo with zero count."""
        command = parse_command("undo 0")
        assert command.command_type.name == "INVALID"
        assert "at least 1" in command.args.get('error', '')

    def test_parse_undo_invalid_count_text(self):
        """Test parsing undo with text instead of number."""
        command = parse_command("undo abc")
        assert command.command_type.name == "INVALID"
        assert "number" in command.args.get('error', '')

    def test_parse_redo_command(self):
        """Test parsing redo command."""
        command = parse_command("redo")
        assert command.command_type.name == "REDO"
        assert command.args.get('count') == 1

    def test_parse_redo_command_abbreviated(self):
        """Test parsing abbreviated redo command."""
        command = parse_command("r")
        assert command.command_type.name == "REDO"
        assert command.args.get('count') == 1

    def test_parse_redo_with_count(self):
        """Test parsing redo command with count."""
        command = parse_command("redo 3")
        assert command.command_type.name == "REDO"
        assert command.args.get('count') == 3

    def test_parse_redo_invalid_count_negative(self):
        """Test parsing redo with negative count."""
        command = parse_command("redo -5")
        assert command.command_type.name == "INVALID"
        assert "at least 1" in command.args.get('error', '')

    def test_parse_redo_invalid_count_zero(self):
        """Test parsing redo with zero count."""
        command = parse_command("redo 0")
        assert command.command_type.name == "INVALID"
        assert "at least 1" in command.args.get('error', '')

    def test_parse_set_undo_limit_command(self):
        """Test parsing set_undo_limit command."""
        command = parse_command("set_undo_limit 100")
        assert command.command_type.name == "SET_UNDO_LIMIT"
        assert command.args.get('limit') == 100

    def test_parse_set_undo_limit_zero(self):
        """Test parsing set_undo_limit with 0 (unlimited)."""
        command = parse_command("set_undo_limit 0")
        assert command.command_type.name == "SET_UNDO_LIMIT"
        assert command.args.get('limit') == 0

    def test_parse_set_undo_limit_negative(self):
        """Test parsing set_undo_limit with negative value."""
        command = parse_command("set_undo_limit -10")
        assert command.command_type.name == "INVALID"
        assert "0 or greater" in command.args.get('error', '')

    def test_parse_set_undo_limit_no_value(self):
        """Test parsing set_undo_limit without value."""
        command = parse_command("set_undo_limit")
        assert command.command_type.name == "INVALID"
        assert "requires a number" in command.args.get('error', '')

    def test_parse_set_undo_limit_invalid_value(self):
        """Test parsing set_undo_limit with text value."""
        command = parse_command("set_undo_limit abc")
        assert command.command_type.name == "INVALID"
        assert "number" in command.args.get('error', '')
