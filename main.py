"""숲해설·환경교육 퀴즈 게임 (Python 3.10+, 표준 라이브러리만 사용)."""


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
        self.quizzes = default_quizzes()
        self.best_score: int | None = None

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

    # ---------- 기능 ----------
    def show_menu(self) -> None:
        print("=" * 40)
        print("  숲해설·환경교육 퀴즈 게임")
        print("=" * 40)
        print("1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
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

    def run(self) -> None:
        while True:
            self.show_menu()
            choice = self.read_int("선택: ", 1, 5)
            if choice is None or choice == 5:
                print("종료합니다.")
                return
            actions = {1: self.play, 2: self.add_quiz}
            if choice in actions:
                if not actions[choice]():
                    return
            elif choice == 3:
                self.list_quizzes()
            elif choice == 4:
                self.show_score()


if __name__ == "__main__":
    QuizGame().run()
