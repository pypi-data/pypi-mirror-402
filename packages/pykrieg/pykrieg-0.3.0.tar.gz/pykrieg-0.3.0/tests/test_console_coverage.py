"""Additional tests to increase console module coverage to 70%+."""

from io import StringIO
from unittest.mock import MagicMock, patch

from pykrieg import Board
from pykrieg.console.display import BoardDisplay, DisplayMode
from pykrieg.console.game import ConsoleGame
from pykrieg.console.input_buffer import CommandBuffer, parse_multi_command_input
from pykrieg.console.mouse_handler import MouseHandler

# ============================================================================
# Input Buffer Coverage Tests
# ============================================================================

class TestCommandBufferCoverage:
    """Tests to increase input_buffer.py coverage."""

    def test_add_raw_input_single_command(self):
        """Test add_raw_input with single command."""
        buffer = CommandBuffer()

        result = buffer.add_raw_input("move 5,10 6,10")

        assert result == (False, None)
        assert buffer.get_count() == 1
        assert buffer.commands[0] == "move 5,10 6,10"

    def test_add_raw_input_multiple_commands(self):
        """Test add_raw_input with multiple commands separated by semicolons."""
        buffer = CommandBuffer()

        result = buffer.add_raw_input("move 5,10 6,10; attack 5,12; pass")

        assert result == (False, None)
        assert buffer.get_count() == 3

    def test_add_raw_input_empty(self):
        """Test add_raw_input with empty input."""
        buffer = CommandBuffer()

        result = buffer.add_raw_input("")

        assert result == (True, None)
        assert buffer.get_count() == 0

    def test_add_raw_input_invalid_commands_filtered(self):
        """Test add_raw_input filters invalid commands."""
        buffer = CommandBuffer()

        result = buffer.add_raw_input("invalidcmd; move 5,10 6,10; anotherbad")

        assert result == (False, None)
        # Only valid command should be added
        assert buffer.get_count() == 1
        assert "move 5,10 6,10" in buffer.commands[0]

    def test_parse_multi_command_input_with_newlines(self):
        """Test parse_multi_command_input with newlines."""
        input_str = "move 5,10 6,10\nmove 6,10 7,10\nattack 5,12"

        result = parse_multi_command_input(input_str)

        assert len(result) == 3
        assert "move 5,10 6,10" in result
        assert "move 6,10 7,10" in result
        assert "attack 5,12" in result

    def test_parse_multi_command_input_with_windows_newlines(self):
        """Test parse_multi_command_input with Windows newlines."""
        input_str = "move 5,10 6,10\r\nmove 6,10 7,10"

        result = parse_multi_command_input(input_str)

        assert len(result) == 2
        assert "move 5,10 6,10" in result
        assert "move 6,10 7,10" in result

    def test_parse_multi_command_input_empty(self):
        """Test parse_multi_command_input with empty string."""
        result = parse_multi_command_input("")

        assert result == []

    def test_command_buffer_display(self):
        """Test command buffer display generation."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")
        buffer.add_command("attack 5,12")

        display = buffer.get_display()

        assert "Buffer:" in display
        assert "1. move 5,10 6,10" in display
        assert "2. attack 5,12" in display
        assert "Press ENTER to execute" in display
        assert "BACKSPACE to remove" in display
        assert "ESC to clear" in display


# ============================================================================
# Mouse Handler Coverage Tests
# ============================================================================

class TestMouseHandlerCoverage:
    """Tests to increase mouse_handler.py coverage."""

    def test_mouse_handler_battle_phase_click(self):
        """Test mouse click during battle phase."""
        board = Board()
        board.switch_to_battle_phase()
        board.create_and_place_unit(5, 10, "CAVALRY", "NORTH")
        board.create_and_place_unit(5, 11, "RELAY", "SOUTH")
        display = BoardDisplay(DisplayMode.COMPATIBILITY)
        handler = MouseHandler(board, display)

        # During battle phase, clicking own unit may not select it
        # (depending on implementation - you can only attack, not move)
        result = handler.handle_mouse_click(5, 10)

        # Just verify it doesn't crash
        assert result is None

    def test_mouse_handler_click_own_unit_twice(self):
        """Test clicking own unit twice deselects it."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        display = BoardDisplay(DisplayMode.COMPATIBILITY)
        handler = MouseHandler(board, display)

        # First click selects
        handler.handle_mouse_click(5, 10)
        assert handler.selected_square == (5, 10)

        # Second click deselects
        result = handler.handle_mouse_click(5, 10)

        assert result is None
        assert handler.selected_square is None

    def test_mouse_handler_click_enemy_without_selection(self):
        """Test clicking enemy unit without selection does nothing."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(5, 11, "CAVALRY", "SOUTH")
        display = BoardDisplay(DisplayMode.COMPATIBILITY)
        handler = MouseHandler(board, display)

        # Click enemy unit without selection
        result = handler.handle_mouse_click(5, 11)

        assert result is None
        assert handler.selected_square is None

    def test_mouse_handler_out_of_bounds_click(self):
        """Test clicking outside board."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)
        handler = MouseHandler(board, display)

        # Click outside board
        result = handler.handle_mouse_click(25, 30)

        assert result is None


