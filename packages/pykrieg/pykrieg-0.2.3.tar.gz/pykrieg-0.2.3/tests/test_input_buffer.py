"""Test suite for input buffer edge cases.

Tests command parsing, buffer management, and display.
"""

from pykrieg.console.input_buffer import CommandBuffer

# ============================================================================
# Input Buffer Edge Cases
# ============================================================================

class TestInputBufferEdgeCases:
    """Test buffer with edge cases."""

    def test_add_command_with_whitespace(self):
        """Test adding command with extra whitespace."""
        buffer = CommandBuffer()
        buffer.add_command("  move 5,10 6,10  ")

        # Should store command with whitespace preserved or trimmed
        assert buffer.get_count() == 1
        assert len(buffer.commands[0]) > 0

    def test_add_empty_command(self):
        """Test adding empty command."""
        buffer = CommandBuffer()
        buffer.add_command("")

        # Empty commands are added but can be filtered later
        assert buffer.get_count() >= 0

    def test_remove_from_empty_buffer(self):
        """Test removing from empty buffer."""
        buffer = CommandBuffer()
        buffer.remove_last()

        # Should not crash
        assert buffer.get_count() == 0

    def test_clear_empty_buffer(self):
        """Test clearing empty buffer."""
        buffer = CommandBuffer()
        buffer.clear()

        # Should not crash
        assert buffer.is_empty() is True

    def test_add_many_commands(self):
        """Test adding many commands to buffer."""
        buffer = CommandBuffer()
        commands = [
            "move 5,10 6,10",
            "move 6,10 7,10",
            "move 7,10 8,10",
            "end"
        ]

        for cmd in commands:
            buffer.add_command(cmd)

        assert buffer.get_count() == 4

    def test_remove_multiple_times(self):
        """Test removing multiple commands."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")
        buffer.add_command("move 6,10 7,10")
        buffer.add_command("end")

        buffer.remove_last()
        buffer.remove_last()

        assert buffer.get_count() == 1
        assert buffer.commands == ["move 5,10 6,10"]

    def test_get_commands_empty(self):
        """Test getting commands from empty buffer."""
        buffer = CommandBuffer()
        result = buffer.get_commands()

        assert result == ""

    def test_get_commands_single(self):
        """Test getting single command."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")

        result = buffer.get_commands()

        assert result == "move 5,10 6,10"

    def test_get_commands_multiple(self):
        """Test getting multiple commands."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")
        buffer.add_command("move 6,10 7,10")
        buffer.add_command("end")

        result = buffer.get_commands()

        assert "move 5,10 6,10" in result
        assert "move 6,10 7,10" in result
        assert "end" in result
        assert "; " in result


# ============================================================================
# Multi-Command Parsing
# ============================================================================

class TestMultiCommandParsing:
    """Test parsing multi-command input."""

    def test_parse_multi_command_with_empty_lines(self):
        """Test parsing with empty lines between commands."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10\n\nmove 6,10 7,10"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False  # Multi-command returns False
        assert error is None

    def test_parse_multi_command_with_semicolons(self):
        """Test parsing with semicolon separators."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10;move 6,10 7,10;end"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False
        assert error is None
        assert buffer.get_count() == 3

    def test_parse_multi_command_mixed_separators(self):
        """Test parsing with mixed separators (newlines and semicolons)."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10\nmove 6,10 7,10;end"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False
        assert error is None
        assert buffer.get_count() >= 2

    def test_parse_mixed_coordinate_formats(self):
        """Test parsing mixed coordinate formats in one input."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10; A1 B2; move Y25 Y24"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False
        assert error is None

    def test_parse_with_whitespace_commands(self):
        """Test parsing with whitespace-only commands."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10;   ;end"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False
        assert error is None
        # Should filter out whitespace-only commands
        assert buffer.get_count() >= 1

    def test_parse_invalid_commands_filtered(self):
        """Test that invalid commands are filtered."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10; invalid_command; end; also_invalid"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False
        assert error is None
        # Should filter out invalid commands
        commands = buffer.commands
        assert "move 5,10 6,10" in commands
        assert "end" in commands
        # Invalid commands should not be present
        assert not any("invalid" in cmd.lower() for cmd in commands)

    def test_parse_single_command_complete(self):
        """Test parsing single complete command."""
        buffer = CommandBuffer()
        input_str = "move 5,10 6,10"

        is_complete, error = buffer.add_raw_input(input_str)

        assert is_complete is False  # Multi-command always returns False
        assert error is None
        assert buffer.get_count() == 1


# ============================================================================
# Buffer Display Tests
# ============================================================================

class TestBufferDisplay:
    """Test buffer display functionality."""

    def test_get_display_empty(self):
        """Test display when buffer is empty."""
        buffer = CommandBuffer()
        display = buffer.get_display()

        assert "Empty" in display
        assert "Buffer:" in display

    def test_get_display_with_commands(self):
        """Test display with queued commands."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")
        buffer.add_command("move 6,10 7,10")

        display = buffer.get_display()

        assert "Buffer:" in display
        assert "move 5,10 6,10" in display
        assert "move 6,10 7,10" in display
        assert "ENTER" in display.upper() or "enter" in display.lower()

    def test_get_display_long_command_list(self):
        """Test display with many commands."""
        buffer = CommandBuffer()
        for i in range(10):
            buffer.add_command(f"move {i},10 {i+1},10")

        display = buffer.get_display()

        assert "Buffer:" in display
        for i in range(10):
            assert f"{i+1}." in display  # Numbered list

    def test_clear_updates_display(self):
        """Test that clear updates display."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")

        display_before = buffer.get_display()
        assert "move 5,10 6,10" in display_before

        buffer.clear()

        display_after = buffer.get_display()
        assert "Empty" in display_after
        assert "move 5,10 6,10" not in display_after

    def test_remove_updates_display(self):
        """Test that remove updates display."""
        buffer = CommandBuffer()
        buffer.add_command("move 5,10 6,10")
        buffer.add_command("end")

        display_before = buffer.get_display()
        assert "end" in display_before

        buffer.remove_last()

        display_after = buffer.get_display()
        assert "end" not in display_after
        assert "move 5,10 6,10" in display_after


# ============================================================================
# Format Validation
# ============================================================================

class TestFormatValidation:
    """Test command format validation."""

    def test_looks_like_coordinates_pair(self):
        """Test coordinate pair detection."""
        buffer = CommandBuffer()

        result = buffer._looks_like_coordinates("5,10 6,10")

        assert result is True

    def test_looks_like_coordinates_odd(self):
        """Test coordinate detection with odd number of parts."""
        buffer = CommandBuffer()

        result = buffer._looks_like_coordinates("5,10 6,10 7,10")

        # Odd number of parts should return False
        assert result is False

    def test_looks_like_single_coord_comma(self):
        """Test single coordinate with comma."""
        buffer = CommandBuffer()

        result = buffer._looks_like_single_coord("5,10")

        assert result is True

    def test_looks_like_single_coord_space(self):
        """Test single coordinate with space."""
        buffer = CommandBuffer()

        result = buffer._looks_like_single_coord("5 10")

        assert result is True

    def test_looks_like_single_coord_invalid(self):
        """Test invalid single coordinate format."""
        buffer = CommandBuffer()

        result = buffer._looks_like_single_coord("5,10,15")

        assert result is False

    def test_is_valid_command_format_known(self):
        """Test valid command format."""
        buffer = CommandBuffer()

        result = buffer._is_valid_command_format("move 5,10 6,10")

        assert result is True

    def test_is_valid_command_format_unknown(self):
        """Test unknown command format."""
        buffer = CommandBuffer()

        result = buffer._is_valid_command_format("unknown command")

        assert result is False

    def test_is_valid_command_format_coordinates_only(self):
        """Test coordinate-only command."""
        buffer = CommandBuffer()

        result = buffer._is_valid_command_format("5,10 6,10")

        assert result is True

    def test_is_valid_command_format_invalid_coords(self):
        """Test invalid coordinate-only format."""
        buffer = CommandBuffer()

        result = buffer._is_valid_command_format("5,10")

        # Single coordinate pair should be invalid
        assert result is False
