"""Tests for terrain display rendering."""


from pykrieg.board import Board
from pykrieg.console.display import BoardDisplay, DisplayMode
from pykrieg.constants import PLAYER_NORTH, PLAYER_SOUTH


class TestTerrainGlyphsCurses:
    """Test terrain glyph generation for curses mode."""

    def test_get_terrain_glyph_curses_mountain(self):
        """Mountain glyph in curses mode."""
        display = BoardDisplay(mode=DisplayMode.CURSES)
        assert display._get_terrain_glyph_curses("MOUNTAIN") == "⛰"

    def test_get_terrain_glyph_curses_pass(self):
        """Mountain pass glyph in curses mode."""
        display = BoardDisplay(mode=DisplayMode.CURSES)
        assert display._get_terrain_glyph_curses("MOUNTAIN_PASS") == "⛞"

    def test_get_terrain_glyph_curses_fortress(self):
        """Fortress glyph in curses mode."""
        display = BoardDisplay(mode=DisplayMode.CURSES)
        assert display._get_terrain_glyph_curses("FORTRESS") == "⚜"

    def test_get_terrain_glyph_curses_empty(self):
        """Empty square glyph in curses mode."""
        display = BoardDisplay(mode=DisplayMode.CURSES)
        assert display._get_terrain_glyph_curses(None) == "·"


class TestTerrainGlyphsCompat:
    """Test terrain glyph generation for compatibility mode."""

    def test_get_terrain_glyph_compat_mountain(self):
        """Mountain glyph in compatibility mode."""
        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        assert display._get_terrain_glyph_compat("MOUNTAIN") == "M"

    def test_get_terrain_glyph_compat_pass(self):
        """Mountain pass glyph in compatibility mode."""
        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        assert display._get_terrain_glyph_compat("MOUNTAIN_PASS") == "P"

    def test_get_terrain_glyph_compat_fortress(self):
        """Fortress glyph in compatibility mode."""
        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        assert display._get_terrain_glyph_compat("FORTRESS") == "F"

    def test_get_terrain_glyph_compat_empty(self):
        """Empty square glyph in compatibility mode."""
        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        assert display._get_terrain_glyph_compat(None) == "_"


class TestTerrainColors:
    """Test terrain color scheme."""

    def test_fortress_color_in_loc(self):
        """Fortress in LOC gets dark green color."""
        board = Board()
        # Create arsenal to establish network
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.CURSES)
        board.set_terrain(10, 10, "FORTRESS")

        # Enable networks to calculate ray coverage
        board.enable_networks()

        # Fortress with unit in LOC should be dark green
        color = display._get_terrain_color(board, 10, 10, "FORTRESS")
        assert color == display.COLOR_TERRAIN_DARK

    def test_fortress_color_outside_loc(self):
        """Fortress outside LOC gets gray color."""
        board = Board()

        display = BoardDisplay(mode=DisplayMode.CURSES)
        board.set_terrain(10, 10, "FORTRESS")

        # Enable networks to calculate ray coverage
        board.enable_networks()

        # Empty fortress with no network coverage will be gray
        color = display._get_terrain_color(board, 10, 10, "FORTRESS")
        assert color == display.COLOR_GRAY

    def test_mountain_uses_terrain_colors(self):
        """Mountains always use gray color (0.2.1 update)."""
        board = Board()
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.CURSES)
        board.set_terrain(10, 10, "MOUNTAIN")

        # Mountains always use gray color (0.2.1)
        color = display._get_terrain_color(board, 10, 10, "MOUNTAIN")
        assert color == display.COLOR_GRAY

    def test_pass_uses_terrain_colors(self):
        """Passes use gray (offline) or dark green (if LOC passes through) (0.2.1 update)."""
        board = Board()
        # Create arsenal to establish network
        board.set_arsenal(10, 12, PLAYER_NORTH)
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.CURSES)
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        # Enable networks to calculate ray coverage
        board.enable_networks()

        # Passes use gray (offline) or dark green (if LOC passes through)
        color = display._get_terrain_color(board, 10, 10, "MOUNTAIN_PASS")
        assert color in (display.COLOR_TERRAIN_DARK, display.COLOR_GRAY)


