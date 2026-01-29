"""Test suite for mouse handler functionality.

Tests mouse click handling, selection state, and status display.
"""

from pykrieg import Board
from pykrieg.console.mouse_handler import MouseHandler

# ============================================================================
# Mouse Handler Initialization Tests
# ============================================================================

class TestMouseHandlerInitialization:
    """Test mouse handler initialization."""

    def test_mouse_handler_init(self):
        """Test mouse handler initialization."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        assert handler.board is board
        assert handler.selected_square is None
        assert handler.command_queue == []
        assert isinstance(handler.mouse_available, bool)


# ============================================================================
# Mouse Click - Movement Phase Tests
# ============================================================================

class TestMouseClickMovementPhase:
    """Test mouse clicks during movement phase."""

    def test_click_empty_square_no_selection(self):
        """Test clicking empty square with no selection."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(5, 10)

        assert result is None
        assert handler.selected_square is None

    def test_click_own_unit_first_click(self):
        """Test first click on own unit selects it."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(5, 10)

        assert result is None
        assert handler.selected_square == (5, 10)

    def test_click_own_unit_second_click_same(self):
        """Test clicking same unit again deselects it."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        # First click
        handler.handle_mouse_click(5, 10)
        assert handler.selected_square == (5, 10)

        # Second click on same unit
        result = handler.handle_mouse_click(5, 10)

        assert result is None
        assert handler.selected_square is None

    def test_click_different_unit_replaces_selection(self):
        """Test clicking different unit replaces selection."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 10, "CAVALRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        # First click
        handler.handle_mouse_click(5, 10)
        assert handler.selected_square == (5, 10)

        # Click different unit
        result = handler.handle_mouse_click(6, 10)

        assert result is None
        assert handler.selected_square == (6, 10)

    def test_click_empty_square_with_selection(self):
        """Test clicking empty square with unit selected."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        # Select unit
        handler.handle_mouse_click(5, 10)
        assert handler.selected_square == (5, 10)

        # Click empty destination
        result = handler.handle_mouse_click(6, 10)

        # Should return spreadsheet format (e.g., "K6 K7")
        assert result is not None
        assert " " in result  # Should have space between coords
        assert handler.selected_square is None

    def test_click_opponent_unit_ignored(self):
        """Test clicking opponent's unit is ignored in movement phase."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 10, "CAVALRY", "SOUTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(6, 10)

        assert result is None
        assert handler.selected_square is None


# ============================================================================
# Mouse Click - Battle Phase Tests
# ============================================================================

class TestMouseClickBattlePhase:
    """Test mouse clicks during battle phase."""

    def test_click_enemy_in_battle_phase(self):
        """Test clicking enemy unit queues attack."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.create_and_place_unit(6, 10, "CAVALRY", "SOUTH")
        board.switch_to_battle_phase()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(6, 10)

        assert result is not None
        assert "attack" in result.lower()
        assert handler.selected_square is None

    def test_click_empty_square_battle_phase(self):
        """Test clicking empty square in battle phase is ignored."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.switch_to_battle_phase()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(6, 10)

        assert result is None

    def test_click_own_unit_in_battle_phase_ignored(self):
        """Test clicking own unit in battle phase is ignored."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        board.switch_to_battle_phase()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(5, 10)

        assert result is None


# ============================================================================
# Invalid Coordinates Tests
# ============================================================================

class TestMouseHandlerInvalidCoordinates:
    """Test mouse handler with invalid coordinates."""

    def test_click_out_of_bounds_row(self):
        """Test clicking out of bounds row."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(20, 10)  # Row 20 is invalid

        assert result is None

    def test_click_out_of_bounds_col(self):
        """Test clicking out of bounds column."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(10, 25)  # Col 25 is invalid

        assert result is None

    def test_click_negative_coordinates(self):
        """Test clicking negative coordinates."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())

        result = handler.handle_mouse_click(-1, 10)

        assert result is None


# ============================================================================
# Status Display Tests
# ============================================================================

class TestMouseHandlerStatus:
    """Test mouse handler status and buffer displays."""

    def test_get_status_display_no_mouse(self):
        """Test status display when mouse unavailable."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        # Directly set mouse_available to False to simulate no mouse support
        handler.mouse_available = False
        status = handler.get_status_display()

        assert "DISABLED" in status
        assert "keyboard" in status.lower()

    def test_get_status_display_with_selection(self):
        """Test status display with unit selected."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        handler.handle_mouse_click(5, 10)

        status = handler.get_status_display()

        # Should show either ACTIVE or DISABLED depending on mouse support
        assert "ACTIVE" in status or "DISABLED" in status

        # Only check for selection info if mouse is active
        if "ACTIVE" in status:
            assert "Selected:" in status
            assert "11F" in status  # Row 5, Col 10 = K6

    def test_get_status_display_no_selection(self):
        """Test status display without selection."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        status = handler.get_status_display()

        # Should show either ACTIVE or DISABLED depending on mouse support
        assert "ACTIVE" in status or "DISABLED" in status


# ============================================================================
# Selection Management Tests
# ============================================================================

class TestMouseHandlerSelection:
    """Test selection state management."""

    def test_clear_selection(self):
        """Test clearing current selection."""
        board = Board()
        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        handler.handle_mouse_click(5, 10)
        assert handler.selected_square is not None

        handler.clear_selection()

        assert handler.selected_square is None

    def test_get_buffer_display_empty(self):
        """Test buffer display when empty."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        display = handler.get_buffer_display()

        assert "None" in display
        assert "Queued Commands:" in display

    def test_get_buffer_display_with_commands(self):
        """Test buffer display with queued commands."""
        board = Board()

        class MockDisplay:
            """Mock display for testing."""
            pass

        handler = MouseHandler(board, MockDisplay())
        handler.command_queue = ["move K6 K7", "move K7 K8"]
        handler.selected_square = (6, 10)

        display = handler.get_buffer_display()

        assert "move K6 K7" in display
        assert "move K7 K8" in display
        assert "6,10" in display or "11G" in display  # Either format
