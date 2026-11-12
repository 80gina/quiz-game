"""숲해설·환경교육 퀴즈 게임 (Python 3.10+, 표준 라이브러리만 사용)."""
import json
import os
import random

from npu_core import judge, make_cross, make_x, mac, normalize_label, render

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


class Quiz:
    """퀴즈 한 문제. answer는 1~4 번호."""

    def __init__(self, question: str, choices: list[str], answer: int):
        self.question = question
        self.choices = choices
        self.answer = answer

    def show(self, number: int | None = None) -> None:
        title = f"[문제 {number}] " if number else ""
        print(f"{title}{self.question}")
        for i, c in enumerate(self.choices, 1):
            print(f"  {i}. {c}")

    def is_correct(self, choice: int) -> bool:
        return choice == self.answer

    def to_dict(self) -> dict:
        return {"question": self.question, "choices": self.choices, "answer": self.answer}

    @staticmethod
    def from_dict(d: dict) -> "Quiz":
        choices = d["choices"]
        answer = d["answer"]
        if len(choices) != 4 or answer not in (1, 2, 3, 4):
            raise ValueError("잘못된 퀴즈 형식")
        return Quiz(str(d["question"]), [str(c) for c in choices], answer)


class PatternQuiz(Quiz):
    """그림(2차원 패턴)을 보고 Cross/X를 맞히는 퀴즈. Quiz를 이어받는다."""

    LABELS = ["Cross", "X"]

    def __init__(self, pattern, label, cross_filter=None, x_filter=None):
        n = len(pattern)
        self.pattern = pattern
        self.label = label
        self.cross_filter = cross_filter or make_cross(n)
        self.x_filter = x_filter or make_x(n)
        super().__init__("이 그림은 Cross(십자가)일까요, X일까요?",
                         ["Cross (십자가)", "X"], self.LABELS.index(label) + 1)

    def show(self, number: int | None = None) -> None:
        title = f"[패턴 문제 {number}] " if number else ""
        print(f"{title}{self.question}")
        print(render(self.pattern))
        for i, c in enumerate(self.choices, 1):
            print(f"  {i}. {c}")

    def explain(self) -> str:
        """MAC 점수를 보여 주고 AI의 판정(Cross/X/UNDECIDED)을 돌려준다."""
        cross_score = mac(self.pattern, self.cross_filter)
        x_score = mac(self.pattern, self.x_filter)
        verdict = judge(cross_score, x_score)
        print("--- AI(MAC)는 이렇게 계산했어요 ---")
        print(f"Cross 필터 점수: {cross_score}")
        print(f"X 필터 점수: {x_score}")
        if verdict == "UNDECIDED":
            print("→ 점수 차이가 허용오차(1e-9)보다 작아 판정 불가(UNDECIDED)")
        else:
            print(f"→ 점수가 더 큰 {verdict}로 판정!")
        return verdict


def make_noisy(pattern: list[list[int]], rng: random.Random, flips: int = 1) -> list[list[int]]:
    """패턴의 칸을 몇 개 뒤집어서 살짝 흐트러뜨린다."""
    n = len(pattern)
    noisy = [row[:] for row in pattern]
    for _ in range(flips):
        i, j = rng.randrange(n), rng.randrange(n)
        noisy[i][j] = 1 - noisy[i][j]
    return noisy


def build_pattern_quizzes(rng: random.Random | None = None, count: int = 4, size: int = 5) -> list[PatternQuiz]:
    """Cross와 X를 반반 섞어 패턴 퀴즈를 만든다. (일부는 칸을 1개 뒤집어 흐트러뜨린다.)"""
    rng = rng or random.Random()
    labels = (["Cross", "X"] * count)[:count]
    rng.shuffle(labels)
    quizzes = []
    for k, label in enumerate(labels):
        base = make_cross(size) if label == "Cross" else make_x(size)
        pattern = make_noisy(base, rng) if k % 2 == 1 else base
        quizzes.append(PatternQuiz(pattern, label))
    return quizzes


def default_quizzes() -> list[Quiz]:
    # TODO: 본인의 업무 지식으로 문제를 바꾸거나 늘려 보세요.
    return [
        Quiz("숲의 가장 위층(상층)을 이루는 식물층은?", ["교목층", "관목층", "초본층", "지피층"], 1),
        Quiz("수질 오염 지표로 쓰는 BOD는 무엇의 약자인가?", ["생물화학적 산소요구량", "화학적 산소요구량", "총인", "부유물질"], 1),
        Quiz("환경영향평가에서 법정보호종에 해당하는 것은?", ["멸종위기 야생생물", "외래종", "흔한 잡초", "가축"], 1),
        Quiz("하천 수질의 부영양화를 일으키는 대표 영양염류는?", ["질소와 인", "칼슘", "철", "나트륨"], 1),
        Quiz("광합성에서 식물이 흡수하는 기체는?", ["이산화탄소", "산소", "질소", "수소"], 1),
    ]


