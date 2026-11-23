"""숲해설·환경교육 퀴즈 게임 (Python 3.10+, 표준 라이브러리만 사용)."""
import json
import os
import random
import signal
import time

from npu_core import judge, make_cross, make_x, mac, normalize_label, render

# 기본은 main.py 옆의 state.json. 환경 변수 QUIZ_STATE_FILE로 위치를 바꿀 수 있다(Docker 볼륨용).
STATE_FILE = os.environ.get("QUIZ_STATE_FILE") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state.json")
BACKUP_FILE = STATE_FILE + ".bak"   # 손상된 state.json을 지우지 않고 보관하는 곳
SAVE_RETRIES = 3                    # 저장 실패 시 재시도 최대 횟수
NUM_CHOICES = 4                     # 선택지 개수 (바뀌면 이 값과 기본 데이터만 확인)


class Quiz:
    """퀴즈 한 문제. answer는 1~4 번호. category는 향후 확장용 분류(선택, 기본 "일반")."""

    def __init__(self, question: str, choices: list[str], answer: int, category: str = "일반"):
        self.question = question
        self.choices = choices
        self.answer = answer
        self.category = category

    def show(self, number: int | None = None) -> None:
        """문제와 선택지를 번호와 함께 출력한다."""
        title = f"[문제 {number}] " if number else ""
        print(f"{title}{self.question}")
        for i, c in enumerate(self.choices, 1):
            print(f"  {i}. {c}")

    def is_correct(self, choice: int) -> bool:
        """입력 번호가 정답 번호와 같으면 True. 입력 범위(1~4) 검증은 QuizGame.read_int가 맡는다."""
        return choice == self.answer

    def to_dict(self) -> dict:
        """state.json에 저장할 딕셔너리로 바꾼다."""
        return {"question": self.question, "choices": self.choices, "answer": self.answer,
                "category": self.category}

    @staticmethod
    def from_dict(d: dict) -> "Quiz":
        """딕셔너리에서 Quiz를 만든다. 선택지 개수·정답 범위가 틀리면 ValueError (옛 파일은 category 없어도 됨)."""
        choices = d["choices"]
        answer = d["answer"]
        if len(choices) != NUM_CHOICES or answer not in range(1, NUM_CHOICES + 1):
            raise ValueError("잘못된 퀴즈 형식")
        return Quiz(str(d["question"]), [str(c) for c in choices], answer, str(d.get("category", "일반")))


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
    """기본 퀴즈 5개. 세 번째 값은 정답 번호, 마지막 값은 분류(category)."""
    return [
        Quiz("숲의 가장 위층(상층)을 이루는 식물층은?", ["교목층", "관목층", "초본층", "지피층"], 1, "숲해설"),
        Quiz("수질 오염 지표로 쓰는 BOD는 무엇의 약자인가?", ["생물화학적 산소요구량", "화학적 산소요구량", "총인", "부유물질"], 1, "수질"),
        Quiz("환경영향평가에서 법정보호종에 해당하는 것은?", ["멸종위기 야생생물", "외래종", "흔한 잡초", "가축"], 1, "환경영향평가"),
        Quiz("하천 수질의 부영양화를 일으키는 대표 영양염류는?", ["질소와 인", "칼슘", "철", "나트륨"], 1, "수질"),
        Quiz("광합성에서 식물이 흡수하는 기체는?", ["이산화탄소", "산소", "질소", "수소"], 1, "숲해설"),
    ]

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def load_pattern_quizzes(path: str = DATA_FILE, max_size: int = 13) -> tuple[list["PatternQuiz"], list[str]]:
    """3번 미션과 같은 형식의 data.json에서 패턴 퀴즈를 만든다. (문제 목록, 건너뛴 이유 목록)"""
    skipped: list[str] = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        raw_filters = data["filters"]
        raw_patterns = data["patterns"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return [], ["data.json을 읽을 수 없어요"]

    filters: dict[str, dict[str, list]] = {}
    for key, value in raw_filters.items():
        labeled = {normalize_label(k): v for k, v in value.items()}
        if "Cross" in labeled and "X" in labeled:
            filters[key.replace("size_", "")] = labeled

    quizzes = []
    for name, case in raw_patterns.items():
        try:
            size = name.split("_")[1]
            pattern = case["input"]
            label = normalize_label(case["expected"])
            flt = filters[size]
            n = int(size)
            if label is None:
                raise ValueError("알 수 없는 라벨")
            if len(pattern) != n or any(len(row) != n for row in pattern) or n > max_size:
                raise ValueError("크기 불일치 또는 너무 큼")
            quizzes.append(PatternQuiz(pattern, label, flt["Cross"], flt["X"]))
        except (IndexError, KeyError, ValueError, TypeError) as e:
            skipped.append(f"{name}: {e}")
    return quizzes, skipped


class QuizGame:
    """게임 전체: 퀴즈 목록과 최고 점수를 갖고, 입력 검증·게임 진행·파일 저장/불러오기를 맡는다."""

    def __init__(self):
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None
        self.load()

    # ---------- 입력 ----------
    def read_line(self, prompt: str) -> str | None:  # 모든 입력의 관문
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
        """state.json을 읽는다. 없으면 기본 퀴즈, 손상됐으면 .bak로 보관 후 기본 퀴즈로 복구한다."""
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.quizzes = [Quiz.from_dict(q) for q in data["quizzes"]]
            self.best_score = data.get("best_score")
        except FileNotFoundError:
            self.quizzes = default_quizzes()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            print("데이터 파일이 손상되어 기본 퀴즈로 복구합니다.")
            try:    # 복구하기 전에 손상된 파일을 .bak로 보관해 사용자 데이터를 잃지 않게 한다
                os.replace(STATE_FILE, BACKUP_FILE)
                print(f"(손상된 파일은 {os.path.basename(BACKUP_FILE)}로 보관했습니다.)")
            except OSError:
                print("(손상된 파일을 보관하지 못했습니다.)")
            self.quizzes = default_quizzes()
            self.best_score = None
            self.save()

    def save(self) -> None:
        """임시 파일에 먼저 쓰고 성공하면 교체한다. 쓰는 도중 꺼져도 기존 state.json은 안전하다."""
        data = {"quizzes": [q.to_dict() for q in self.quizzes], "best_score": self.best_score}
        tmp = STATE_FILE + ".tmp"
        for attempt in range(1, SAVE_RETRIES + 1):
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, STATE_FILE)
                return
            except OSError as e:
                if attempt < SAVE_RETRIES:
                    time.sleep(0.2)     # 잠깐 쉬었다가 다시 시도 (최대 SAVE_RETRIES번)
                    continue
                print(f"저장 실패: {e} (폴더 쓰기 권한과 디스크 공간을 확인하세요. 이번 변경은 저장되지 않았습니다.)")

    # ---------- 기능 ----------
    def show_menu(self) -> None:
        """메뉴를 출력한다."""
        print("=" * 40)
        print("  숲해설·환경교육 퀴즈 게임")
        print("=" * 40)
        print("1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
        print("6. AI 패턴 퀴즈 (3번 미션: MAC 연산 체험)")
        print("=" * 40)

    def play(self) -> bool:
        """저장된 퀴즈를 차례로 출제하고 점수를 계산한다. 입력이 중단되면 False."""
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return True
        print(f"퀴즈를 시작합니다! (총 {len(self.quizzes)}문제)")
        score = 0
        for i, quiz in enumerate(self.quizzes, 1):
            print("-" * 40)
            quiz.show(i)
            choice = self.read_int("정답 번호: ", 1, NUM_CHOICES)
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
        """문제, 선택지, 정답 번호를 입력받아 퀴즈를 추가하고 저장한다. 입력이 중단되면 False."""
        question = ""
        while not question:
            text = self.read_line("문제: ")
            if text is None:
                return False
            question = text
            if not question:
                print("빈 입력입니다.")
        choices = []
        for i in range(1, NUM_CHOICES + 1):
            text = ""
            while not text:
                text = self.read_line(f"선택지 {i}: ")
                if text is None:
                    return False
                if not text:
                    print("빈 입력입니다.")
            choices.append(text)
        answer = self.read_int(f"정답 번호(1-{NUM_CHOICES}): ", 1, NUM_CHOICES)
        if answer is None:
            return False
        self.quizzes.append(Quiz(question, choices, answer))
        self.save()
        print("퀴즈가 추가되었습니다.")
        return True

    def list_quizzes(self) -> None:
        """등록된 퀴즈의 문제 목록을 출력한다."""
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return
        print(f"등록된 퀴즈 ({len(self.quizzes)}개)")
        for i, q in enumerate(self.quizzes, 1):
            print(f"[{i}] {q.question}")

    def show_score(self) -> None:
        """최고 점수를 출력한다. 아직 안 풀었으면 안내한다."""
        if self.best_score is None:
            print("아직 퀴즈를 풀지 않았습니다.")
        else:
            print(f"최고 점수: {self.best_score}/{len(self.quizzes)}")


    def play_pattern_quiz(self, rounds: int = 4) -> bool:
        """AI 패턴 퀴즈: data.json의 패턴으로 출제하고, AI(MAC 연산)의 판정과 비교한다."""
        pool, skipped = load_pattern_quizzes()
        for reason in skipped:
            print(f"(건너뜀) {reason}")
        if pool:
            quizzes = random.sample(pool, min(rounds, len(pool)))
            print(f"(data.json의 패턴 {len(pool)}개 중 {len(quizzes)}개를 골랐어요)")
        else:
            print("(data.json이 없어서 패턴을 직접 만들어요)")
            quizzes = build_pattern_quizzes(count=rounds)
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
        """메뉴 루프. 선택에 따라 기능을 호출하고, 종료하거나 입력이 중단되면 저장 후 끝낸다."""
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


def install_signal_handlers() -> None:
    """SIGTERM(종료 요청)·SIGHUP(터미널 끊김)을 Ctrl+C와 같이 취급해 안전하게 저장하고 종료한다."""
    def _stop(signum, frame):
        raise KeyboardInterrupt

    for name in ("SIGTERM", "SIGHUP"):      # SIGHUP은 윈도우에 없어서 있는 것만 등록
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, _stop)
            except (ValueError, OSError):
                pass


if __name__ == "__main__":
    install_signal_handlers()
    QuizGame().run()