# ============================================================================
# Game Loop Coverage Tests
# ============================================================================

class TestGameLoopCoverage:
    """Tests to increase game.py coverage."""

    def test_display_welcome_and_render(self):
        """Test display welcome and render methods."""
        game = ConsoleGame(display_mode='compatibility')

        with patch('builtins.input', return_value=''):
            game._display_welcome()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            game._render()
            output = mock_stdout.getvalue()

            # Check output contains expected elements
            assert "PYKRIEG" in output
            assert "Turn:" in output
            assert "Current Player:" in output

    def test_prompt_for_command_invalid_input(self):
        """Test prompt for command with invalid input."""
        game = ConsoleGame(display_mode='compatibility')

        with patch('builtins.input', return_value='invalid_command'):
            game._prompt_for_command()

        # Should not crash, just show error

    def test_prompt_for_command_empty_input(self):
        """Test prompt for command with empty input."""
        game = ConsoleGame(display_mode='compatibility')

        with patch('builtins.input', return_value=''):
            game._prompt_for_command()

        # Should not crash

    def test_execute_command_invalid(self):
        """Test _execute_command with invalid command."""
        game = ConsoleGame(display_mode='compatibility')

        # This should not raise an exception
        game._execute_command(MagicMock(command_type=MagicMock(name="INVALID")))

    def test_execute_move_invalid_coordinates(self):
        """Test _execute_move with invalid coordinates."""
        game = ConsoleGame(display_mode='compatibility')
        from pykrieg.console.parser import Command, CommandType

        command = Command(CommandType.MOVE, {
            'from_row': 99,
            'from_col': 99,
            'to_row': 100,
            'to_col': 100,
        })

        with patch('builtins.input', return_value=''):
            game._execute_move(command)

        # Should show error message, not crash

    def test_execute_attack_invalid_coordinates(self):
        """Test _execute_attack with invalid coordinates."""
        game = ConsoleGame(display_mode='compatibility')
        game.board.switch_to_battle_phase()
        from pykrieg.console.parser import Command, CommandType

        command = Command(CommandType.ATTACK, {
            'target_row': 99,
            'target_col': 99,
        })

        with patch('builtins.input', return_value=''):
            game._execute_attack(command)

        # Should show error message, not crash


# ============================================================================
# Terminal Detection Coverage Tests
# ============================================================================

class TestTerminalDetectionCoverage:
    """Tests to increase terminal.py coverage."""

    def test_terminal_width_fallback(self):
        """Test terminal width returns reasonable fallback."""
        from pykrieg.console.terminal import get_terminal_width

        width = get_terminal_width()

        # Should be a reasonable value
        assert 40 <= width <= 200
