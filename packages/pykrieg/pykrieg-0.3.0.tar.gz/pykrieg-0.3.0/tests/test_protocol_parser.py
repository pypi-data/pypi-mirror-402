# Parser unit tests

import pytest

from pykrieg.protocol.exceptions import ParseError, UnknownCommandError
from pykrieg.protocol.parser import ProtocolParser


class TestProtocolParser:
    def test_parse_uci_command(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("uci")
        assert cmd.command == "uci"
        assert cmd.parameters == {}

    def test_parse_uci_with_args_raises_error(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("uci extra args")

    def test_parse_debug_on(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("debug on")
        assert cmd.command == "debug"
        assert cmd.parameters == {"mode": "on"}

    def test_parse_debug_off(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("debug off")
        assert cmd.command == "debug"
        assert cmd.parameters == {"mode": "off"}

    def test_parse_debug_invalid_mode(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("debug maybe")

    def test_parse_isready(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("isready")
        assert cmd.command == "isready"
        assert cmd.parameters == {}

    def test_parse_setoption(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("setoption name Hash value 256")
        assert cmd.command == "setoption"
        assert cmd.parameters == {"name": "Hash", "value": "256"}

    def test_parse_setoption_with_spaces(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("setoption name MultiPV value 3")
        assert cmd.parameters == {"name": "MultiPV", "value": "3"}

    def test_parse_setoption_missing_value(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("setoption name Hash")

    def test_parse_ucinewgame(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("ucinewgame")
        assert cmd.command == "ucinewgame"
        assert cmd.parameters == {}

    def test_parse_position_startpos(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("position startpos")
        assert cmd.command == "position"
        assert cmd.parameters["type"] == "startpos"
        assert cmd.parameters["moves"] == []

    def test_parse_position_startpos_with_moves(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("position startpos moves 1A1B 2C2D")
        assert cmd.parameters["moves"] == ["1A1B", "2C2D"]

    def test_parse_position_kfen(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("position kfen game.kfen")
        assert cmd.parameters["type"] == "kfen"
        assert cmd.parameters["value"] == "game.kfen"

    def test_parse_position_invalid_type(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("position invalid type")

    def test_parse_position_fen_not_supported(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("position fen I:...:N:M:B")

    def test_parse_go_depth(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("go depth 10")
        assert cmd.command == "go"
        assert cmd.parameters["depth"] == 10
        assert cmd.parameters["infinite"] is False

    def test_parse_go_nodes(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("go nodes 1000000")
        assert cmd.parameters["nodes"] == 1000000

    def test_parse_go_movetime(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("go movetime 1000")
        assert cmd.parameters["movetime"] == 1000

    def test_parse_go_infinite(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("go infinite")
        assert cmd.parameters["infinite"] is True

    def test_parse_go_multiple_params(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("go depth 10 nodes 100000")
        assert cmd.parameters["depth"] == 10
        assert cmd.parameters["nodes"] == 100000

    def test_parse_stop(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("stop")
        assert cmd.command == "stop"
        assert cmd.parameters == {}

    def test_parse_quit(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("quit")
        assert cmd.command == "quit"
        assert cmd.parameters == {}

    def test_parse_unknown_command(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(UnknownCommandError):
            parser.parse("unknown")

    def test_parse_empty_command(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("")

    def test_parse_whitespace_only(self) -> None:
        parser = ProtocolParser()
        with pytest.raises(ParseError):
            parser.parse("   ")

    def test_parse_status(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("status")
        assert cmd.command == "status"
        assert cmd.parameters == {}

    def test_parse_network(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("network")
        assert cmd.command == "network"
        assert cmd.parameters == {}

    def test_parse_victory(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("victory")
        assert cmd.command == "victory"
        assert cmd.parameters == {}

    def test_parse_phase(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("phase movement")
        assert cmd.command == "phase"
        assert cmd.parameters == {"phase": "movement"}

    def test_parse_retreats(self) -> None:
        parser = ProtocolParser()
        cmd = parser.parse("retreats")
        assert cmd.command == "retreats"
        assert cmd.parameters == {}
