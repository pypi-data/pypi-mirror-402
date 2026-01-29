"""
Test coordinate system conversions in pykrieg.board module.
"""
import pytest

from pykrieg.board import Board


class TestCoordinateConversions:
    """Test coordinate system conversions."""

    def test_spreadsheet_to_tuple(self):
        """Test converting spreadsheet coordinates to tuples."""
        # Top-left corner
        assert Board.spreadsheet_to_tuple("1A") == (0, 0)
        assert Board.spreadsheet_to_tuple("25A") == (0, 24)

        # Bottom row (row 19 in 0-based from top)
        assert Board.spreadsheet_to_tuple("1T") == (19, 0)
        assert Board.spreadsheet_to_tuple("25T") == (19, 24)

        # Middle rows
        assert Board.spreadsheet_to_tuple("1J") == (9, 0)
        assert Board.spreadsheet_to_tuple("27J") == (9, 26)

    def test_tuple_to_spreadsheet(self):
        """Test converting tuples to spreadsheet coordinates."""
        # Top-left corner
        assert Board.tuple_to_spreadsheet(0, 0) == "1A"
        assert Board.tuple_to_spreadsheet(0, 24) == "25A"

        # Bottom row (row 19)
        assert Board.tuple_to_spreadsheet(19, 0) == "1T"
        assert Board.tuple_to_spreadsheet(19, 24) == "25T"

        # Middle rows
        assert Board.tuple_to_spreadsheet(9, 0) == "1J"
        assert Board.tuple_to_spreadsheet(9, 26) == "27J"

    def test_spreadsheet_roundtrip(self):
        """Test spreadsheet coordinate conversion roundtrip."""
        # Spreadsheet -> Tuple -> Spreadsheet
        original = "7G"
        tup = Board.spreadsheet_to_tuple(original)
        back = Board.tuple_to_spreadsheet(*tup)
        assert back == original

        # Tuple -> Spreadsheet -> Tuple
        original_tup = (5, 6)
        coord = Board.tuple_to_spreadsheet(*original_tup)
        back_tup = Board.spreadsheet_to_tuple(coord)
        assert back_tup == original_tup

    def test_multi_column_notation(self):
        """Test multi-letter column notation."""
        # AA is 26th column (index 25)
        assert Board.spreadsheet_to_tuple("27A") == (0, 26)
        assert Board.tuple_to_spreadsheet(0, 26) == "27A"

        # AZ is 52nd column (index 51)
        assert Board.spreadsheet_to_tuple("52A") == (0, 51)
        assert Board.tuple_to_spreadsheet(0, 51) == "52A"

        # BA is 53rd column (index 52)
        assert Board.spreadsheet_to_tuple("53A") == (0, 52)
        assert Board.tuple_to_spreadsheet(0, 52) == "53A"

    def test_invalid_spreadsheet_string(self):
        """Test invalid spreadsheet coordinates raise errors."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("1")  # No column letters

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A")  # No row number

        with pytest.raises(TypeError):
            Board.spreadsheet_to_tuple(123)  # Not a string

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("")  # Empty string

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("1")  # Zero row (invalid)

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A-5")  # Negative row (invalid)

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("B-1")  # Negative row (invalid)

    def test_tuple_to_index(self):
        """Test converting coordinates to square index."""
        assert Board.tuple_to_index(0, 0) == 0
        assert Board.tuple_to_index(0, 1) == 1
        assert Board.tuple_to_index(1, 0) == 25
        assert Board.tuple_to_index(19, 24) == 499

    def test_tuple_to_index_custom_board_size(self):
        """Test tuple_to_index with custom board dimensions."""
        # Test with different board sizes
        assert Board.tuple_to_index(0, 0, board_cols=10) == 0
        assert Board.tuple_to_index(1, 0, board_cols=10) == 10
        assert Board.tuple_to_index(0, 5, board_cols=10) == 5

    def test_index_to_tuple(self):
        """Test converting square index to coordinates."""
        assert Board.index_to_tuple(0) == (0, 0)
        assert Board.index_to_tuple(1) == (0, 1)
        assert Board.index_to_tuple(25) == (1, 0)
        assert Board.index_to_tuple(499) == (19, 24)

    def test_index_to_tuple_custom_board_size(self):
        """Test index_to_tuple with custom board dimensions."""
        assert Board.index_to_tuple(0, board_cols=10, board_rows=10) == (0, 0)
        assert Board.index_to_tuple(10, board_cols=10, board_rows=10) == (1, 0)
        assert Board.index_to_tuple(5, board_cols=10, board_rows=10) == (0, 5)

    def test_index_roundtrip(self):
        """Test index conversion roundtrip."""
        for index in [0, 1, 25, 127, 499]:
            row, col = Board.index_to_tuple(index)
            back_index = Board.tuple_to_index(row, col)
            assert back_index == index

    def test_invalid_index(self):
        """Test invalid indices raise errors."""
        with pytest.raises(ValueError):
            Board.index_to_tuple(-1)

        with pytest.raises(ValueError):
            Board.index_to_tuple(500)

        with pytest.raises(ValueError):
            Board.index_to_tuple(1000)

        with pytest.raises(TypeError):
            Board.index_to_tuple("0")

    def test_invalid_tuple_to_index(self):
        """Test invalid coordinates raise errors for tuple_to_index."""
        with pytest.raises(ValueError):
            Board.tuple_to_index(-1, 0)

        with pytest.raises(ValueError):
            Board.tuple_to_index(0, -1)

        with pytest.raises(ValueError):
            Board.tuple_to_index(-5, -10)

    def test_spreadsheet_case_insensitive(self):
        """Test that spreadsheet coordinates are case-insensitive."""
        assert Board.spreadsheet_to_tuple("1a") == Board.spreadsheet_to_tuple("1A")
        assert Board.spreadsheet_to_tuple("1j") == Board.spreadsheet_to_tuple("1J")
        assert Board.spreadsheet_to_tuple("1t") == Board.spreadsheet_to_tuple("1T")

    def test_various_spreadsheet_coordinates(self):
        """Test a variety of spreadsheet coordinate conversions."""
        test_cases = [
            ("1A", (0, 0)),
            ("2A", (0, 1)),
            ("26A", (0, 25)),
            ("27A", (0, 26)),
            ("28A", (0, 27)),
            ("52A", (0, 51)),
            ("53A", (0, 52)),
            ("702A", (0, 701)),
            ("1B", (1, 0)),
            ("1J", (9, 0)),
            ("1T", (19, 0)),
            ("2E", (4, 1)),
            ("7G", (6, 6)),
            ("20O", (14, 19)),
        ]

        for coord, expected in test_cases:
            assert Board.spreadsheet_to_tuple(coord) == expected
            assert Board.tuple_to_spreadsheet(*expected) == coord.upper()

    def test_coordinate_boundary_values(self):
        """Test coordinate conversions at boundary values."""
        # Minimum values
        assert Board.spreadsheet_to_tuple("1A") == (0, 0)
        assert Board.tuple_to_spreadsheet(0, 0) == "1A"
        assert Board.tuple_to_index(0, 0) == 0
        assert Board.index_to_tuple(0) == (0, 0)

        # Maximum values for 20x25 board
        assert Board.tuple_to_spreadsheet(19, 24) == "25T"
        assert Board.tuple_to_index(19, 24) == 499
        assert Board.index_to_tuple(499) == (19, 24)

    def test_all_single_letter_rows(self):
        """Test all single-letter row names (A-T)."""
        for i in range(20):
            row_letter = chr(ord('A') + i)
            coord = f"1{row_letter}"
            expected = (i, 0)
            assert Board.spreadsheet_to_tuple(coord) == expected
            assert Board.tuple_to_spreadsheet(i, 0) == coord

    def test_index_to_tuple_edge_cases(self):
        """Test index_to_tuple at edge cases."""
        # First index
        assert Board.index_to_tuple(0) == (0, 0)

        # Last index for 20x25 board
        assert Board.index_to_tuple(499) == (19, 24)

        # Index at row boundary
        assert Board.index_to_tuple(24) == (0, 24)
        assert Board.index_to_tuple(25) == (1, 0)

        # Middle of board
        assert Board.index_to_tuple(250) == (10, 0)

    def test_tuple_to_index_edge_cases(self):
        """Test tuple_to_index at edge cases."""
        # Corners
        assert Board.tuple_to_index(0, 0) == 0
        assert Board.tuple_to_index(0, 24) == 24
        assert Board.tuple_to_index(19, 0) == 475
        assert Board.tuple_to_index(19, 24) == 499

        # Row boundaries
        assert Board.tuple_to_index(9, 24) == 249
        assert Board.tuple_to_index(10, 0) == 250

    def test_empty_string_spreadsheet(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("")

    def test_whitespace_in_spreadsheet(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("   ")

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A 1")

    def test_numeric_only_spreadsheet(self):
        """Test that numeric-only string raises ValueError."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("123")

    def test_alpha_only_spreadsheet(self):
        """Test that alpha-only string raises ValueError."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("ABC")

    def test_tuple_to_spreadsheet_invalid_types(self):
        """Test that tuple_to_spreadsheet raises TypeError for invalid types."""
        with pytest.raises(TypeError):
            Board.tuple_to_spreadsheet("0", 0)  # Row is string

        with pytest.raises(TypeError):
            Board.tuple_to_spreadsheet(0, "0")  # Col is string

        with pytest.raises(TypeError):
            Board.tuple_to_spreadsheet(None, 0)  # Row is None

        with pytest.raises(TypeError):
            Board.tuple_to_spreadsheet(0, None)  # Col is None

    def test_extremely_large_spreadsheet_coordinates(self):
        """Test conversion of very large spreadsheet coordinates."""
        # AAA is 703rd column (26^2 + 26 + 1)
        assert Board.spreadsheet_to_tuple("703A") == (0, 702)
        assert Board.tuple_to_spreadsheet(0, 702) == "703A"

        # ZZZ is 18278th column (26^3 + 26^2 + 26)
        assert Board.spreadsheet_to_tuple("18278A") == (0, 18277)
        assert Board.tuple_to_spreadsheet(0, 18277) == "18278A"

        # Test with larger row numbers
        assert Board.spreadsheet_to_tuple("28CV") == (99, 27)
        assert Board.tuple_to_spreadsheet(99, 27) == "28CV"

    def test_spreadsheet_with_mixed_case(self):
        """Test spreadsheet coordinates with mixed case letters."""
        assert Board.spreadsheet_to_tuple("1AbCd") == Board.spreadsheet_to_tuple("1ABCD")
        assert Board.tuple_to_spreadsheet(1, 6).lower() == Board.tuple_to_spreadsheet(1, 6).lower()

    def test_spreadsheet_with_special_characters(self):
        """Test spreadsheet coordinates with special characters raise error."""
        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A1!")  # Special character

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A-1")  # Hyphen

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A_1")  # Underscore

        with pytest.raises(ValueError):
            Board.spreadsheet_to_tuple("A.1")  # Dot

    def test_index_conversion_with_large_values(self):
        """Test index conversions with large board dimensions."""
        # Test with 100x100 board
        assert Board.tuple_to_index(99, 99, board_cols=100) == 9999
        assert Board.index_to_tuple(9999, board_cols=100, board_rows=100) == (99, 99)

        # Test with 50x50 board
        assert Board.tuple_to_index(49, 49, board_cols=50) == 2499
        assert Board.index_to_tuple(2499, board_cols=50, board_rows=50) == (49, 49)

    def test_tuple_to_index_negative_coordinates(self):
        """Test tuple_to_index with negative coordinates raises error."""
        with pytest.raises(ValueError):
            Board.tuple_to_index(-1, 0)

        with pytest.raises(ValueError):
            Board.tuple_to_index(0, -1)

        with pytest.raises(ValueError):
            Board.tuple_to_index(-10, -5)

    def test_index_conversion_boundary_cases(self):
        """Test index conversion at boundary values."""
        # First index
        assert Board.index_to_tuple(0) == (0, 0)
        assert Board.tuple_to_index(0, 0) == 0

        # Last index for default board
        assert Board.index_to_tuple(499) == (19, 24)
        assert Board.tuple_to_index(19, 24) == 499

        # Index at row boundary
        assert Board.index_to_tuple(24) == (0, 24)
        assert Board.tuple_to_index(0, 24) == 24

        assert Board.index_to_tuple(25) == (1, 0)
        assert Board.tuple_to_index(1, 0) == 25