class QuizGame:
    def __init__(self):
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None
        self.load()

    # ---------- 입력 ----------
    def read_line(self, prompt: str) -> str | None:
        """공백 제거. Ctrl+C·EOF면 None 반환."""
        try:
            return input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n입력이 중단되었습니다. 종료합니다.")
            return None

    def read_int(self, prompt: str, low: int, high: int) -> int | None:
        while True:
            text = self.read_line(prompt)
            if text is None:
                return None
            if text == "":
                print("빈 입력입니다. 숫자를 입력하세요.")
                continue
            try:
                value = int(text)
            except ValueError:
                print("숫자만 입력하세요.")
                continue
            if not low <= value <= high:
                print(f"{low}~{high} 사이의 숫자를 입력하세요.")
                continue
            return value

    # ---------- 저장/불러오기 ----------
    def load(self) -> None:
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.quizzes = [Quiz.from_dict(q) for q in data["quizzes"]]
            self.best_score = data.get("best_score")
        except FileNotFoundError:
            self.quizzes = default_quizzes()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            print("데이터 파일이 손상되어 기본 퀴즈로 복구합니다.")
            self.quizzes = default_quizzes()
            self.best_score = None
            self.save()

    def save(self) -> None:
        data = {"quizzes": [q.to_dict() for q in self.quizzes], "best_score": self.best_score}
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"저장 실패: {e}")

    # ---------- 기능 ----------
    def show_menu(self) -> None:
        print("=" * 40)
        print("  숲해설·환경교육 퀴즈 게임")
        print("=" * 40)
        print("1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
        print("6. AI 패턴 퀴즈 (3번 미션: MAC 연산 체험)")
        print("=" * 40)

    def play(self) -> bool:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return True
        print(f"퀴즈를 시작합니다! (총 {len(self.quizzes)}문제)")
        score = 0
        for i, quiz in enumerate(self.quizzes, 1):
            print("-" * 40)
            quiz.show(i)
            choice = self.read_int("정답 번호: ", 1, 4)
            if choice is None:
                return False
            if quiz.is_correct(choice):
                print("정답입니다!")
                score += 1
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다.")
        print("=" * 40)
        print(f"결과: {len(self.quizzes)}문제 중 {score}문제 정답 ({score * 100 // len(self.quizzes)}점)")
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            print("최고 점수를 갱신했습니다!")
        self.save()
        return True

    def add_quiz(self) -> bool:
        question = ""
        while not question:
            text = self.read_line("문제: ")
            if text is None:
                return False
            question = text
            if not question:
                print("빈 입력입니다.")
        choices = []
        for i in range(1, 5):
            text = ""
            while not text:
                text = self.read_line(f"선택지 {i}: ")
                if text is None:
                    return False
                if not text:
                    print("빈 입력입니다.")
            choices.append(text)
        answer = self.read_int("정답 번호(1-4): ", 1, 4)
        if answer is None:
            return False
        self.quizzes.append(Quiz(question, choices, answer))
        self.save()
        print("퀴즈가 추가되었습니다.")
        return True

    def list_quizzes(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return
        print(f"등록된 퀴즈 ({len(self.quizzes)}개)")
        for i, q in enumerate(self.quizzes, 1):
            print(f"[{i}] {q.question}")

    def show_score(self) -> None:
        if self.best_score is None:
            print("아직 퀴즈를 풀지 않았습니다.")
        else:
            print(f"최고 점수: {self.best_score}/{len(self.quizzes)}")


    def play_pattern_quiz(self) -> bool:
        """AI 패턴 퀴즈: 그림을 맞히고, AI(MAC 연산)가 어떻게 판정했는지 비교한다."""
        quizzes = build_pattern_quizzes()
        print(f"AI 패턴 퀴즈를 시작합니다! (총 {len(quizzes)}문제)")
        mine = ai = 0
        for i, quiz in enumerate(quizzes, 1):
            print("-" * 40)
            quiz.show(i)
            choice = self.read_int("정답 번호(1~2): ", 1, 2)
            if choice is None:
                return False
            verdict = quiz.explain()
            if quiz.is_correct(choice):
                print("정답입니다!")
                mine += 1
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번({quiz.label})입니다.")
            if verdict == quiz.label:
                ai += 1
        print("=" * 40)
        print(f"내 점수: {mine}/{len(quizzes)}  |  AI(MAC) 점수: {ai}/{len(quizzes)}")
        return True

    def run(self) -> None:
        while True:
            self.show_menu()
            choice = self.read_int("선택: ", 1, 6)
            if choice is None or choice == 5:
                self.save()
                print("종료합니다.")
                return
            actions = {1: self.play, 2: self.add_quiz, 6: self.play_pattern_quiz}
            if choice in actions:
                if not actions[choice]():
                    self.save()
                    return
            elif choice == 3:
                self.list_quizzes()
            elif choice == 4:
                self.show_score()


if __name__ == "__main__":
    QuizGame().run()
