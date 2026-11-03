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


def show_menu() -> None:
    print("=" * 40)
    print("  숲해설·환경교육 퀴즈 게임")
    print("=" * 40)
    print("1. 퀴즈 풀기\n2. 퀴즈 추가\n3. 퀴즈 목록\n4. 점수 확인\n5. 종료")
    print("=" * 40)


def read_int(prompt: str, low: int, high: int) -> int | None:
    """공백 제거, 빈 입력, 숫자 변환 실패, 범위 밖 숫자를 처리한다. Ctrl+C·EOF면 None."""
    while True:
        try:
            text = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n입력이 중단되었습니다.")
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


def main() -> None:
    while True:
        show_menu()
        choice = read_int("선택: ", 1, 5)
        if choice is None or choice == 5:
            print("종료합니다.")
            return
        print("아직 준비 중인 기능입니다.")


if __name__ == "__main__":
    main()
