# Engine interface tests

import pytest

from pykrieg.protocol.engine import UCIEngine
from pykrieg.protocol.uci import EngineOption, GoParameters


class MockEngine(UCIEngine):
    """Mock engine for testing."""

    def __init__(self) -> None:
        super().__init__()
        self._search_return_value = "1A1B"

    def get_name(self) -> str:
        return "MockEngine"

    def get_author(self) -> str:
        return "TestAuthor"

    def go(self, params: GoParameters) -> str:
        return self._search_return_value

    def set_search_return(self, move: str) -> None:
        self._search_return_value = move


class TestUCIEngine:
    def test_uci_initialization(self) -> None:
        engine = MockEngine()
        engine.uci()
        assert engine.debug_mode is False

    def test_get_name(self) -> None:
        engine = MockEngine()
        assert engine.get_name() == "MockEngine"

    def test_get_author(self) -> None:
        engine = MockEngine()
        assert engine.get_author() == "TestAuthor"

    def test_isready(self) -> None:
        engine = MockEngine()
        assert engine.isready() is True

    def test_setoption_check(self) -> None:
        engine = MockEngine()
        # Add a test option
        engine._options["TestOption"] = EngineOption(
            name="TestOption", type="check", default=False, min=None, max=None, var=None
        )

        engine.setoption("TestOption", "true")
        assert engine._option_values["TestOption"] is True

    def test_setoption_spin(self) -> None:
        engine = MockEngine()
        engine._options["Hash"] = EngineOption(
            name="Hash", type="spin", default=128, min=1, max=1024, var=None
        )

        engine.setoption("Hash", "256")
        assert engine._option_values["Hash"] == 256

    def test_setoption_unknown(self) -> None:
        engine = MockEngine()
        with pytest.raises(ValueError):
            engine.setoption("Unknown", "value")

    def test_ucinewgame(self) -> None:
        engine = MockEngine()
        engine.ucinewgame()
        # Should not raise exception

    def test_position_startpos(self) -> None:
        engine = MockEngine()
        engine.position("startpos", None, [])
        # Should not raise exception

    def test_position_with_moves(self) -> None:
        engine = MockEngine()
        engine.position("startpos", None, ["1A1B"])
        # Should not raise exception

    def test_apply_move_valid(self) -> None:
        engine = MockEngine()
        engine._apply_move("1A1B")
        # Should not raise exception

    def test_apply_move_invalid_format(self) -> None:
        engine = MockEngine()
        with pytest.raises(ValueError):
            engine._apply_move("ZZZZ")

    def test_apply_move_invalid_row(self) -> None:
        engine = MockEngine()
        with pytest.raises(ValueError):
            engine._apply_move("0A1B")

    def test_apply_move_invalid_column(self) -> None:
        engine = MockEngine()
        with pytest.raises(ValueError):
            engine._apply_move("1Z1B")

    def test_go_depth(self) -> None:
        engine = MockEngine()
        engine.set_search_return("1A1B")

        params = GoParameters(depth=5, nodes=None, movetime=None, infinite=False, ponder=False)
        move = engine.go(params)

        assert move == "1A1B"

    def test_stop(self) -> None:
        engine = MockEngine()
        engine.stop()
        # Should not raise exception

    def test_cleanup(self) -> None:
        engine = MockEngine()
        engine.cleanup()
        # Should not raise exception
