# Response generator tests


from pykrieg.protocol.response import ResponseGenerator
from pykrieg.protocol.uci import EngineOption, InfoParameters, Score


class TestResponseGenerator:
    def test_uci_identification(self) -> None:
        gen = ResponseGenerator(engine_name="TestEngine", engine_author="TestAuthor")
        response = gen.uci_identification()
        assert "id name TestEngine" in response
        assert "id author TestAuthor" in response
        assert "uciok" in response

    def test_ready_ok(self) -> None:
        gen = ResponseGenerator()
        response = gen.ready_ok()
        assert response == "readyok"

    def test_best_move_simple(self) -> None:
        gen = ResponseGenerator()
        response = gen.best_move("1A1B")
        assert response == "bestmove 1A1B"

    def test_best_move_with_ponder(self) -> None:
        gen = ResponseGenerator()
        response = gen.best_move("1A1B", "2C2D")
        assert response == "bestmove 1A1B ponder 2C2D"

    def test_best_move_none(self) -> None:
        gen = ResponseGenerator()
        response = gen.best_move(None)
        assert response == "bestmove (none)"

    def test_info_depth(self) -> None:
        gen = ResponseGenerator()
        params = InfoParameters(depth=10)
        response = gen.info(params)
        assert "depth 10" in response

    def test_info_with_score_cp(self) -> None:
        gen = ResponseGenerator()
        score = Score(cp=150, lowerbound=False, upperbound=False)
        params = InfoParameters(depth=10, score=score)
        response = gen.info(params)
        assert "score cp 150" in response

    def test_info_with_score_mate(self) -> None:
        gen = ResponseGenerator()
        score = Score(mate=5, lowerbound=False, upperbound=False)
        params = InfoParameters(depth=10, score=score)
        response = gen.info(params)
        assert "score mate 5" in response

    def test_info_with_lowerbound(self) -> None:
        gen = ResponseGenerator()
        score = Score(cp=100, lowerbound=True, upperbound=False)
        params = InfoParameters(depth=10, score=score)
        response = gen.info(params)
        assert "lowerbound" in response

    def test_info_full(self) -> None:
        gen = ResponseGenerator()
        score = Score(cp=150, lowerbound=False, upperbound=False)
        params = InfoParameters(
            depth=10,
            seldepth=15,
            time=5000,
            nodes=100000,
            score=score,
            currmove="1A1B",
            currmovenumber=5,
            hashfull=1000,
            nps=20000,
        )
        response = gen.info(params)
        assert "depth 10" in response
        assert "seldepth 15" in response
        assert "time 5000" in response
        assert "nodes 100000" in response
        assert "score cp 150" in response
        assert "currmove 1A1B" in response
        assert "currmovenumber 5" in response
        assert "hashfull 1000" in response
        assert "nps 20000" in response

    def test_option_spin(self) -> None:
        gen = ResponseGenerator()
        option = EngineOption(name="Hash", type="spin", default=128, min=1, max=1024, var=None)
        response = gen.option(option)
        assert "option name Hash type spin default 128" in response
        assert "min 1" in response
        assert "max 1024" in response

    def test_option_combo(self) -> None:
        gen = ResponseGenerator()
        option = EngineOption(
            name="Style",
            type="combo",
            default="Balanced",
            min=None,
            max=None,
            var=["Aggressive", "Balanced", "Defensive"],
        )
        response = gen.option(option)
        assert "option name Style type combo default Balanced" in response
        assert "var Aggressive" in response
        assert "var Defensive" in response

    def test_option_check(self) -> None:
        gen = ResponseGenerator()
        option = EngineOption(
            name="Ponder", type="check", default=False, min=None, max=None, var=None
        )
        response = gen.option(option)
        assert "option name Ponder type check default false" in response

    def test_status(self) -> None:
        gen = ResponseGenerator()
        response = gen.status(turn="NORTH", phase="movement", turn_number=1)
        assert "turn=NORTH" in response
        assert "phase=movement" in response
        assert "turn_number=1" in response

    def test_network(self) -> None:
        gen = ResponseGenerator()
        response = gen.network(north_online=20, north_offline=5, south_online=18, south_offline=7)
        assert "north_online=20" in response
        assert "north_offline=5" in response
        assert "south_online=18" in response
        assert "south_offline=7" in response

    def test_victory_ongoing(self) -> None:
        gen = ResponseGenerator()
        response = gen.victory(winner=None, condition=None)
        assert response == "victory false ongoing"

    def test_victory_complete(self) -> None:
        gen = ResponseGenerator()
        response = gen.victory(winner="NORTH", condition="elimination")
        assert "victory true" in response
        assert "winner=NORTH" in response
        assert "condition=elimination" in response

    def test_phase(self) -> None:
        gen = ResponseGenerator()
        response = gen.phase("movement")
        assert response == "phase movement"

    def test_retreats_none(self) -> None:
        gen = ResponseGenerator()
        response = gen.retreats([])
        assert response == "retreats none"

    def test_retreats_with_units(self) -> None:
        gen = ResponseGenerator()
        response = gen.retreats(["1A", "5B", "10C"])
        assert "retreats 1A,5B,10C" in response

    def test_error(self) -> None:
        gen = ResponseGenerator()
        response = gen.error("Something went wrong")
        assert response == "error Something went wrong"
