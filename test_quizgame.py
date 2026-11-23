"""간단한 자동 테스트 (표준 라이브러리 unittest만 사용).

실행: python test_quizgame.py   (또는 python -m unittest -v)
실제 state.json은 건드리지 않고, 임시 폴더의 파일로 시험한다.
"""
import io
import json
import os
import signal
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import main


class TempState(unittest.TestCase):
    """각 테스트마다 임시 폴더의 state.json을 쓰도록 바꾼다."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "state.json")
        self.patches = [
            mock.patch.object(main, "STATE_FILE", self.path),
            mock.patch.object(main, "BACKUP_FILE", self.path + ".bak"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.dir.cleanup()

    def run_game(self, inputs):
        """입력 목록을 차례로 넣어 게임을 실행하고 출력 문자열을 돌려준다."""
        out = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs), redirect_stdout(out):
            game = main.QuizGame()
            game.run()
        self.game = game
        return out.getvalue()


class QuizTests(unittest.TestCase):
    """Quiz 클래스의 책임: 채점, 변환, 형식 검증"""

    def test_is_correct(self):
        q = main.Quiz("문제", ["a", "b", "c", "d"], 2)
        self.assertTrue(q.is_correct(2))
        self.assertFalse(q.is_correct(1))

    def test_default_quizzes_five_with_category(self):
        quizzes = main.default_quizzes()
        self.assertEqual(len(quizzes), 5)
        self.assertTrue(all(len(q.choices) == main.NUM_CHOICES and q.category for q in quizzes))

    def test_from_dict_legacy_without_category(self):
        q = main.Quiz.from_dict({"question": "q", "choices": ["a", "b", "c", "d"], "answer": 3})
        self.assertEqual(q.category, "일반")

    def test_from_dict_rejects_bad_data(self):
        with self.assertRaises(ValueError):
            main.Quiz.from_dict({"question": "q", "choices": ["a", "b"], "answer": 1})
        with self.assertRaises(ValueError):
            main.Quiz.from_dict({"question": "q", "choices": ["a", "b", "c", "d"], "answer": 9})

    def test_round_trip(self):
        q = main.default_quizzes()[0]
        again = main.Quiz.from_dict(q.to_dict())
        self.assertEqual((again.question, again.choices, again.answer, again.category),
                         (q.question, q.choices, q.answer, q.category))


class InputTests(TempState):
    """QuizGame의 책임: 입력 검증"""

    def read(self, inputs, low=1, high=5):
        game = main.QuizGame()
        out = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs), redirect_stdout(out):
            value = game.read_int("선택: ", low, high)
        return value, out.getvalue()

    def test_valid_with_spaces(self):
        self.assertEqual(self.read([" 3 "])[0], 3)

    def test_invalid_inputs_reprompt(self):
        value, out = self.read(["", "abc", "9", "0", "2"])
        self.assertEqual(value, 2)
        self.assertIn("빈 입력", out)
        self.assertIn("숫자만 입력", out)
        self.assertEqual(out.count("1~5 사이의 숫자를 입력하세요."), 2)

    def test_ctrl_c_and_eof_return_none(self):
        self.assertIsNone(self.read([KeyboardInterrupt()])[0])
        self.assertIsNone(self.read([EOFError()])[0])


class FlowTests(TempState):
    """메뉴 선택 흐름(시나리오)과 영속성"""

    def test_menu_flow_list_score_exit(self):
        out = self.run_game(["3", "4", "5"])
        self.assertIn("등록된 퀴즈 (5개)", out)
        self.assertIn("아직 퀴즈를 풀지 않았습니다.", out)
        self.assertIn("종료합니다.", out)

    def test_invalid_menu_then_exit(self):
        out = self.run_game(["abc", "9", "", "5"])
        self.assertIn("숫자만 입력하세요.", out)
        self.assertIn("1~6 사이의 숫자를 입력하세요.", out)

    def test_play_updates_best_score_and_persists(self):
        out = self.run_game(["1"] + ["1"] * 5 + ["4", "5"])   # 정답은 모두 1번
        self.assertIn("5문제 중 5문제 정답", out)
        self.assertIn("최고 점수: 5/5", out)
        self.game = None
        self.run_game(["4", "5"])
        self.assertEqual(self.game.best_score, 5)

    def test_add_quiz_persists_after_restart(self):
        self.run_game(["2", "새 문제", "가", "나", "다", "라", "3", "5"])
        self.run_game(["5"])
        self.assertEqual(len(self.game.quizzes), 6)
        self.assertEqual(self.game.quizzes[-1].question, "새 문제")

    def test_eof_during_menu_is_safe_and_saves(self):
        out = self.run_game([EOFError()])
        self.assertIn("입력이 중단되었습니다.", out)
        self.assertTrue(os.path.exists(self.path))


class StorageTests(TempState):
    """QuizGame의 책임: 저장/불러오기, 복구"""

    def test_first_run_uses_default_quizzes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            game = main.QuizGame()
        self.assertEqual(len(game.quizzes), 5)

    def test_corrupted_file_is_backed_up(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{깨진")
        out = io.StringIO()
        with redirect_stdout(out):
            game = main.QuizGame()
        self.assertEqual(len(game.quizzes), 5)
        self.assertIn("손상", out.getvalue())
        with open(self.path + ".bak", encoding="utf-8") as f:
            self.assertEqual(f.read(), "{깨진")

    def test_save_is_atomic_no_tmp_left(self):
        game = main.QuizGame.__new__(main.QuizGame)
        game.quizzes, game.best_score = main.default_quizzes(), 3
        game.save()
        self.assertFalse(os.path.exists(self.path + ".tmp"))
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["best_score"], 3)
        self.assertEqual(len(data["quizzes"]), 5)

    def test_save_retries_then_succeeds(self):
        game = main.QuizGame.__new__(main.QuizGame)
        game.quizzes, game.best_score = main.default_quizzes(), None
        real = os.replace
        calls = {"n": 0}

        def flaky(src, dst):
            calls["n"] += 1
            if calls["n"] < 3:
                raise OSError("일시적 오류")
            return real(src, dst)

        with mock.patch.object(main.os, "replace", flaky), mock.patch.object(main.time, "sleep"):
            game.save()
        self.assertEqual(calls["n"], 3)
        self.assertTrue(os.path.exists(self.path))

    def test_save_gives_up_with_message(self):
        game = main.QuizGame.__new__(main.QuizGame)
        game.quizzes, game.best_score = main.default_quizzes(), None
        out = io.StringIO()
        with mock.patch.object(main.os, "replace", side_effect=OSError("권한 없음")), \
                mock.patch.object(main.time, "sleep"), redirect_stdout(out):
            game.save()
        self.assertIn("저장 실패", out.getvalue())


class SignalTests(unittest.TestCase):
    def test_sigterm_handler_registered_and_acts_like_ctrl_c(self):
        old = signal.getsignal(signal.SIGTERM)
        try:
            main.install_signal_handlers()
            handler = signal.getsignal(signal.SIGTERM)
            self.assertTrue(callable(handler))
            with self.assertRaises(KeyboardInterrupt):
                handler(signal.SIGTERM, None)
        finally:
            signal.signal(signal.SIGTERM, old)


if __name__ == "__main__":
    unittest.main(verbosity=2)
