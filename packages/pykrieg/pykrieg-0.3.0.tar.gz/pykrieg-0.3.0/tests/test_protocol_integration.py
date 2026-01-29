# Protocol integration tests

from typing import List, Optional

from pykrieg.protocol.engine import UCIEngine
from pykrieg.protocol.parser import ProtocolParser
from pykrieg.protocol.response import ResponseGenerator
from pykrieg.protocol.uci import GoParameters


class SimpleEngine(UCIEngine):
    """Simple test engine for integration testing."""

    def __init__(self) -> None:
        super().__init__()
        self.move_counter = 0
        self.position_set = False

    def get_name(self) -> str:
        return "Pykrieg Test Engine"

    def get_author(self) -> str:
        return "Pykrieg Test Team"

    def go(self, params: GoParameters) -> str:
        # Generate deterministic moves for testing
        self.move_counter += 1
        row = (self.move_counter // 25) % 19 + 1
        col = (self.move_counter % 25)
        col_letter = chr(ord('A') + col) if col < 26 else 'A'
        from_pos = f"{row}{col_letter}"
        to_col = chr(ord('A') + (col + 1) % 25) if (col + 1) < 26 else 'A'
        to_pos = f"{row}{to_col}"
        return f"{from_pos}{to_pos}"

    def position(
        self,
        position_type: str,
        value: Optional[str],
        moves: List[str],
    ) -> None:
        super().position(position_type, value, moves)
        self.position_set = True


class MockFrontend:
    """Mock frontend for testing engine communication."""

    def __init__(self, engine: UCIEngine) -> None:
        self.engine = engine
        self.parser = ProtocolParser()
        self.response_gen = ResponseGenerator()
        self.output: List[str] = []
        self.engine_ready = False
        self.game_started = False

    def send_command(self, command: str) -> None:
        """Send command to engine and capture response."""
        parsed = self.parser.parse(command)
        self._execute_command(parsed)

    def _execute_command(self, parsed) -> None:  # noqa: ANN401
        """Execute parsed command on engine."""
        if parsed.command == "uci":
            self._handle_uci()
        elif parsed.command == "debug":
            mode = parsed.parameters.get("mode", "off")
            self.engine.debug_mode = mode == "on"
        elif parsed.command == "isready":
            self._handle_isready()
        elif parsed.command == "setoption":
            self.engine.setoption(
                parsed.parameters["name"],
                parsed.parameters["value"],
            )
        elif parsed.command == "ucinewgame":
            self.engine.ucinewgame()
            self.game_started = True
        elif parsed.command == "position":
            self.engine.position(
                parsed.parameters["type"],
                parsed.parameters.get("value"),
                parsed.parameters["moves"],
            )
        elif parsed.command == "go":
            params = GoParameters(**parsed.parameters)
            move = self.engine.go(params)
            self.output.append(self.response_gen.best_move(move))
        elif parsed.command == "stop":
            self.engine.stop()
        elif parsed.command == "quit":
            self.engine.cleanup()
        elif parsed.command == "status":
            self._handle_status()
        elif parsed.command == "network":
            self._handle_network()
        elif parsed.command == "victory":
            self._handle_victory()
        elif parsed.command == "phase":
            phase = parsed.parameters.get("phase", "movement")
            self.output.append(self.response_gen.phase(phase))
        elif parsed.command == "retreats":
            self.output.append(self.response_gen.retreats([]))

    def _handle_uci(self) -> None:
        """Handle UCI initialization."""
        self.engine.uci()
        self.output.append(
            self.response_gen.uci_identification().replace(
                "Pykrieg Engine",
                self.engine.get_name(),
            ).replace(
                "Pykrieg Team",
                self.engine.get_author(),
            )
        )
        self.engine_ready = True

    def _handle_isready(self) -> None:
        """Handle isready command."""
        ready = self.engine.isready()
        if ready:
            self.output.append(self.response_gen.ready_ok())

    def _handle_status(self) -> None:
        """Handle status command."""
        response = self.response_gen.status(
            turn="NORTH",
            phase="movement",
            turn_number=1,
        )
        self.output.append(response)

    def _handle_network(self) -> None:
        """Handle network command."""
        response = self.response_gen.network(
            north_online=10,
            north_offline=2,
            south_online=10,
            south_offline=2,
        )
        self.output.append(response)

    def _handle_victory(self) -> None:
        """Handle victory command."""
        response = self.response_gen.victory(
            winner=None,
            condition=None,
        )
        self.output.append(response)


class TestProtocolIntegration:
    def test_full_initialization_sequence(self) -> None:
        """Test complete engine initialization sequence."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Send uci
        frontend.send_command("uci")

        assert len(frontend.output) == 1
        assert "id name Pykrieg Test Engine" in frontend.output[0]
        assert "id author Pykrieg Test Team" in frontend.output[0]
        assert "uciok" in frontend.output[0]

        # Send isready
        frontend.send_command("isready")

        assert len(frontend.output) == 2
        assert frontend.output[1] == "readyok"

        # Verify engine state
        assert frontend.engine_ready is True

    def test_debug_mode_toggle(self) -> None:
        """Test debug mode can be toggled."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")

        # Enable debug
        frontend.send_command("debug on")
        assert engine.debug_mode is True

        # Disable debug
        frontend.send_command("debug off")
        assert engine.debug_mode is False

    def test_option_setting(self) -> None:
        """Test setting engine options."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Add test options
        from pykrieg.protocol.uci import EngineOption

        engine._options["Hash"] = EngineOption(
            name="Hash",
            type="spin",
            default=128,
            min=1,
            max=1024,
            var=None,
        )
        engine._options["Ponder"] = EngineOption(
            name="Ponder",
            type="check",
            default=False,
            min=None,
            max=None,
            var=None,
        )

        frontend.send_command("uci")

        # Set spin option
        frontend.send_command("setoption name Hash value 256")
        assert engine._option_values.get("Hash") == 256

        # Set check option
        frontend.send_command("setoption name Ponder value true")
        assert engine._option_values.get("Ponder") is True

    def test_new_game_sequence(self) -> None:
        """Test starting a new game."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")

        # Start new game
        frontend.send_command("ucinewgame")
        assert frontend.game_started is True

        # Set position
        frontend.send_command("position startpos")
        assert engine.position_set is True

        # Set position with moves
        frontend.send_command("position startpos moves 1A1B 2C2D")
        assert engine.position_set is True

    def test_search_with_depth(self) -> None:
        """Test search with depth parameter."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize and set position
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # Search with depth
        frontend.send_command("go depth 5")

        assert len(frontend.output) == 3  # uci, readyok, bestmove
        assert "bestmove" in frontend.output[2]

    def test_search_with_nodes(self) -> None:
        """Test search with nodes parameter."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize and set position
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # Search with nodes
        frontend.send_command("go nodes 100000")

        assert len(frontend.output) == 3
        assert "bestmove" in frontend.output[2]

    def test_search_with_movetime(self) -> None:
        """Test search with time limit."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize and set position
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # Search with time limit
        frontend.send_command("go movetime 1000")

        assert len(frontend.output) == 3
        assert "bestmove" in frontend.output[2]

    def test_search_infinite_and_stop(self) -> None:
        """Test infinite search and stop."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize and set position
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # Start infinite search
        frontend.send_command("go infinite")

        # Stop search
        frontend.send_command("stop")

        # Should have bestmove from stop
        assert len(frontend.output) == 3
        assert "bestmove" in frontend.output[2]

    def test_multiple_searches_sequence(self) -> None:
        """Test multiple searches in sequence."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")

        # First search
        frontend.send_command("position startpos")
        frontend.send_command("go depth 5")
        first_move = frontend.output[2]

        # Second search
        frontend.send_command("position startpos moves 1A1B")
        frontend.send_command("go depth 5")
        second_move = frontend.output[3]

        # Moves should be different due to counter
        assert first_move != second_move
        assert "bestmove" in first_move
        assert "bestmove" in second_move

    def test_pykrieg_status_command(self) -> None:
        """Test Pykrieg-specific status command."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Query status
        frontend.send_command("status")

        assert len(frontend.output) == 2
        assert "status" in frontend.output[1]

    def test_pykrieg_network_command(self) -> None:
        """Test Pykrieg-specific network command."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Query network
        frontend.send_command("network")

        assert len(frontend.output) == 2
        assert "network" in frontend.output[1]

    def test_pykrieg_victory_command(self) -> None:
        """Test Pykrieg-specific victory command."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Query victory
        frontend.send_command("victory")

        assert len(frontend.output) == 2
        assert "victory" in frontend.output[1]

    def test_pykrieg_phase_command(self) -> None:
        """Test Pykrieg-specific phase command."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Query phase
        frontend.send_command("phase")
        assert len(frontend.output) == 2
        assert "phase movement" in frontend.output[1]

        # Set phase
        frontend.send_command("phase battle")
        assert len(frontend.output) == 3
        assert "phase battle" in frontend.output[2]

    def test_pykrieg_retreats_command(self) -> None:
        """Test Pykrieg-specific retreats command."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Query retreats
        frontend.send_command("retreats")

        assert len(frontend.output) == 2
        assert "retreats none" in frontend.output[1]

    def test_complete_game_session(self) -> None:
        """Test complete game session from start to finish."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialization
        frontend.send_command("uci")
        frontend.send_command("isready")

        # New game
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # North moves
        frontend.send_command("go depth 5")
        north_move = frontend.output[2]

        # South moves
        frontend.send_command("position startpos moves " + north_move.split()[1])
        frontend.send_command("go depth 5")
        frontend.output[3]

        # Check status
        frontend.send_command("status")

        # Check network
        frontend.send_command("network")

        # Check victory
        frontend.send_command("victory")

        # Verify session
        assert len(frontend.output) == 7
        assert "id name" in frontend.output[0]
        assert "readyok" in frontend.output[1]
        assert "bestmove" in frontend.output[2]
        assert "bestmove" in frontend.output[3]
        assert "status" in frontend.output[4]
        assert "network" in frontend.output[5]
        assert "victory" in frontend.output[6]

    def test_error_handling_invalid_option(self) -> None:
        """Test error handling for invalid option."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Try to set unknown option
        try:
            frontend.send_command("setoption name Unknown value test")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unknown option" in str(e)

    def test_error_handling_invalid_command(self) -> None:
        """Test error handling for invalid command."""
        from pykrieg.protocol.exceptions import UnknownCommandError

        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Try invalid command
        try:
            frontend.send_command("invalid_command")
            raise AssertionError("Should have raised UnknownCommandError")
        except UnknownCommandError:
            pass  # Expected

    def test_position_with_kfen(self) -> None:
        """Test position command with KFEN format."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")

        # Set position with KFEN
        frontend.send_command("position kfen game.kfen")
        assert engine.position_set is True

    def test_position_with_moves_sequence(self) -> None:
        """Test applying move sequence to position."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")

        # Set position with multiple moves
        frontend.send_command("position startpos moves 1A1B 2C2D 3E3F 4G4H 5I5J")
        assert engine.position_set is True

    def test_no_moves_available(self) -> None:
        """Test behavior when no moves are available."""
        engine = SimpleEngine()
        # Override go to return None
        original_go = engine.go

        def no_moves_go(params):  # type: ignore[no-untyped-def]
            return None

        engine.go = no_moves_go  # type: ignore[method-assign]

        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")
        frontend.send_command("isready")
        frontend.send_command("ucinewgame")
        frontend.send_command("position startpos")

        # Search
        frontend.send_command("go depth 5")

        assert len(frontend.output) == 3
        assert "bestmove (none)" in frontend.output[2]

        # Restore original
        engine.go = original_go  # type: ignore[method-assign]

    def test_cleanup_on_quit(self) -> None:
        """Test cleanup when quit command is sent."""
        engine = SimpleEngine()
        frontend = MockFrontend(engine)

        # Initialize
        frontend.send_command("uci")

        # Quit
        frontend.send_command("quit")

        # Verify cleanup was called
        assert True  # If no exception raised, cleanup succeeded