class TestCompatibilityRendering:
    """Test compatibility mode rendering with terrain."""

    def test_render_cell_compat_mountain(self):
        """Render mountain cell in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "MOUNTAIN")

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "M"  # Mountain without trailing space

    def test_render_cell_compat_pass_empty(self):
        """Render empty pass in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "MOUNTAIN_PASS")

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "P"  # Pass without trailing space

    def test_render_cell_compat_pass_occupied(self):
        """Render occupied pass in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "MOUNTAIN_PASS")
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "I)"  # Unit + closing bracket (2 chars)

    def test_render_cell_compat_fortress_empty(self):
        """Render empty fortress in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "FORTRESS")

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "F"  # Fortress without trailing space

    def test_render_cell_compat_fortress_occupied(self):
        """Render occupied fortress in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "FORTRESS")
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "I]"  # Unit + closing bracket (2 chars)

    def test_render_cell_compat_south_unit_in_pass(self):
        """Render South unit in pass in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "MOUNTAIN_PASS")
        board.create_and_place_unit(10, 10, "INFANTRY", PLAYER_SOUTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        assert cell == "i)"  # Unit + closing bracket (2 chars)

    def test_render_cell_compat_multiple_terrain_types(self):
        """Render multiple terrain types in compatibility mode."""
        board = Board()

        # Set different terrain types
        board.set_terrain(10, 10, "MOUNTAIN")
        board.set_terrain(10, 11, "MOUNTAIN_PASS")
        board.set_terrain(10, 12, "FORTRESS")

        # Add units to pass and fortress
        board.create_and_place_unit(10, 11, "CAVALRY", PLAYER_NORTH)
        board.create_and_place_unit(10, 12, "CANNON", PLAYER_SOUTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)

        # Check each terrain type
        assert display._render_cell_compat(board, 10, 10) == "M"
        assert display._render_cell_compat(board, 10, 11) == "C)"  # Unit + closing bracket
        assert display._render_cell_compat(board, 10, 12) == "k]"  # Unit + closing bracket


class TestCursesRendering:
    """Test curses mode rendering with terrain."""

    def test_render_row_compat_includes_terrain(self):
        """Row rendering in compat mode includes terrain."""
        board = Board()

        # Set terrain on multiple squares
        board.set_terrain(10, 10, "MOUNTAIN")
        board.set_terrain(10, 11, "MOUNTAIN_PASS")
        board.create_and_place_unit(10, 11, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        row = display._render_row_compat(board, 10)

        # Row should contain terrain and units
        assert "M " in row  # Mountain with space added by join
        assert "I)" in row  # Occupied pass with closing bracket

    def test_render_compatibility_with_terrain(self):
        """Full compatibility rendering with terrain."""
        board = Board()

        # Add some terrain
        board.set_terrain(10, 10, "MOUNTAIN")
        board.set_terrain(10, 11, "MOUNTAIN_PASS")
        board.create_and_place_unit(10, 11, "INFANTRY", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        output = display._render_compatibility(board)

        # Output should be a string
        assert isinstance(output, str)
        # Should contain terrain glyphs
        assert "M " in output  # Mountain with space added by join
        assert "I)" in output  # Occupied pass with closing bracket


class TestTerrainDisplayIntegration:
    """Integration tests for terrain display."""

    def test_board_with_all_terrain_types(self):
        """Board rendering with all terrain types."""
        board = Board()

        # Place all terrain types
        board.set_terrain(5, 5, "MOUNTAIN")
        board.set_terrain(5, 6, "MOUNTAIN_PASS")
        board.create_and_place_unit(5, 6, "INFANTRY", PLAYER_NORTH)
        board.set_terrain(5, 7, "FORTRESS")
        board.create_and_place_unit(5, 7, "CAVALRY", PLAYER_SOUTH)

        # Test both modes
        for mode in [DisplayMode.CURSES, DisplayMode.COMPATIBILITY]:
            display = BoardDisplay(mode=mode)

            # Check individual cells
            cell_mountain = display._render_cell_compat(board, 5, 5) if mode == DisplayMode.COMPATIBILITY else None
            cell_pass = display._render_cell_compat(board, 5, 6) if mode == DisplayMode.COMPATIBILITY else None
            cell_fortress = display._render_cell_compat(board, 5, 7) if mode == DisplayMode.COMPATIBILITY else None

            if mode == DisplayMode.COMPATIBILITY:
                assert cell_mountain == "M"  # Empty terrain without space
                assert cell_pass == "I)"  # Unit + closing bracket
                assert cell_fortress == "c]"  # Unit + closing bracket

    def test_swift_unit_on_terrain_compat(self):
        """Swift unit on terrain in compatibility mode."""
        board = Board()
        board.set_terrain(10, 10, "FORTRESS")
        board.create_and_place_unit(10, 10, "SWIFT_CANNON", PLAYER_NORTH)

        display = BoardDisplay(mode=DisplayMode.COMPATIBILITY)
        cell = display._render_cell_compat(board, 10, 10)

        # Swift cannon in fortress - unit + closing bracket
        assert cell == "W]"
