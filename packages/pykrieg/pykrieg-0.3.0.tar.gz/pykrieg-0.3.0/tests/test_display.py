"""Test suite for display coordinate mapping.

Tests screen-to-board coordinate conversion, highlights, and rendering.
"""

from pykrieg import Board
from pykrieg.console.display import BoardDisplay, DisplayMode

# ============================================================================
# Display Coordinate Mapping Tests
# ============================================================================

class TestDisplayCoordinateMapping:
    """Test screen-to-board coordinate mapping."""

    def test_calculate_cell_positions_all_cells(self):
        """Test that all board cells have calculated positions."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display._calculate_cell_positions(board)

        cell_positions = display.render_state['cell_positions']

        # Should have positions for all cells
        assert len(cell_positions) == board.rows * board.cols  # 20 * 25 = 500

        # Check a few specific positions
        assert (0, 0) in cell_positions  # Top-left
        assert (19, 24) in cell_positions  # Bottom-right
        assert (10, 12) in cell_positions  # Center

    def test_screen_to_board_valid_clicks(self):
        """Test converting valid screen clicks to board coordinates."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display._calculate_cell_positions(board)

        # Test clicking on known cells
        # Cell (0, 0) should be at screen position (3, 1)
        # Row header width = 3, header height = 1
        # cell (0, 0) is at x=3, y=1
        cell_positions = display.render_state['cell_positions']
        screen_x, screen_y = cell_positions.get((0, 0), (3, 1))

        result = display.screen_to_board(screen_x, screen_y)

        assert result == (0, 0)

    def test_screen_to_board_invalid_clicks(self):
        """Test converting invalid screen clicks returns None."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display._calculate_cell_positions(board)

        # Click outside board area
        result = display.screen_to_board(0, 0)

        # Should return None (this is in header area)
        assert result is None or result != (0, 0)

        # Click far outside
        result = display.screen_to_board(999, 999)

        assert result is None

    def test_screen_to_board_edge_cases(self):
        """Test screen-to-board conversion at edges."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display._calculate_cell_positions(board)

        cell_positions = display.render_state['cell_positions']

        # Test each corner
        corners = [
            (0, 0),    # Top-left
            (0, 24),   # Top-right
            (19, 0),   # Bottom-left
            (19, 24),   # Bottom-right
        ]

        for row, col in corners:
            screen_x, screen_y = cell_positions.get((row, col))
            result = display.screen_to_board(screen_x, screen_y)

            assert result == (row, col)

    def test_calculate_cell_positions_consistency(self):
        """Test that cell positions are consistent."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display._calculate_cell_positions(board)

        cell_positions = display.render_state['cell_positions']

        # Check that positions increase correctly
        # Row 0 should be at y=1 (after header)
        row0_x = cell_positions[(0, 0)][0]
        row0_y = cell_positions[(0, 0)][1]

        row1_x = cell_positions[(1, 0)][0]
        row1_y = cell_positions[(1, 0)][1]

        # Y should increase by 1 for each row
        assert row1_y == row0_y + 1

        # X should be same for same column
        assert row1_x == row0_x

    def test_get_column_headers_text(self):
        """Test column headers generation."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)
        headers = display._get_column_headers_text()

        # Should have "  " prefix (2 spaces for row letter)
        assert headers.startswith("  ")

        # Should have all 25 columns (numbers 1-25)
        assert "1" in headers
        assert "25" in headers

        # Should have 2 spaces at both ends for row letters
        assert headers.endswith("  ")

    def test_get_unit_char_all_types(self):
        """Test unit character generation for all unit types."""
        board = Board()

        # Test curses mode (Unicode)
        display_curses = BoardDisplay(DisplayMode.CURSES)

        # Test compatibility mode (ASCII)
        display_compat = BoardDisplay(DisplayMode.COMPATIBILITY)

        unit_types = [
            "INFANTRY",
            "CAVALRY",
            "CANNON",
            "RELAY",
            "SWIFT_CANNON",
            "SWIFT_RELAY",
        ]

        for unit_type in unit_types:
            board.create_and_place_unit(5, 10, unit_type, "NORTH")
            unit = board.get_unit(5, 10)

            # Curses mode should return Unicode
            char_curses = display_curses._get_unit_char(unit)
            assert len(char_curses) >= 1
            assert char_curses != ""

            # Compatibility mode should return ASCII
            char_compat = display_compat._get_unit_char(unit)
            assert char_compat.isupper()  # North is uppercase
            assert char_compat in ['I', 'C', 'K', 'R', 'W', 'X']

            board.clear_square(5, 10)

    def test_get_unit_char_south_lowercase(self):
        """Test South units are lowercase in compatibility mode."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        board.create_and_place_unit(5, 10, "INFANTRY", "SOUTH")
        unit = board.get_unit(5, 10)

        char = display._get_unit_char(unit)

        # South should be lowercase in compat mode
        assert char.islower()
        assert char == 'i'

    def test_get_unit_char_north_uppercase(self):
        """Test North units are uppercase in compatibility mode."""
        board = Board()
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        board.create_and_place_unit(5, 10, "INFANTRY", "NORTH")
        unit = board.get_unit(5, 10)

        char = display._get_unit_char(unit)

        # North should be uppercase in compat mode
        assert char.isupper()
        assert char == 'I'


# ============================================================================
# Highlight Tests
# ============================================================================

class TestDisplayHighlights:
    """Test cell highlighting functionality."""

    def test_set_highlight(self):
        """Test setting cell highlight."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display.set_highlight(5, 10, 'selected')

        highlights = display.render_state['highlights']

        assert (5, 10) in highlights
        assert highlights[(5, 10)] == 'selected'

    def test_set_highlight_multiple(self):
        """Test setting multiple highlights."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display.set_highlight(5, 10, 'selected')
        display.set_highlight(6, 10, 'destination')
        display.set_highlight(7, 10, 'attack')

        highlights = display.render_state['highlights']

        assert len(highlights) == 3
        assert highlights[(5, 10)] == 'selected'
        assert highlights[(6, 10)] == 'destination'
        assert highlights[(7, 10)] == 'attack'

    def test_clear_highlights(self):
        """Test clearing all highlights."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display.set_highlight(5, 10, 'selected')
        display.set_highlight(6, 10, 'destination')

        assert len(display.render_state['highlights']) == 2

        display.clear_highlights()

        highlights = display.render_state['highlights']

        assert len(highlights) == 0

    def test_overwrite_highlight(self):
        """Test overwriting existing highlight."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        display.set_highlight(5, 10, 'selected')
        display.set_highlight(5, 10, 'attack')

        highlights = display.render_state['highlights']

        assert len(highlights) == 1
        assert highlights[(5, 10)] == 'attack'

    def test_highlight_types(self):
        """Test all highlight types."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        highlight_types = ['selected', 'destination', 'attack']

        # Test each highlight type individually (not all at once)
        for htype in highlight_types:
            display.set_highlight(5, 10, htype)
            highlights = display.render_state['highlights']
            assert highlights[(5, 10)] == htype
            display.clear_highlights()


# ============================================================================
# Display State Tests
# ============================================================================

class TestDisplayState:
    """Test display state management."""

    def test_render_state_initialization(self):
        """Test render state initialization."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        state = display.render_state

        assert 'header_height' in state
        assert 'row_header_width' in state
        assert 'cell_width' in state
        assert 'cell_positions' in state
        assert 'highlights' in state

    def test_render_state_defaults(self):
        """Test render state default values."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        state = display.render_state

        assert state['header_height'] >= 0
        assert state['row_header_width'] >= 0
        assert state['cell_width'] >= 0
        assert isinstance(state['cell_positions'], dict)
        assert isinstance(state['highlights'], dict)

    def test_render_state_cell_positions_empty(self):
        """Test cell positions are empty before calculation."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        state = display.render_state

        # Should be empty before calling _calculate_cell_positions
        assert len(state['cell_positions']) == 0

    def test_render_state_highlights_empty(self):
        """Test highlights are empty initially."""
        display = BoardDisplay(DisplayMode.COMPATIBILITY)

        state = display.render_state

        # Should be empty
        assert len(state['highlights']) == 0
